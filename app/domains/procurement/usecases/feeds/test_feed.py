# app/domains/procurement/usecases/feeds/test_feed.py
from __future__ import annotations

from app.core.errors import BadRequest
from app.external.feed_downloader import FeedDownloader
from app.schemas.feeds import FeedTestRequest, FeedTestResponse


async def execute(payload: FeedTestRequest) -> FeedTestResponse:
    downloader = FeedDownloader()
    try:
        return await downloader.preview(payload)
    except Exception as e:
        raise BadRequest(f"Could not preview feed: {e}")
