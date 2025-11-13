# app/repositories/write/feed_run_write_repo.py
from __future__ import annotations

from sqlalchemy.orm import Session
from app.core.errors import NotFound
from app.models.feed_run import FeedRun


class FeedRunWriteRepository:
    def __init__(self, db: Session):
        self.db = db

    # helper interno para evitar dependência cruzada do read repo
    def _get_required(self, id_run: int) -> FeedRun:
        run = self.db.get(FeedRun, id_run)
        if not run:
            raise NotFound("Run not found")
        return run

    def start(self, *, id_feed: int) -> FeedRun:
        run = FeedRun(id_feed=id_feed, status="running")
        self.db.add(run)
        self.db.flush()
        return run

    def finalize_ok(
        self, id_run: int, *, rows_total: int, rows_changed: int, partial: bool
    ) -> None:
        run = self._get_required(id_run)
        run.status = "partial" if partial else "ok"
        run.rows_total = rows_total
        run.rows_changed = rows_changed
        self.db.flush()

    def finalize_http_error(self, id_run: int, *, http_status: int, error_msg: str) -> None:
        run = self._get_required(id_run)
        run.status = "error"
        run.http_status = http_status
        run.error_msg = (error_msg or "")[:500]
        self.db.flush()

    def finalize_error(self, id_run: int, *, error_msg: str) -> None:
        run = self._get_required(id_run)
        run.status = "error"
        run.error_msg = (error_msg or "")[:500]
        self.db.flush()
