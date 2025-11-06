# app/external/feed_downloader.py
from __future__ import annotations

import csv
import io
import json
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.schemas.feeds import FeedTestRequest, FeedTestResponse

MAX_PREVIEW_BYTES = 256 * 1024


def _looks_like_html(raw: bytes) -> bool:
    if not raw:
        return False
    start = raw.lstrip()[:64].lower()
    return start.startswith(b"<!doctype html") or start.startswith(b"<html")


def _charset_from_content_type(ct: str | None) -> str | None:
    if not ct:
        return None
    for part in ct.split(";"):
        part = part.strip().lower()
        if part.startswith("charset="):
            return part.split("=", 1)[1].strip()
    return None


def _infer_format(format_hint: str | None, content_type: str | None, sample: bytes) -> str:
    """
    Decide 'json' vs 'csv' quando o cliente não define explicitamente.
    """
    if format_hint:
        return format_hint.lower()

    ct = (content_type or "").lower()
    if "application/json" in ct or "ld+json" in ct or "json" in ct:
        return "json"
    if "text/csv" in ct:
        return "csv"

    # Heurística rápida pelo conteúdo
    s = sample.lstrip()[:1]
    if s in (b"{", b"["):
        return "json"
    return "csv"


# --- Back-compat helpers para serviços antigos -----------------------------


async def http_download(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
    timeout_s: int = 30,
    auth_kind: str | None = None,
    auth: dict[str, str] | None = None,
) -> tuple[int, str | None, bytes]:
    """
    Wrapper fino sobre FeedDownloader._http_get para manter APIs antigas.
    """
    dl = FeedDownloader()
    status, ct, raw, _err = await dl._http_get(
        url=url,
        headers=headers,
        params=params,
        auth_kind=auth_kind,
        auth=auth,
        timeout_s=timeout_s,
    )
    return status, ct, raw


def parse_rows_json(raw: bytes) -> list[dict]:
    """
    Extrai linhas (dicts) de JSON (lista, {data|items|results|products|rows|list}, objeto único),
    ou NDJSON (uma linha JSON por linha).
    """
    # 1) JSON tradicional
    try:
        obj = json.loads(raw.decode(errors="ignore"))
        if isinstance(obj, list):
            return [x for x in obj if isinstance(x, dict)]
        if isinstance(obj, dict):
            for key in ("data", "items", "results", "products", "rows", "list"):
                v = obj.get(key)
                if isinstance(v, list):
                    return [x for x in v if isinstance(x, dict)]
            return [obj]
    except Exception:
        pass

    # 2) NDJSON (cada linha um JSON)
    out: list[dict] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            val = json.loads(line.decode(errors="ignore"))
            if isinstance(val, dict):
                out.append(val)
        except Exception:
            continue
    return out


def parse_rows_csv(
    raw: bytes,
    *,
    delimiter: str = ",",
    max_rows: int | None = None,
) -> list[dict]:
    """
    Converte CSV → lista de dicts (usando 1ª linha como cabeçalho).
    """
    text = FeedDownloader()._decode_best(raw, ct="text/csv; charset=utf-8")
    # Remove BOM se existir
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")

    sio = io.StringIO(text)
    reader = csv.DictReader(sio, delimiter=(delimiter or ","), restkey="_extra", restval="")
    out: list[dict] = []
    for i, row in enumerate(reader, 1):
        clean: dict[str, Any] = {}
        for k, v in row.items():
            if k is None:
                continue
            key = str(k).strip() or f"col_{len(clean) + 1}"
            if isinstance(v, list):
                v = ",".join("" if x is None else str(x) for x in v)
            clean[key] = "" if v is None else v
        out.append(clean)
        if max_rows and i >= max_rows:
            break
    return out


