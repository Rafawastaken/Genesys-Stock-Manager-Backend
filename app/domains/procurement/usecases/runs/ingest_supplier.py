# app/domains/procurement/usecases/runs/ingest_supplier.py
from __future__ import annotations

import csv
import io
import json
import logging
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.core.errors import InvalidArgument, NotFound  # << NOVO
from app.core.normalize import normalize_images
from app.domains.catalog.repos import ProductRepository
from app.domains.mapping.engine import IngestEngine
from app.domains.procurement.repos import (
    FeedRunRepository,
    MapperRepository,
    ProductEventRepository,
    SupplierFeedRepository,
    SupplierItemRepository,
)
from app.external.feed_downloader import http_download, parse_rows_json
from app.infra.uow import UoW
from contextlib import suppress

log = logging.getLogger("gsm.ingest")

CANON_PRODUCT_KEYS = {
    "gtin",
    "mpn",
    "partnumber",
    "name",
    "description",
    "image_url",
    "image_urls",
    "category",
    "weight",
    "brand",
}
CANON_OFFER_KEYS = {"price", "stock", "sku"}


def _decode_csv(raw: bytes, delimiter: str = ",") -> list[dict]:
    """Convert CSV bytes into list[dict] (utf-8; ignore errors)."""
    text = raw.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text), delimiter=(delimiter or ","))
    return [{k: (v if v is not None else "") for k, v in row.items()} for row in reader]


def _split_payload(mapped: dict[str, Any]):
    out_product = {
        "gtin": (mapped.get("gtin") or "") or None,
        "partnumber": (mapped.get("mpn") or mapped.get("partnumber") or "") or None,
        "name": mapped.get("name"),
        "description": mapped.get("description"),
        "image_url": mapped.get("image_url"),
        "category_path": mapped.get("category"),
        "weight_str": mapped.get("weight"),
    }
    out_offer = {
        "price": (mapped.get("price") or "").strip(),
        "stock": int(mapped.get("stock") or 0),
        "sku": (mapped.get("sku") or mapped.get("partnumber") or mapped.get("gtin") or "").strip(),
        "gtin": out_product["gtin"],
        "partnumber": out_product["partnumber"],
    }
    used = set(CANON_PRODUCT_KEYS) | set(CANON_OFFER_KEYS) | {"category_path", "weight_str"}
    meta = {k: v for k, v in mapped.items() if k not in used and v not in (None, "", [])}
    return out_product, out_offer, meta


