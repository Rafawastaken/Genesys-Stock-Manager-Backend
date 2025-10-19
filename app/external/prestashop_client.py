# app/external/prestashop_client.py
# Client HTTP para Prestashop com retries e configuração personalizada

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import certifi

from app.core.config import settings
from app.core.logging import logging

log = logging.getLogger("gsm.external.prestashop_client")

class PrestashopClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int | None = None,
        user_agent: str | None = None,
    ) -> None:
        self.base_url = base_url or getattr(settings, "PS_BASE_URL", None)
        # Sec
        self.api_key = api_key or getattr(settings, "PS_API_KEY", None)
        self.user_agent = user_agent or getattr(settings, "PS_USER_AGENT", "genesys/2.0")
        # Misc
        self.timeout = timeout or getattr(settings, "PS_TIMEOUT_S", 10)

        # --- HTTP session com retries e CA bundle explícito ---
        self._session = requests.Session()
        retries = Retry(
            total=4,
            connect=4,
            read=2,
            backoff_factor=0.4,
            status_forcelist=(502, 503, 504),
            allowed_methods=frozenset(["GET"]),  # login é POST → sem retry (intencional)
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=4, pool_maxsize=8)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)
        verify_env = str(getattr(settings, "PS_VERIFY_SSL", "true")).lower()
        self._verify = certifi.where() if verify_env != "false" else False

    # --- Autenticação via módulo r_genesys (email/password + X-Genesys-Key) ---
    def login(self, email: str, password: str) -> dict:
        url = settings.PS_AUTH_VALIDATE_URL
        headers = {
            settings.PS_AUTH_VALIDATE_HEADER: settings.PS_GENESYS_KEY,
            "User-Agent": self.user_agent,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        log.debug(f"PrestashopClient.login: POST {url} for email={email} {self.user_agent}")
        
        timeout = int(getattr(settings, "PS_AUTH_TIMEOUT_S", 10))
        verify = certifi.where() if str(getattr(settings, "PS_AUTH_VERIFY_SSL", "true")).lower() != "false" else False

        resp = self._session.post(url, json={"email": email, "password": password}, headers=headers,
                                  timeout=timeout, verify=verify)

        if resp.status_code != 200:
            # não vazar detalhes: devolve erro genérico ao caller
            raise RuntimeError(f"auth_failed:{resp.status_code}")

        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}

        # Normalização mínima (ajusta aos campos reais devolvidos pelo módulo)
        return {
            "id": data.get("id") or data.get("user_id") or email,
            "email": data.get("email", email),
            "name": data.get("name"),
            "role": data.get("role", "user"),
        }
