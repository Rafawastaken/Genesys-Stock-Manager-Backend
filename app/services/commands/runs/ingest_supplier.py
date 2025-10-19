# app/services/commands/runs/ingest_supplier.py
# Ingests supplier feed data into the system.

from __future__ import annotations
from typing import Optional, Dict, Any, List
import json
from fastapi import HTTPException

from app.infra.uow import UoW
from app.repositories.supplier_feed_repo import SupplierFeedRepository
from app.repositories.mapper_repo import MapperRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.supplier_item_repo import SupplierItemRepository
from app.repositories.product_event_repo import ProductEventRepository
from app.models.feed_run import FeedRun
from app.domain.ingest_engine import IngestEngine
from app.core.normalize import normalize_images
from app.external.feed_downloader import http_download, parse_rows_csv, parse_rows_json

async def handle(uow: UoW, *, supplier_id: int, limit: Optional[int] = None) -> Dict[str, Any]:
    feed_repo = SupplierFeedRepository(uow.db)
    mapper_repo = MapperRepository(uow.db)
    prod_repo = ProductRepository(uow.db)
    item_repo = SupplierItemRepository(uow.db)
    ev_repo = ProductEventRepository(uow.db)

    feed = feed_repo.get_by_supplier(supplier_id)
    if not feed or not feed.active:
        raise HTTPException(status_code=404, detail="Feed not found for supplier")

    # cria run
    run = FeedRun(feed_id=feed.id, status="running")
    uow.db.add(run); uow.db.flush()

    # fetch
    headers = json.loads(feed.headers_json) if feed.headers_json else None
    params  = json.loads(feed.params_json) if feed.params_json else None
    auth    = json.loads(feed.auth_json) if feed.auth_json else None  # <- novo
    status_code, ct, raw = await http_download(
        feed.url,
        headers=headers,
        params=params,
        timeout_s=30,
        auth_kind=feed.auth_kind,     # <- novo
        auth=auth,                    # <- novo
    )
    if status_code < 200 or status_code >= 300:
        run.status = "error"; run.error_msg = f"HTTP {status_code}"[:200]
        uow.commit()
        return {"ok": False, "run_id": run.id, "error": run.error_msg}

    # parse rows (json|csv)
    rows: List[Dict[str, Any]] = []
    fmt = (feed.format or "").lower()
    if fmt == "json":
        rows = parse_rows_json(raw)
    elif fmt == "csv":
        rows = parse_rows_csv(raw, delimiter=(feed.csv_delimiter or ","))  # <- usa helper novo
    else:
        rows = []

    if limit is not None:
        rows = rows[:limit]

    # mapper
    profile = mapper_repo.get_or_create_profile(feed.id)
    engine = IngestEngine(profile)

    total = len(rows); ok = bad = 0
    for raw_row in rows:
        mapped, err = engine.map_row(raw_row)
        if not mapped:
            bad += 1; continue
        mapped = normalize_images(mapped)
        gtin = (mapped.get("gtin") or "").strip()
        price = (mapped.get("price") or "").strip()
        stock = int(mapped.get("stock") or 0)
        pn    = (mapped.get("partnumber") or "").strip() or None
        sku   = (mapped.get("sku") or pn or gtin or "").strip() or gtin

        p = prod_repo.get_or_create_by_gtin(gtin)
        prod_repo.fill_canonicals_if_empty(
            p.id, name=mapped.get("name"), description_html=mapped.get("description"),
            image_url=mapped.get("image_url"), category_path=mapped.get("category"),
            weight_str=mapped.get("weight"), partnumber=pn,
        )

        item_repo.upsert(feed_id=feed.id, sku=sku, price=price, stock=stock,
                         gtin=gtin, partnumber=pn, last_seen_run_id=run.id)

        ev_repo.add_change_if_needed(product_id=p.id, supplier_id=supplier_id,
                                     price=price, stock=stock, supplier_partnumber=pn, feed_run_id=run.id)
        ok += 1

    # EOL para não vistos
    eol_marked = ev_repo.mark_eol_for_unseen_items(feed_id=feed.id, supplier_id=supplier_id, feed_run_id=run.id)

    run.status = "partial" if bad and ok else "ok"
    uow.commit()  # persiste tudo (incl. run)

    return {"ok": True, "run_id": run.id, "rows_total": total, "rows_mapped": ok, "rows_invalid": bad, "eol_marked": eol_marked}
