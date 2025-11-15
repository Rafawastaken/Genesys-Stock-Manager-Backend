# app/domains/catalog/read_services/series.py
from __future__ import annotations
from datetime import datetime
from app.schemas.products import ProductEventOut, SeriesPointOut


def aggregate_daily_points(events: list[ProductEventOut]) -> list[SeriesPointOut]:
    bucket: dict[str, SeriesPointOut] = {}
    for e in events:
        day = e.created_at.strftime("%Y-%m-%d")  # <- created_at
        bucket[day] = SeriesPointOut(
            date=datetime.fromisoformat(day + "T00:00:00"),
            price=e.price,
            stock=e.stock,
        )
    return [bucket[k] for k in sorted(bucket.keys())]
