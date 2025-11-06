# app/infra/base.py
# Base module for SQLAlchemy ORM models and utility functions.

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import declarative_base

Base = declarative_base()


def utcnow() -> datetime:
    return datetime.utcnow()
