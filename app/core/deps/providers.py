# app/core/deps/providers.py
from typing import Any
from collections.abc import Callable, Awaitable

from app.external.prestashop_client import PrestashopClient
from app.external.feed_downloader import FeedDownloader
from app.schemas.feeds import FeedTestRequest, FeedTestResponse


def get_auth_login() -> Callable[[str, str], dict[str, Any]]:
    return PrestashopClient().login


def get_feed_preview() -> Callable[[FeedTestRequest], Awaitable[FeedTestResponse]]:
    async def _preview(req: FeedTestRequest) -> FeedTestResponse:
        downloader = FeedDownloader()  # instância efémera (stateless por chamada)
        return await downloader.preview(req)

    return _preview
