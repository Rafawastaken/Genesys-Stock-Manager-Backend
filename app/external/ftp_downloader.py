from __future__ import annotations

import asyncio
from ftplib import FTP, FTP_TLS
from typing import Any
from urllib.parse import urlparse

from app.core.config import settings
from app.external.feed_downloader import (
    FeedDownloader,
    guess_content_type_from_path,
)


class FTPDownloader(FeedDownloader):
    """
    Downloader FTP/FTPS.

    Modos suportados:
    - URL ftp://user:pass@host:21/path/file.csv        (tudo na URL)
    - URL path/file.csv + auth.host/auth.username/... (auth_kind=ftp_password)
    - URL vazia ou "/" ou "." → lista diretório e saca o primeiro ficheiro de dados
      (comportamento tipo Globomatik antigo).
    - Caso especial Globomatik:
      kind="ftp" + url HTTP/HTTPS → trigger HTTP e depois FTP root (1º ficheiro).
    """

    def __init__(self, timeout_s: int | None = None) -> None:
        self.timeout_s = timeout_s or int(getattr(settings, "FEED_DOWNLOAD_TIMEOUT", 30))

    async def download(
        self,
        *,
        url: str,
        headers: dict[str, str] | None,
        params: dict[str, str] | None,
        auth_kind: str | None,
        auth: dict[str, Any] | None,
        timeout_s: int | None = None,
        kind: str | None = None,
    ) -> tuple[int, str | None, bytes, str | None]:
        # headers/params não fazem sentido em FTP, mantidos só para compatibilidade
        _ = headers, params

        timeout = timeout_s or self.timeout_s
        parsed = urlparse(url or "")
        scheme = (parsed.scheme or "").lower()
        kind_l = (kind or "").lower()

        # ---- Caso especial: Globomatik (kind=ftp + url HTTP/HTTPS) ----
        # 1) Faz trigger via HTTP (GET), ignorando o body; se falhar devolve o erro HTTP.
        # 2) Depois liga ao FTP (host/creds via auth) e apanha o 1º ficheiro real do diretório.
        if kind_l == "ftp" and scheme in {"http", "https"}:
            from app.external.http_downloader import HttpDownloader

            http_dl = HttpDownloader(timeout_s=timeout)
            http_status, http_ct, http_raw, http_err = await http_dl.download(
                url=url,
                headers=None,
                params=None,
                auth_kind=None,
                auth=None,
                timeout_s=timeout,
                kind="http",
            )
            if http_status < 200 or http_status >= 300:
                return http_status, http_ct, http_raw, http_err

            # A partir daqui, comportamento FTP "root" (path em branco) com host/creds de auth.
            ftp_url = ""
            parsed = urlparse(ftp_url)
            scheme = (parsed.scheme or "").lower()

        # ---- Caminho "normal" FTP ----
        is_ftps = scheme == "ftps"

        host = parsed.hostname
        port = parsed.port or 21
        path = parsed.path or ""

        # Se não vier host na URL, tenta auth.host / auth.hostname / auth.server / auth.ftp_hostname
        if isinstance(auth, dict):
            if not host:
                host = (
                    auth.get("host")
                    or auth.get("hostname")
                    or auth.get("server")
                    or auth.get("ftp_hostname")
                )
            port_val = auth.get("port")
            try:
                port = int(port_val) if port_val is not None else port
            except Exception:
                pass

        if not host:
            return 400, None, b"", "FTP host is missing"

        # credenciais
        user = parsed.username
        pwd = parsed.password

        ak = (auth_kind or "").lower()
        if ak == "ftp_password" and isinstance(auth, dict):
            user = auth.get("username") or auth.get("user") or auth.get("ftp_username") or user
            pwd = auth.get("password") or auth.get("pass") or auth.get("ftp_password") or pwd

        if not user:
            user = "anonymous"
        if pwd is None:
            pwd = "anonymous@"

        def _do_download() -> tuple[bytes, str | None]:
            data = bytearray()
            cls = FTP_TLS if is_ftps else FTP
            with cls() as ftp:
                ftp.connect(host, port, timeout=timeout)
                if is_ftps:
                    try:
                        ftp.auth()
                        ftp.prot_p()
                    except Exception:
                        # alguns servidores já vêm em modo protegido
                        pass
                ftp.login(user=user, passwd=pwd)
                ftp.set_pasv(True)

                target_path = path

                # Se não foi dado path, comporta-se como o código antigo:
                # lista o diretório e escolhe o primeiro ficheiro "real".
                if target_path in ("", "/", "."):
                    names = ftp.nlst(".")
                    candidate: str | None = None
                    for name in names:
                        n = name.strip()
                        if not n:
                            continue
                        base = n.rsplit("/", 1)[-1]
                        if base in {".", "..", ".ftpquota"}:
                            continue
                        candidate = n
                        break

                    if not candidate:
                        raise RuntimeError("No data file found in FTP directory")

                    target_path = candidate

                ftp.retrbinary(f"RETR {target_path}", data.extend)

                # apagar ficheiro depois de ler (como no código antigo da Globomatik)
                try:
                    ftp.delete(target_path)
                except Exception:
                    pass

            return bytes(data), guess_content_type_from_path(target_path)

        try:
            content, ct = await asyncio.to_thread(_do_download)
            return 200, ct, content, None
        except Exception as e:
            return 599, None, b"", str(e)
