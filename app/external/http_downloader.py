from __future__ import annotations

import httpx
from typing import Any

from app.core.config import settings
from app.external.feed_downloader import decode_best, FeedDownloader


class HttpDownloader(FeedDownloader):
    """
    Downloader HTTP(S) simples (GET), com suporte para:
    - auth_kind: basic / bearer / api_key / header
    - headers & params adicionais
    """

    def __init__(self, timeout_s: int | None = None) -> None:
        super().__init__(timeout_s=timeout_s)

    async def download(
        self,
        *,
        url: str,
        headers: dict[str, str] | None,
        params: dict[str, str] | None,
        auth_kind: str | None,
        auth: dict[str, Any] | None,
        timeout_s: int | None = None,
        kind: str | None = None,  # não usado, mas mantido para interface comum
    ) -> tuple[int, str | None, bytes, str | None]:
        h = dict(headers or {})

        # auth
        httpx_auth = None
        ak = (auth_kind or "").lower()
        if ak == "basic" and isinstance(auth, dict):
            user = auth.get("username") or auth.get("user")
            pwd = auth.get("password") or auth.get("pass")
            if user is not None and pwd is not None:
                httpx_auth = httpx.BasicAuth(user, pwd)
        elif ak == "bearer" and isinstance(auth, dict):
            token = auth.get("token") or auth.get("access_token")
            if token:
                h.setdefault("Authorization", f"Bearer {token}")
        elif ak in {"header", "apikey", "api_key"} and isinstance(auth, dict):
            # Ex.: {"header": "X-API-Key", "value": "..."} ou {"name":"X-Token","value":"..."}
            key = auth.get("header") or auth.get("name")
            val = auth.get("value") or auth.get("token")
            if key and val:
                h.setdefault(str(key), str(val))

        # user-agent mínimo
        h.setdefault("Accept", "application/json,text/csv;q=0.9,*/*;q=0.1")
        h.setdefault("User-Agent", getattr(settings, "PS_USER_AGENT", "genesys/2.0"))

        timeout = timeout_s or self.timeout_s

        try:
            async with httpx.AsyncClient(timeout=timeout) as cli:
                resp = await cli.get(url, headers=h, params=params, auth=httpx_auth)
                ct = resp.headers.get("content-type")
                err_text = None
                if resp.status_code >= 400:
                    err_text = decode_best(resp.content[:4096], ct)
                return resp.status_code, ct, resp.content, err_text
        except Exception as e:
            # mapeia exceção de rede como 599 (custom)
            return 599, None, b"", str(e)
