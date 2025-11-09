# app/core/deps/providers.py
from typing import Any
from collections.abc import Callable
from app.external.prestashop_client import PrestashopClient


def get_auth_login() -> Callable[[str, str], dict[str, Any]]:
    return PrestashopClient().login
