# app/repositories/base.py

from __future__ import annotations
from typing import Generic, TypeVar, Type, Sequence, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

T = TypeVar("T")

class Repository(Generic[T]):
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def get(self, id_entity: int) -> Optional[T]:
        return self.db.get(self.model, id_entity)

    def add(self, entity: T) -> T:
        self.db.add(entity)
        return entity

    def delete(self, entity: T) -> None:
        self.db.delete(entity)

    def list(self) -> Sequence[T]:
        return self.db.execute(select(self.model)).scalars().all()
