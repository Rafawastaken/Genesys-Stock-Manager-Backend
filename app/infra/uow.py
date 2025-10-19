# app/infra/uow.py
# Unit of Work simples para SQLAlchemy

from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session

class UoW:
    """Unit of Work simples: commands fazem commit; queries nunca."""
    def __init__(self, db: Session):
        self.db: Session = db
        self._committed = False

    def commit(self) -> None:
        if not self._committed:
            self.db.commit()
            self._committed = True

    def rollback(self) -> None:
        if not self._committed:
            self.db.rollback()

    def __enter__(self) -> "UoW":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc:
            self.rollback()
        # se não commitarem explicitamente num command, fazemos rollback para segurança
        if not self._committed:
            self.rollback()
