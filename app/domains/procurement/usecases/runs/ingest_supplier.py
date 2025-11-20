from __future__ import annotations

import csv
import io
import json
import logging
from contextlib import suppress
from sqlalchemy.exc import IntegrityError
from typing import Any

from app.core.errors import InvalidArgument, NotFound
from app.core.normalize import normalize_images, normalize_simple
from app.domains.catalog.services.active_offer import (
    recalculate_active_offer_for_product,
)
from app.domains.catalog.services.sync_events import emit_product_state_event
from app.domains.mapping.engine import IngestEngine
from app.external.feed_downloader import http_download, parse_rows_json
from app.infra.uow import UoW
from app.repositories.catalog.read.products_read_repo import ProductsReadRepository
from app.repositories.catalog.write.product_write_repo import ProductWriteRepository
from app.repositories.procurement.read.feed_run_read_repo import FeedRunReadRepository
from app.repositories.procurement.read.mapper_read_repo import MapperReadRepository
from app.repositories.procurement.read.supplier_feed_read_repo import (
    SupplierFeedReadRepository,
)
from app.repositories.procurement.read.supplier_read_repo import SupplierReadRepository
from app.repositories.procurement.write.feed_run_write_repo import (
    FeedRunWriteRepository,
)
from app.repositories.procurement.write.product_event_write_repo import (
    ProductEventWriteRepository,
)
from app.repositories.procurement.write.supplier_item_write_repo import (
    SupplierItemWriteRepository,
)

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


def _decode_csv(raw: bytes, delimiter: str = ",") -> list[dict[str, Any]]:
    """
    Converte um CSV em lista de dicts normalizados (str→str).
    """
    text = raw.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text), delimiter=(delimiter or ","))
    return [{k: (v if v is not None else "") for k, v in row.items()} for row in reader]


