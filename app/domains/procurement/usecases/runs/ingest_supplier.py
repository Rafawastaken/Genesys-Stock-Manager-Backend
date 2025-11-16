# app/domains/procurement/usecases/runs/ingest_supplier.py
from __future__ import annotations

import csv
import io
import json
import logging
from contextlib import suppress
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.core.errors import InvalidArgument, NotFound
from app.core.normalize import normalize_images, normalize_simple
from app.domains.mapping.engine import IngestEngine
from app.repositories.catalog.write.product_write_repo import ProductWriteRepository
from app.repositories.procurement.read.feed_run_read_repo import FeedRunReadRepository
from app.repositories.procurement.read.mapper_read_repo import MapperReadRepository
from app.repositories.procurement.read.supplier_feed_read_repo import SupplierFeedReadRepository

from app.repositories.procurement.read.supplier_read_repo import SupplierReadRepository
from app.external.feed_downloader import http_download, parse_rows_json
from app.infra.uow import UoW
from app.repositories.procurement.write.feed_run_write_repo import FeedRunWriteRepository
from app.repositories.procurement.write.product_event_write_repo import ProductEventWriteRepository
from app.repositories.procurement.write.supplier_item_write_repo import SupplierItemWriteRepository

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
    # repos (CQRS)
    run_r = FeedRunReadRepository(uow.db)
    run_w = FeedRunWriteRepository(uow.db)

    sup_r = SupplierReadRepository(uow.db)
    supplier = sup_r.get_required(id_supplier)
    supplier_margin = float(supplier.margin or 0.0)

    feed_r = SupplierFeedReadRepository(uow.db)
    mapper_r = MapperReadRepository(uow.db)

    prod_w = ProductWriteRepository(uow.db)
    item_w = SupplierItemWriteRepository(uow.db)
    ev_w = ProductEventWriteRepository(uow.db)

    # valida feed do supplier
    feed = feed_r.get_by_supplier(id_supplier)
    if not feed or not feed.active:
        raise NotFound("Feed not found for supplier")

    # inicia run
    run = run_w.start(id_feed=feed.id)
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
            run_w.finalize_http_error(
                id_run, http_status=status_code, error_msg=f"HTTP {status_code}"
            )
            uow.commit()
            log.error("[run=%s] download error: HTTP %s", id_run, status_code)
            return {"ok": False, "id_run": id_run, "error": f"HTTP {status_code}"}

        # parse
        fmt = (feed.format or "").lower()
        if fmt == "json":
            rows: list[dict] = parse_rows_json(raw)
        else:
            rows = _decode_csv(raw, delimiter=(feed.csv_delimiter or ","))

        total = len(rows)
        if limit is not None:
            rows = rows[:limit]
        log.info("[run=%s] fetched rows: total=%s using=%s", id_run, total, len(rows))

        # mapping
        profile = mapper_r.profile_for_feed(feed.id)  # devolve {} se não existir/ inválido
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

            raw_brand_name = mapped.get("brand") or None
            raw_category_name = product_payload.get("category_path") or None

            brand_name = normalize_simple(raw_brand_name) if raw_brand_name else None
            category_name = normalize_simple(raw_category_name) if raw_category_name else None

            try:
                p = prod_w.get_or_create(
                    gtin=gtin, partnumber=pn, brand_name=brand_name, default_margin=supplier_margin
                )
            except InvalidArgument:
                bad += 1
                log.warning("[run=%s] row#%s skipped (no product key)", id_run, idx)
                continue
            except IntegrityError as ie:
                # race/unique — tenta recuperar
                uow.db.rollback()
                p = prod_w.get_by_gtin(gtin) if gtin else None
                if not p and (brand_name and pn):
                    try:
                        p = prod_w.get_or_create(gtin=None, partnumber=pn, brand_name=brand_name)
                    except Exception:
                        p = None
                if not p:
                    bad += 1
                    log.warning("[run=%s] row#%s skipped after IntegrityError: %s", id_run, idx, ie)
                    continue

            # canonicals se vazios + associa brand/category se faltarem
            prod_w.fill_canonicals_if_empty(
                p.id,
                name=product_payload.get("name"),
                description=product_payload.get("description"),
                image_url=product_payload.get("image_url"),
                category_path=product_payload.get("category_path"),
                weight_str=product_payload.get("weight_str"),
                partnumber=pn,
                gtin=gtin,
            )
            prod_w.fill_brand_category_if_empty(
                p.id,
                brand_name=brand_name,
                category_name=category_name,
            )

            # meta não-canónica
            for k, v in meta_payload.items():
                if v in (None, "", []):
                    continue
                inserted, _conflict = prod_w.add_meta_if_missing(p.id, name=str(k), value=str(v))
                if inserted:
                    changed += 1

            # upsert da oferta do fornecedor
            price = offer_payload["price"]
            stock = offer_payload["stock"]
            sku = offer_payload["sku"] or (pn or gtin or f"row-{idx}")

            _item, created, changed_item, old_price, old_stock = item_w.upsert(
                id_feed=feed.id,
                id_product=p.id,
                sku=sku,
                price=price,
                stock=stock,
                gtin=gtin,
                partnumber=pn,
                id_feed_run=id_run,
            )

            # evento por criação/alteração
            changed += ev_w.record_from_item_change(
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

        # EOL dos itens não vistos neste run
        eol_marked = ev_w.mark_eol_for_unseen_items(
            id_feed=feed.id, id_supplier=id_supplier, id_feed_run=id_run
        )
        log.info("[run=%s] EOL marked=%s", id_run, eol_marked)

        # finaliza
        run_w.finalize_ok(
            id_run,
            rows_total=total,
            rows_changed=changed,
            partial=bool(bad and ok),
        )
        uow.commit()

        status = (run_r.get(id_run) or run).status
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
        with suppress(Exception):
            uow.db.rollback()
        try:
            run_w.finalize_error(id_run, error_msg=f"{type(e).__name__}: {e}")
            uow.commit()
        except Exception:
            with suppress(Exception):
                uow.db.rollback()
        log.exception("[run=%s] ingest failed", id_run)
        return {"ok": False, "id_run": id_run, "error": str(e)}
