# app/external/http_downloader.py
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class HttpDownloader:
    """
    Cliente HTTP simples para download de feeds.
    Suporta auth_kind básico (basic, bearer, api_key/header, oauth_password).
    """

    def __init__(self, timeout_s: int | None = None) -> None:
        self.timeout_s = int(timeout_s or getattr(settings, "FEED_DOWNLOAD_TIMEOUT", 30))

    async def fetch(
        self,
        *,
        url: str,
        method: str = "GET",
        headers: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        auth_kind: str | None = None,
        auth: dict[str, Any] | None = None,
        json_body: Any = None,
        timeout_s: int | None = None,
    ) -> tuple[int, str | None, bytes, str | None]:
        """
        Executa o pedido HTTP e devolve (status_code, content_type, raw_bytes, error_text).

        Em caso de exceção de rede, devolve status_code 599 e error_text com a mensagem.
        """
        timeout = int(timeout_s or self.timeout_s)

        # headers defensivos
        h: dict[str, str] = {}
        if headers:
            for k, v in headers.items():
                if v is None:
                    continue
                h[str(k)] = str(v)

        # auth
        httpx_auth = None
        ak = (auth_kind or "").lower()
        if ak == "basic" and isinstance(auth, dict):
            user = auth.get("username") or auth.get("user")
            pwd = auth.get("password") or auth.get("pass")
            if user is not None and pwd is not None:
                httpx_auth = httpx.BasicAuth(str(user), str(pwd))
        elif ak == "bearer" and isinstance(auth, dict):
            token = auth.get("token") or auth.get("access_token")
            if token:
                h.setdefault("Authorization", f"Bearer {token}")
        elif ak in {"header", "apikey", "api_key"} and isinstance(auth, dict):
            # Ex.: {"header":"X-API-Key","value":"..."} ou {"name":"X-Token","value":"..."}
            key = auth.get("header") or auth.get("name")
            val = auth.get("value") or auth.get("token")
            if key and val:
                h.setdefault(str(key), str(val))
        elif ak == "oauth_password" and isinstance(auth, dict):
            # Para já tratamos como bearer token normal se vier "access_token"
            token = auth.get("access_token")
            if token:
                h.setdefault("Authorization", f"Bearer {token}")

        # user-agent mínimo
        h.setdefault("Accept", "application/json,text/csv;q=0.9,*/*;q=0.1")
        h.setdefault("User-Agent", getattr(settings, "PS_USER_AGENT", "genesys/2.0"))

        try:
            async with httpx.AsyncClient(timeout=timeout) as cli:
                resp = await cli.request(
                    method=method or "GET",
                    url=url,
                    headers=h,
                    params=params,
                    json=json_body,
                    auth=httpx_auth,
                )
                ct = resp.headers.get("content-type")
                err_text = None
                if resp.status_code >= 400:
                    # usamos texto simples; preview depois faz decode melhor se precisar
                    try:
                        err_text = resp.text[:4096]
                    except Exception:
                        err_text = None
                return resp.status_code, ct, resp.content, err_text
        except Exception as e:  # erros de rede
            return 599, None, b"", str(e)
