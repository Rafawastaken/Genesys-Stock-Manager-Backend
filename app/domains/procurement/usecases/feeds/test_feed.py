from __future__ import annotations
from app.schemas.feeds import FeedTestRequest, FeedTestResponse
from app.external.feed_downloader import FeedDownloader

async def execute(payload: FeedTestRequest) -> FeedTestResponse:
    downloader = FeedDownloader()
    return await downloader.preview(payload)
