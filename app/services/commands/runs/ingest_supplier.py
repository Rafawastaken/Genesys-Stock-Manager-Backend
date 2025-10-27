# app/services/commands/runs/ingest_supplier.py
from __future__ import annotations

from typing import Optional, Dict, Any, List, Tuple
import csv
import io
import json
import logging

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.infra.uow import UoW
from app.repositories.feed_run_repo import FeedRunRepository
from app.repositories.supplier_feed_repo import SupplierFeedRepository
from app.repositories.mapper_repo import MapperRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.supplier_item_repo import SupplierItemRepository
from app.repositories.product_event_repo import ProductEventRepository
from app.domain.ingest_engine import IngestEngine
from app.core.normalize import normalize_images
from app.external.feed_downloader import http_download, parse_rows_json

log = logging.getLogger("gsm.ingest")

CANON_PRODUCT_KEYS = {
    "gtin", "mpn", "partnumber", "name", "description",
    "image_url", "image_urls",
    "category", "weight", "brand",
}
CANON_OFFER_KEYS = {"price", "stock", "sku"}


def _decode_csv(raw: bytes, delimiter: str = ",") -> List[dict]:
    """Converte bytes CSV em lista de dicts (utf-8; ignora erros)."""
    text = raw.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text), delimiter=(delimiter or ","))
    return [{k: (v if v is not None else "") for k, v in row.items()} for row in reader]


def _split_payload(mapped: Dict[str, Any]):
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