def _split_payload(mapped: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """
    Separa o resultado do mapper em:
    - product_payload (campos canónicos de produto)
    - offer_payload   (preço/stock/sku + chaves técnicas)
    - meta_payload    (resto dos campos, não-canónicos)
    """
    out_product = {
        "gtin": (mapped.get("gtin") or "") or None,
        "partnumber": (mapped.get("mpn") or mapped.get("partnumber") or "") or None,
        "name": mapped.get("name"),
        "description": mapped.get("description"),
        "image_url": mapped.get("image_url"),
        "weight_str": mapped.get("weight"),
    }

    out_offer = {
        "price": (mapped.get("price") or "").strip(),
        "stock": int(mapped.get("stock") or 0),
        "sku": (mapped.get("sku") or mapped.get("partnumber") or mapped.get("gtin") or "").strip(),
        "gtin": out_product["gtin"],
        "partnumber": out_product["partnumber"],
    }

    used = set(CANON_PRODUCT_KEYS) | set(CANON_OFFER_KEYS)
    meta = {k: v for k, v in mapped.items() if k not in used and v not in (None, "", [])}
    return out_product, out_offer, meta


async def execute(uow: UoW, *, id_supplier: int, limit: int | None = None) -> dict[str, Any]:
    """
    Orquestra uma run de ingest para um supplier:

    1) Valida supplier/feed e cria FeedRun.
    2) Faz download + parse do feed (CSV/JSON).
    3) Mapeia linhas via IngestEngine e, por cada linha válida:
       - Product.get_or_create + fill canonicals + brand/category + meta.
       - SupplierItem.upsert → deteta created/changed.
       - ProductSupplierEvent.record_from_item_change (init/change).
    4) mark_eol_for_unseen_items → regista events "eol" + devolve products afetados.
    5) Para cada produto afetado com id_ecommerce:
       - recalcula ProductActiveOffer com base nas SupplierItem atuais;
       - compara snapshot anterior vs novo;
       - se mudou (supplier/preço_enviado/stock) → emite product_state_changed
         no CatalogUpdateStream (prioridade em função da transição de stock).
    6) Finaliza FeedRun (ok/erro) e devolve resumo.
    """
    db = uow.db

    # --- Repositórios (CQRS) ---
    run_r = FeedRunReadRepository(db)
    run_w = FeedRunWriteRepository(db)

    sup_r = SupplierReadRepository(db)
    feed_r = SupplierFeedReadRepository(db)
    mapper_r = MapperReadRepository(db)
    prod_r = ProductsReadRepository(db)

    prod_w = ProductWriteRepository(db)
    item_w = SupplierItemWriteRepository(db)
    ev_w = ProductEventWriteRepository(db)

    # --- 1) Supplier + Feed + Run ---
    supplier = sup_r.get_required(id_supplier)
    supplier_margin = float(supplier.margin or 0.0)

    feed = feed_r.get_by_supplier(id_supplier)
    if not feed or not feed.active:
        raise NotFound("Feed not found for supplier")

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
        # --- 2) Download + parse feed ---
        headers = json.loads(feed.headers_json) if feed.headers_json else None
        params = json.loads(feed.params_json) if feed.params_json else None

        status_code, content_type, raw = await http_download(
            feed.url,
            headers=headers,
            params=params,
            timeout_s=60,
        )

        if status_code < 200 or status_code >= 300:
            run_w.finalize_http_error(
                id_run,
                http_status=status_code,
                error_msg=f"HTTP {status_code}",
            )
            uow.commit()
            log.error("[run=%s] download error: HTTP %s", id_run, status_code)
            return {"ok": False, "id_run": id_run, "error": f"HTTP {status_code}"}

        fmt = (feed.format or "").lower()
        if fmt == "json":
            rows: list[dict[str, Any]] = parse_rows_json(raw)
        else:
            rows = _decode_csv(raw, delimiter=(feed.csv_delimiter or ","))

        total = len(rows)
        if limit is not None:
            rows = rows[:limit]

        log.info(
            "[run=%s] fetched rows: total=%s using=%s",
            id_run,
            total,
            len(rows),
        )

        # --- 3) Mapping + persistência linha-a-linha ---
        profile = mapper_r.profile_for_feed(feed.id)  # {} se não existir/for inválido
        engine = IngestEngine(profile)

        affected_products: set[int] = set()
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
            raw_category_name = mapped.get("category") or None

            brand_name = normalize_simple(raw_brand_name) if raw_brand_name else None
            category_name = normalize_simple(raw_category_name) if raw_category_name else None

            # 3.1) Produto canónico
            try:
                p = prod_w.get_or_create(
                    gtin=gtin,
                    partnumber=pn,
                    brand_name=brand_name,
                    default_margin=supplier_margin,
                )
            except InvalidArgument:
                bad += 1
                log.warning("[run=%s] row#%s skipped (no product key)", id_run, idx)
                continue
            except IntegrityError as ie:
                # race/unique — tenta recuperar
                db.rollback()
                p = prod_w.get_by_gtin(gtin) if gtin else None
                if not p and (brand_name and pn):
                    try:
                        p = prod_w.get_or_create(
                            gtin=None,
                            partnumber=pn,
                            brand_name=brand_name,
                        )
                    except Exception:
                        p = None

                if not p:
                    bad += 1
                    log.warning(
                        "[run=%s] row#%s skipped after IntegrityError: %s",
                        id_run,
                        idx,
                        ie,
                    )
                    continue

            # 3.2) Preencher campos canónicos vazios + brand/category
            prod_w.fill_canonicals_if_empty(
                p.id,
                name=product_payload.get("name"),
                description=product_payload.get("description"),
                image_url=product_payload.get("image_url"),
                weight_str=product_payload.get("weight_str"),
                partnumber=pn,
                gtin=gtin,
            )
            prod_w.fill_brand_category_if_empty(
                p.id,
                brand_name=brand_name,
                category_name=category_name,
            )

            # 3.3) Meta não-canónica
            for k, v in meta_payload.items():
                if v in (None, "", []):
                    continue
                inserted, _conflict = prod_w.add_meta_if_missing(
                    p.id,
                    name=str(k),
                    value=str(v),
                )
                if inserted:
                    changed += 1

            # 3.4) Upsert da oferta do fornecedor
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

            affected_products.add(p.id)

            # 3.5) Evento por criação/alteração da oferta do supplier
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
                log.info(
                    "[run=%s] progress %s/%s ok=%s bad=%s",
                    id_run,
                    idx,
                    len(rows),
                    ok,
                    bad,
                )

        # --- 4) EOL dos itens não vistos neste run ---
        eol_res = ev_w.mark_eol_for_unseen_items(
            id_feed=feed.id,
            id_supplier=id_supplier,
            id_feed_run=id_run,
        )
        eol_marked = eol_res.items_stock_changed  # “mudanças reais”
        eol_unseen = eol_res.items_total  # “desaparecidos do feed”
        affected_products.update(eol_res.affected_products)

        log.info("[run=%s] EOL marked=%s", id_run, eol_marked)

        # --- 5) Active offer + eventos de estado (apenas para produtos com id_ecommerce) ---
        for id_product in affected_products:
            product = prod_r.get(id_product)

            if not product:
                continue

            # snapshot da oferta ativa ANTES do recálculo
            prev_active_snapshot: dict[str, Any] | None = None
            if product.active_offer is not None:
                ao = product.active_offer
                prev_active_snapshot = {
                    "id_supplier": ao.id_supplier,
                    "id_supplier_item": ao.id_supplier_item,
                    "unit_price_sent": float(ao.unit_price_sent)
                    if ao.unit_price_sent is not None
                    else None,
                    "stock_sent": int(ao.stock_sent or 0),
                }

            # se o produto não está ligado ao PrestaShop, não há nada para emitir
            if not product.id_ecommerce or product.id_ecommerce <= 0:
                continue

            # recalcula ProductActiveOffer com base nas SupplierItem atuais
            new_active = recalculate_active_offer_for_product(
                db,
                id_product=id_product,
            )

            # emite evento apenas se o snapshot efetivo mudou
            emit_product_state_event(
                db,
                product=product,
                active_offer=new_active,
                reason="ingest_supplier",
                prev_active_snapshot=prev_active_snapshot,
            )

        # --- 6) Finalizar run + commit ---
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
            "eol_unseen": eol_unseen,
            "eol_marked": eol_marked,
            "status": status,
        }

    except Exception as e:
        # Hard-fail da run
        with suppress(Exception):
            db.rollback()

        try:
            run_w.finalize_error(
                id_run,
                error_msg=f"{type(e).__name__}: {e}",
            )
            uow.commit()
        except Exception:
            with suppress(Exception):
                db.rollback()

        log.exception("[run=%s] ingest failed", id_run)
        return {"ok": False, "id_run": id_run, "error": str(e)}
