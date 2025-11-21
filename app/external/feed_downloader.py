from __future__ import annotations

import csv
import io
import json
from typing import Any
from urllib.parse import urlparse

from app.core.config import settings
from app.schemas.feeds import FeedTestRequest, FeedTestResponse

MAX_PREVIEW_BYTES = 256 * 1024


def looks_like_html(raw: bytes) -> bool:
    if not raw:
        return False
    start = raw.lstrip()[:64].lower()
    return start.startswith(b"<!doctype html") or start.startswith(b"<html")


def charset_from_content_type(ct: str | None) -> str | None:
    if not ct:
        return None
    for part in ct.split(";"):
        part = part.strip().lower()
        if part.startswith("charset="):
            return part.split("=", 1)[1].strip()
    return None


def infer_format(format_hint: str | None, content_type: str | None, sample: bytes) -> str:
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


def guess_content_type_from_path(path: str | None) -> str | None:
    if not path:
        return None
    lower = path.lower()
    if lower.endswith(".json"):
        return "application/json"
    if lower.endswith(".csv"):
        return "text/csv"
    if lower.endswith(".txt"):
        return "text/plain"
    return None


def decode_best(raw: bytes, ct: str | None) -> str:
    if not raw:
        return ""
    enc = charset_from_content_type(ct)
    tried: list[str] = []
    if enc:
        tried.append(enc)
    for codec in tried + ["utf-8", "latin-1"]:
        try:
            return raw.decode(codec, errors="ignore")
        except Exception:
            continue
    return raw.decode("utf-8", errors="ignore")


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
    text = decode_best(raw, ct="text/csv; charset=utf-8")
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
    Orquestra o preview consoante o tipo (HTTP vs FTP), usando os downloaders específicos.
    """

    def __init__(self, timeout_s: int | None = None) -> None:
        self.timeout_s = timeout_s or int(getattr(settings, "FEED_DOWNLOAD_TIMEOUT", 30))

    async def preview(self, req: FeedTestRequest) -> FeedTestResponse:
        """
        Usa HttpDownloader ou FTPDownloader para sacar os bytes e devolve só uma amostra.
        """
        # Import lazy para evitar ciclos
        from app.external.http_downloader import HttpDownloader
        from app.external.ftp_downloader import FTPDownloader

        url = req.url or ""
        parsed = urlparse(url)
        scheme = (parsed.scheme or "").lower()
        kind = (req.kind or "http").lower()
        auth_kind = (req.auth_kind or "").lower()

        is_ftp = kind == "ftp" or scheme in {"ftp", "ftps"} or auth_kind == "ftp_password"

        if is_ftp:
            downloader = FTPDownloader(timeout_s=self.timeout_s)
        else:
            downloader = HttpDownloader(timeout_s=self.timeout_s)

        status_code, ct, raw, err_text = await downloader.download(
            url=url,
            headers=req.headers,
            params=req.params,
            auth_kind=req.auth_kind,
            auth=req.auth,
            timeout_s=self.timeout_s,
            kind=kind,
        )

        # falha → devolve erro + snippet
        if status_code < 200 or status_code >= 300:
            return FeedTestResponse(
                ok=False,
                status_code=status_code,
                content_type=ct,
                bytes_read=len(raw or b""),
                preview_type=None,
                rows_preview=[],
                error=(err_text or decode_best(raw, ct))[:300],
            )

        sample = (raw or b"")[:MAX_PREVIEW_BYTES]

        # HTML → snippet curto apenas para debug/login-pages
        if looks_like_html(sample):
            return FeedTestResponse(
                ok=True,
                status_code=status_code,
                content_type=ct,
                bytes_read=len(raw or b""),
                preview_type=None,
                rows_preview=[{"html_snippet": decode_best(sample, ct)[:1200]}],
                error=None,
            )

        # decidir formato
        fmt = infer_format(req.format, ct, sample)

        if fmt == "json":
            rows = parse_rows_json(sample)
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

        # default → CSV
        rows = parse_rows_csv(
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
    Wrapper fino para ingestão:
    - Se for HTTP normal → HttpDownloader
    - Se for FTP (esquema ftp/ftps ou auth_kind=ftp_password) → FTPDownloader
      (inclui o caso Globomatik: url HTTP + auth_kind=ftp_password → FTP com trigger HTTP).
    """
    from app.external.http_downloader import HttpDownloader
    from app.external.ftp_downloader import FTPDownloader

    parsed = urlparse(url or "")
    scheme = (parsed.scheme or "").lower()
    ak = (auth_kind or "").lower()

    is_ftp = scheme in {"ftp", "ftps"} or ak == "ftp_password"

    if is_ftp:
        dl = FTPDownloader(timeout_s=timeout_s)
        status, ct, raw, _err = await dl.download(
            url=url,
            headers=headers,
            params=params,
            auth_kind=auth_kind,
            auth=auth,
            timeout_s=timeout_s,
            kind="ftp",
        )
    else:
        dl = HttpDownloader(timeout_s=timeout_s)
        status, ct, raw, _err = await dl.download(
            url=url,
            headers=headers,
            params=params,
            auth_kind=auth_kind,
            auth=auth,
            timeout_s=timeout_s,
            kind="http",
        )

    return status, ct, raw