class FeedDownloader:
    """
    Downloader/preview unificado para feeds CSV/JSON via HTTP.
    (Se precisares de FTP mais tarde, podemos plugar um conector aqui.)
    """

    def __init__(self) -> None:
        self.timeout_s = int(getattr(settings, "FEED_DOWNLOAD_TIMEOUT", 30))

    async def preview(self, req: FeedTestRequest) -> FeedTestResponse:
        # --- validação básica de URL/kind ---
        scheme = urlparse((req.url or "").lower()).scheme
        if scheme in {"ftp", "ftps"} or (req.kind and req.kind.lower() in {"ftp", "ftps"}):
            return FeedTestResponse(
                ok=False,
                status_code=400,
                content_type=None,
                bytes_read=0,
                preview_type=None,
                rows_preview=[],
                error="FTP/FTPS is not supported by this downloader",
            )

        status_code, ct, raw, err_text = await self._http_get(
            url=req.url,
            headers=req.headers,
            params=req.params,
            auth_kind=req.auth_kind,
            auth=req.auth,
            timeout_s=self.timeout_s,
        )

        # falha HTTP → devolve erro + pequeno corpo para debug
        if status_code < 200 or status_code >= 300:
            return FeedTestResponse(
                ok=False,
                status_code=status_code,
                content_type=ct,
                bytes_read=len(raw or b""),
                preview_type=None,
                rows_preview=[],
                error=(err_text or self._decode_best(raw, ct))[:300],
            )

        sample = (raw or b"")[:MAX_PREVIEW_BYTES]

        # HTML → snippet curto apenas para debug/login-pages
        if _looks_like_html(sample):
            return FeedTestResponse(
                ok=True,
                status_code=status_code,
                content_type=ct,
                bytes_read=len(raw or b""),
                preview_type=None,
                rows_preview=[{"html_snippet": self._decode_best(sample, ct)[:1200]}],
                error=None,
            )

        # decidir formato
        fmt = _infer_format(req.format, ct, sample)

        if fmt == "json":
            rows = self._preview_json(sample)
            rows = rows[: (req.max_rows or 20)]
            return FeedTestResponse(
                ok=True,
                status_code=status_code,
                content_type=ct,
                bytes_read=len(raw or b""),
                preview_type="json",
                rows_preview=rows,
                error=None,
            )
        else:
            # default → CSV
            rows = self._preview_csv(
                sample,
                delimiter=(req.csv_delimiter or ","),
                max_rows=(req.max_rows or 20),
            )
            return FeedTestResponse(
                ok=True,
                status_code=status_code,
                content_type=ct,
                bytes_read=len(raw or b""),
                preview_type="csv",
                rows_preview=rows,
                error=None,
            )

    # -------------------- HTTP core --------------------

    async def _http_get(
        self,
        *,
        url: str,
        headers: dict[str, str] | None,
        params: dict[str, str] | None,
        auth_kind: str | None,
        auth: dict[str, str] | None,
        timeout_s: int,
    ) -> tuple[int, str | None, bytes, str | None]:
        # headers defensivos
        h = dict(headers or {})

        # auth
        httpx_auth = None
        if (auth_kind or "").lower() == "basic" and isinstance(auth, dict):
            user = auth.get("username") or auth.get("user")
            pwd = auth.get("password") or auth.get("pass")
            if user is not None and pwd is not None:
                httpx_auth = httpx.BasicAuth(user, pwd)
        elif (auth_kind or "").lower() == "bearer" and isinstance(auth, dict):
            token = auth.get("token") or auth.get("access_token")
            if token:
                h.setdefault("Authorization", f"Bearer {token}")
        elif (auth_kind or "").lower() in {"header", "apikey"} and isinstance(auth, dict):
            # Ex.: {"header": "X-API-Key", "value": "..."} ou {"name":"X-Token","value":"..."}
            key = auth.get("header") or auth.get("name")
            val = auth.get("value") or auth.get("token")
            if key and val:
                h.setdefault(str(key), str(val))

        # user-agent mínimo
        h.setdefault("Accept", "application/json,text/csv;q=0.9,*/*;q=0.1")
        h.setdefault("User-Agent", getattr(settings, "PS_USER_AGENT", "genesys/2.0"))

        try:
            async with httpx.AsyncClient(timeout=timeout_s) as cli:
                resp = await cli.get(url, headers=h, params=params, auth=httpx_auth)
                ct = resp.headers.get("content-type")
                err_text = None
                if resp.status_code >= 400:
                    err_text = self._decode_best(resp.content[:4096], ct)
                return resp.status_code, ct, resp.content, err_text
        except Exception as e:
            # mapeia exceção de rede como 599 (custom)
            return 599, None, b"", str(e)

    # -------------------- Preview helpers --------------------

    def _decode_best(self, raw: bytes, ct: str | None) -> str:
        if not raw:
            return ""
        enc = _charset_from_content_type(ct)
        tried: list[str] = []
        if enc:
            tried.append(enc)
        for codec in tried + ["utf-8", "latin-1"]:
            try:
                return raw.decode(codec, errors="ignore")
            except Exception:
                continue
        return raw.decode("utf-8", errors="ignore")

    def _preview_json(self, raw_sample: bytes) -> list[dict]:
        # tenta JSON tradicional; se falhar, tenta NDJSON
        try:
            obj = json.loads(raw_sample.decode(errors="ignore"))
            if isinstance(obj, list):
                return [x for x in obj if isinstance(x, dict)]
            if isinstance(obj, dict):
                for key in ("data", "items", "results", "products", "rows", "list"):
                    v = obj.get(key)
                    if isinstance(v, list):
                        return [x for x in v if isinstance(x, dict)]
                return [obj]
        except Exception:
            pass

        # NDJSON (uma linha JSON por linha)
        out: list[dict] = []
        for line in raw_sample.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                val = json.loads(line.decode(errors="ignore"))
                if isinstance(val, dict):
                    out.append(val)
            except Exception:
                continue
        return out

    def _preview_csv(
        self, raw_sample: bytes, *, delimiter: str = ",", max_rows: int = 20
    ) -> list[dict]:
        text = self._decode_best(raw_sample, ct="text/csv; charset=utf-8")
        if text.startswith("\ufeff"):
            text = text.lstrip("\ufeff")
        sio = io.StringIO(text)

        reader = csv.DictReader(
            sio,
            delimiter=(delimiter or ","),
            restkey="_extra",
            restval="",
        )

        out: list[dict] = []
        for i, row in enumerate(reader, 1):
            clean: dict[str, Any] = {}
            for k, v in row.items():
                if k is None:
                    continue
                key = str(k).strip() or f"col_{len(clean) + 1}"
                if isinstance(v, list):
                    v = ",".join("" if x is None else str(x) for x in v)
                clean[key] = "" if v is None else v
            out.append(clean)
            if i >= max_rows:
                break
        return out
