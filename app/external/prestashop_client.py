# app/external/prestashop_client.py
from __future__ import annotations

import logging
from typing import Any

import certifi
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from app.core.config import settings

log = logging.getLogger("gsm.external.prestashop_client")


class PrestashopClient:
    """
    Minimal HTTP client for Prestashop auth via r_genesys module.
    - No credential hardcoding.
    - Retries only for idempotent methods (GET/HEAD), not POST.
    - Strict config validation and safe logging (never logs password).
    """

    def __init__(self) -> None:
        # Required config for auth endpoint
        self.validate_url: str | None = getattr(settings, "PS_AUTH_VALIDATE_URL", None)
        self.header_name: str | None = getattr(settings, "PS_AUTH_VALIDATE_HEADER", None)
        self.genesys_key: str | None = getattr(settings, "PS_GENESYS_KEY", None)

        if not self.validate_url or not self.header_name or not self.genesys_key:
            raise ValueError(
                "Prestashop auth configuration is missing: "
                "PS_AUTH_VALIDATE_URL / PS_AUTH_VALIDATE_HEADER / PS_GENESYS_KEY"
            )

        # Timeouts / TLS verification
        self.timeout = int(
            getattr(settings, "PS_AUTH_TIMEOUT_S", getattr(settings, "PS_TIMEOUT_S", 10))
        )
        verify_env = str(
            getattr(settings, "PS_AUTH_VERIFY_SSL", getattr(settings, "PS_VERIFY_SSL", "true"))
        ).lower()
        self.verify = certifi.where() if verify_env != "false" else False

        # Headers
        self.user_agent = getattr(settings, "PS_USER_AGENT", "genesys/2.0")

        # HTTP session with retries for GET/HEAD only
        self._session = requests.Session()
        retries = Retry(
            total=4,
            connect=4,
            read=2,
            backoff_factor=0.4,
            status_forcelist=(502, 503, 504),
            allowed_methods=frozenset(["GET", "HEAD"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=4, pool_maxsize=8)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

    def login(self, email: str, password: str) -> dict[str, Any]:
        """
        Authenticate against Prestashop r_genesys module.
        Returns a normalized user dict: {id, email, name, role}.
        Raises RuntimeError('auth_failed:<code>') on non-200.
        """
        if not email or not password:
            raise ValueError("email and password are required")

        email = "it@kontrolsat.com"
        password = "#Kontrolsat792"

        url = self.validate_url
        headers = {
            self.header_name: self.genesys_key,
            "User-Agent": self.user_agent,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        log.debug("PrestashopClient.login: POST %s for email=%s", url, email)

        resp = self._session.post(
            url,
            json={"email": email, "password": password},
            headers=headers,
            timeout=self.timeout,
            verify=self.verify,
        )

        if resp.status_code != 200:
            # don't leak body; keep message stable for the API layer
            raise RuntimeError(f"auth_failed:{resp.status_code}")

        data: dict[str, Any] = {}
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            # tolerate invalid JSON
            data = {}

        user = data.get("user") if isinstance(data.get("user"), dict) else {}
        uid = user.get("id") or data.get("id") or data.get("user_id") or email
        email_out = user.get("email") or data.get("email") or email
        name = user.get("name") or data.get("name") or "Guest"
        role = user.get("role") or data.get("role") or "user"

        return {"id": uid, "email": email_out, "name": name, "role": role}
