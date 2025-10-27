# app/repositories/feed_run_repo.py
from sqlalchemy.orm import Session
from app.models.feed_run import FeedRun

class FeedRunRepository:
    def __init__(self, db: Session):
        self.db = db

    def start(self, *, id_feed: int) -> FeedRun:
        run = FeedRun(id_feed=id_feed, status="running")
        self.db.add(run)
        self.db.flush()
        return run

    def finalize_ok(self, id_run: int, *, rows_total: int, rows_changed: int, partial: bool) -> None:
        run = self.db.get(FeedRun, id_run)
        run.status = "partial" if partial else "ok"
        run.rows_total = rows_total
        run.rows_changed = rows_changed
        self.db.flush()

    def finalize_http_error(self, id_run: int, *, http_status: int, error_msg: str) -> None:
        run = self.db.get(FeedRun, id_run)
        run.status = "error"
        run.http_status = http_status
        run.error_msg = error_msg[:500]
        self.db.flush()

    def finalize_error(self, id_run: int, *, error_msg: str) -> None:
        run = self.db.get(FeedRun, id_run)
        run.status = "error"
        run.error_msg = error_msg[:500]
        self.db.flush()

    def get(self, id_run: int) -> FeedRun | None:
        return self.db.get(FeedRun, id_run)
