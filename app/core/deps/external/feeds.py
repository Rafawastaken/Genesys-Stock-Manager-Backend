from collections.abc import Awaitable, Callable
from app.external.feed_downloader import FeedDownloader
from app.schemas.feeds import FeedTestRequest, FeedTestResponse

PreviewFn = Callable[[FeedTestRequest], Awaitable[FeedTestResponse]]


def get_feed_preview() -> PreviewFn:
    async def _preview(req: FeedTestRequest) -> FeedTestResponse:
        return await FeedDownloader().preview(req)  # instância efémera

    return _preview