async def handle(uow: UoW, *, supplier_id: int, limit: Optional[int] = None) -> Dict[str, Any]:
    # repos
    run_repo    = FeedRunRepository(uow.db)
    feed_repo   = SupplierFeedRepository(uow.db)
    mapper_repo = MapperRepository(uow.db)
    prod_repo   = ProductRepository(uow.db)
    item_repo   = SupplierItemRepository(uow.db)
    ev_repo     = ProductEventRepository(uow.db)

    # valida feed do fornecedor
    feed = feed_repo.get_by_supplier(supplier_id)
    if not feed or not feed.active:
        raise HTTPException(status_code=404, detail="Feed not found for supplier")

    # inicia run
    run = run_repo.start(id_feed=feed.id)
    run_id = run.id
    log.info("[run=%s] start ingest supplier_id=%s feed_id=%s format=%s url=%s",
             run_id, supplier_id, feed.id, feed.format, feed.url)

    try:
        # download
        headers = json.loads(feed.headers_json) if feed.headers_json else None
        params  = json.loads(feed.params_json) if feed.params_json else None
        status_code, content_type, raw = await http_download(
            feed.url, headers=headers, params=params, timeout_s=60
        )

        if status_code < 200 or status_code >= 300:
            run_repo.finalize_http_error(run_id, http_status=status_code, error_msg=f"HTTP {status_code}")
            uow.commit()
            log.error("[run=%s] download error: HTTP %s", run_id, status_code)
            return {"ok": False, "run_id": run_id, "error": f"HTTP {status_code}"}

        # parse rows
        fmt = (feed.format or "").lower()
        rows: List[dict]
        if fmt == "json":
            rows = parse_rows_json(raw)
        else:
            rows = _decode_csv(raw, delimiter=(feed.csv_delimiter or ","))

        total = len(rows)
        if limit is not None:
            rows = rows[:limit]
        log.info("[run=%s] fetched rows: total=%s using=%s", run_id, total, len(rows))

        # engine de mapeamento
        profile = mapper_repo.get_profile(feed.id)
        engine = IngestEngine(profile)

        ok = bad = changed = 0

        for idx, raw_row in enumerate(rows, 1):
            mapped, err = engine.map_row(raw_row)
            if not mapped:
                bad += 1
                log.warning("[run=%s] row#%s invalid (mapper): %s", run_id, idx, err)
                continue

            # normalizações (ex: image_url/image_urls)
            mapped = normalize_images(mapped)

            product_payload, offer_payload, meta_payload = _split_payload(mapped)

            gtin = product_payload.get("gtin") or None
            pn   = product_payload.get("partnumber") or None
            brand_name    = (mapped.get("brand") or None)
            category_name = product_payload.get("category_path") or None

            # produto: get_or_create por GTIN; fallback Brand+MPN
            try:
                p = prod_repo.get_or_create(gtin=gtin, partnumber=pn, brand_name=brand_name)
            except ValueError:
                bad += 1
                log.warning("[run=%s] row#%s skipped (no product key)", run_id, idx)
                continue
            except IntegrityError as ie:
                # corrida/unique — rollback curto e tenta obter
                uow.db.rollback()
                p = prod_repo.get_by_gtin(gtin) if gtin else None
                if not p and (brand_name and pn):
                    try:
                        p = prod_repo.get_or_create(gtin=None, partnumber=pn, brand_name=brand_name)
                    except Exception:
                        p = None
                if not p:
                    bad += 1
                    log.warning("[run=%s] row#%s skipped after IntegrityError: %s", run_id, idx, ie)
                    continue

            # preencher canónicos só se vazio + associar brand/category se em falta
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

            # meta extra: insert-if-missing (sem images)
            for k, v in meta_payload.items():
                if v in (None, "", []):
                    continue
                inserted, conflict = prod_repo.add_meta_if_missing(
                    p.id, name=str(k), value=str(v)
                )
                if inserted:
                    changed += 1

            # oferta do fornecedor (upsert por (feed_id, sku) + fingerprint interno do repo)
            price = offer_payload["price"]
            stock = offer_payload["stock"]
            sku   = offer_payload["sku"] or (pn or gtin or f"row-{idx}")

            item, created, changed_item, old_price, old_stock = item_repo.upsert(
                id_feed=feed.id,
                id_product=p.id,
                sku=sku,
                price=price,
                stock=stock,
                gtin=gtin,
                partnumber=pn,
                id_feed_run=run_id,
            )

            # 1 linha que decide o evento:
            changed += ev_repo.record_from_item_change(
                id_product=p.id,
                id_supplier=supplier_id,
                gtin=gtin,
                new_price=price,
                new_stock=stock,
                created=created,
                changed=changed_item,
                id_feed_run=run_id,
            )

            ok += 1

            if idx % 500 == 0:
                log.info("[run=%s] progress %s/%s ok=%s bad=%s",
                         run_id, idx, len(rows), ok, bad)

        # marca EOL para itens não vistos neste run
        eol_marked = ev_repo.mark_eol_for_unseen_items(
            id_feed=feed.id, id_supplier=supplier_id, id_feed_run=run_id
        )
        log.info("[run=%s] EOL marked=%s", run_id, eol_marked)

        # finaliza run
        run_repo.finalize_ok(
            run_id,
            rows_total=total,
            rows_changed=changed,
            partial=bool(bad and ok),
        )
        uow.commit()

        status = run_repo.get(run_id).status  # para devolver ao caller
        log.info(
            "[run=%s] done status=%s total=%s ok=%s bad=%s changed=%s eol=%s",
            run_id, status, total, ok, bad, changed, eol_marked
        )

        return {
            "ok": True,
            "run_id": run_id,
            "rows_total": total,
            "rows_processed": ok + bad,
            "rows_valid": ok,
            "rows_invalid": bad,
            "changes": changed,
            "eol_marked": eol_marked,
            "status": status,
        }

    except Exception as e:
        # rollback e tentativa de marcar run como erro
        try:
            uow.db.rollback()
        except Exception:
            pass
        try:
            run_repo.finalize_error(run_id, error_msg=f"{type(e).__name__}: {e}")
            uow.commit()
        except Exception:
            try:
                uow.db.rollback()
            except Exception:
                pass
        log.exception("[run=%s] ingest failed", run_id)
        return {"ok": False, "run_id": run_id, "error": str(e)}