async def execute(uow: UoW, *, id_supplier: int, limit: int | None = None) -> dict[str, Any]:
    # repositories
    run_repo = FeedRunRepository(uow.db)
    feed_repo = SupplierFeedRepository(uow.db)
    mapper_repo = MapperRepository(uow.db)
    prod_repo = ProductRepository(uow.db)
    item_repo = SupplierItemRepository(uow.db)
    ev_repo = ProductEventRepository(uow.db)

    # validate supplier feed
    feed = feed_repo.get_by_supplier(id_supplier)
    if not feed or not feed.active:
        # era HTTPException(404) → agora AppError tratado pelo middleware
        raise NotFound("Feed not found for supplier")

    # start run
    run = run_repo.start(id_feed=feed.id)
    id_run = run.id
    log.info(
        "[run=%s] start ingest id_supplier=%s id_feed=%s format=%s url=%s",
        id_run,
        id_supplier,
        feed.id,
        feed.format,
        feed.url,
    )

    try:
        # download
        headers = json.loads(feed.headers_json) if feed.headers_json else None
        params = json.loads(feed.params_json) if feed.params_json else None
        status_code, content_type, raw = await http_download(
            feed.url, headers=headers, params=params, timeout_s=60
        )

        if status_code < 200 or status_code >= 300:
            run_repo.finalize_http_error(
                id_run, http_status=status_code, error_msg=f"HTTP {status_code}"
            )
            uow.commit()
            log.error("[run=%s] download error: HTTP %s", id_run, status_code)
            return {"ok": False, "id_run": id_run, "error": f"HTTP {status_code}"}

        # parse rows
        fmt = (feed.format or "").lower()
        rows: list[dict]
        if fmt == "json":
            rows = parse_rows_json(raw)
        else:
            rows = _decode_csv(raw, delimiter=(feed.csv_delimiter or ","))

        total = len(rows)
        if limit is not None:
            rows = rows[:limit]
        log.info("[run=%s] fetched rows: total=%s using=%s", id_run, total, len(rows))

        # mapping engine
        profile = mapper_repo.get_profile(feed.id)
        engine = IngestEngine(profile)

        ok = bad = changed = 0

        for idx, raw_row in enumerate(rows, 1):
            mapped, err = engine.map_row(raw_row)
            if not mapped:
                bad += 1
                log.warning("[run=%s] row#%s invalid (mapper): %s", id_run, idx, err)
                continue

            mapped = normalize_images(mapped)

            product_payload, offer_payload, meta_payload = _split_payload(mapped)

            gtin = product_payload.get("gtin") or None
            pn = product_payload.get("partnumber") or None
            brand_name = mapped.get("brand") or None
            category_name = product_payload.get("category_path") or None

            # product: get_or_create by GTIN; fallback Brand+MPN
            try:
                p = prod_repo.get_or_create(gtin=gtin, partnumber=pn, brand_name=brand_name)
            except InvalidArgument:
                # era ValueError → agora InvalidArgument do nosso domínio
                bad += 1
                log.warning("[run=%s] row#%s skipped (no product key)", id_run, idx)
                continue
            except IntegrityError as ie:
                # race/unique — short rollback and try to fetch
                uow.db.rollback()
                p = prod_repo.get_by_gtin(gtin) if gtin else None
                if not p and (brand_name and pn):
                    try:
                        p = prod_repo.get_or_create(gtin=None, partnumber=pn, brand_name=brand_name)
                    except Exception:
                        p = None
                if not p:
                    bad += 1
                    log.warning("[run=%s] row#%s skipped after IntegrityError: %s", id_run, idx, ie)
                    continue

            # fill canonicals if empty + associate brand/category if missing
            prod_repo.fill_canonicals_if_empty(
                p.id,
                name=product_payload.get("name"),
                description=product_payload.get("description"),
                image_url=product_payload.get("image_url"),
                category_path=product_payload.get("category_path"),
                weight_str=product_payload.get("weight_str"),
                partnumber=pn,
                gtin=gtin,
            )
            prod_repo.fill_brand_category_if_empty(
                p.id,
                brand_name=brand_name,
                category_name=category_name,
            )

            # non-canonical meta: insert-if-missing (no images)
            for k, v in meta_payload.items():
                if v in (None, "", []):
                    continue
                inserted, conflict = prod_repo.add_meta_if_missing(p.id, name=str(k), value=str(v))
                if inserted:
                    changed += 1

            # supplier offer upsert ((id_feed, sku) + internal fingerprint)
            price = offer_payload["price"]
            stock = offer_payload["stock"]
            sku = offer_payload["sku"] or (pn or gtin or f"row-{idx}")

            item, created, changed_item, old_price, old_stock = item_repo.upsert(
                id_feed=feed.id,
                id_product=p.id,
                sku=sku,
                price=price,
                stock=stock,
                gtin=gtin,
                partnumber=pn,
                id_feed_run=id_run,
            )

            # 1 line decides the event:
            changed += ev_repo.record_from_item_change(
                id_product=p.id,
                id_supplier=id_supplier,
                gtin=gtin,
                new_price=price,
                new_stock=stock,
                created=created,
                changed=changed_item,
                id_feed_run=id_run,
            )

            ok += 1

            if idx % 500 == 0:
                log.info("[run=%s] progress %s/%s ok=%s bad=%s", id_run, idx, len(rows), ok, bad)

        # mark EOL for unseen items this run
        eol_marked = ev_repo.mark_eol_for_unseen_items(
            id_feed=feed.id, id_supplier=id_supplier, id_feed_run=id_run
        )
        log.info("[run=%s] EOL marked=%s", id_run, eol_marked)

        # finalize run
        run_repo.finalize_ok(
            id_run,
            rows_total=total,
            rows_changed=changed,
            partial=bool(bad and ok),
        )
        uow.commit()

        status = run_repo.get(id_run).status  # return to caller
        log.info(
            "[run=%s] done status=%s total=%s ok=%s bad=%s changed=%s eol=%s",
            id_run,
            status,
            total,
            ok,
            bad,
            changed,
            eol_marked,
        )

        return {
            "ok": True,
            "id_run": id_run,
            "rows_total": total,
            "rows_processed": ok + bad,
            "rows_valid": ok,
            "rows_invalid": bad,
            "changes": changed,
            "eol_marked": eol_marked,
            "status": status,
        }

    except Exception as e:
        # rollback and try to mark run as error
        with suppress(Exception):
            uow.db.rollback()

        try:
            run_repo.finalize_error(id_run, error_msg=f"{type(e).__name__}: {e}")
            uow.commit()
        except Exception:
            # se falhar a finalização, tentar rollback mas sem ruído
            with suppress(Exception):
                uow.db.rollback()

        log.exception("[run=%s] ingest failed", id_run)
        return {"ok": False, "id_run": id_run, "error": str(e)}
