# app/services/commands/feeds/test_feed.py
from __future__ import annotations
from app.schemas.feeds import FeedTestRequest, FeedTestResponse
from app.external.feed_downloader import FeedDownloader

async def handle(payload: FeedTestRequest) -> FeedTestResponse:
    downloader = FeedDownloader()
    return await downloader.preview(payload)
