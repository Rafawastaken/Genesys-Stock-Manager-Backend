# app/repositories/read/feed_run_read_repo.py
from __future__ import annotations

from sqlalchemy.orm import Session
from app.core.errors import NotFound
from app.models.feed_run import FeedRun


class FeedRunReadRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id_run: int) -> FeedRun | None:
        return self.db.get(FeedRun, id_run)

    def get_required(self, id_run: int) -> FeedRun:
        run = self.get(id_run)
        if not run:
            raise NotFound("Run not found")
        return run
