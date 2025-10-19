# app/infra/base.py
# Base module for SQLAlchemy ORM models and utility functions.

from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import declarative_base

from app.core.config import settings

Base = declarative_base()

def utcnow() -> datetime:
    return datetime.now(settings.TIMEZONE or timezone.utc)