# app/domains/procurement/usecases/suppliers/update_bundle.py
from __future__ import annotations

from typing import Any
import json

from sqlalchemy.exc import IntegrityError

from app.core.errors import BadRequest, Conflict, NotFound
from app.domains.procurement.repos import (
    MapperRepository,
    SupplierFeedRepository,
    SupplierRepository,
)
from app.domains.procurement.usecases.suppliers.get_supplier_detail import (
    execute as uc_get_detail,
)
from app.infra.uow import UoW
from app.schemas.suppliers import SupplierBundleUpdate, SupplierDetailOut


# -------------------------- helpers -------------------------- #


def _update_supplier_fields(
    sup_repo: SupplierRepository,
    id_supplier: int,
    supplier_data: Any | None,
) -> None:
    if supplier_data is None:
        return

    s = sup_repo.get(id_supplier)
    if not s:
        raise NotFound("Supplier not found")

    for f in (
        "name",
        "active",
        "logo_image",
        "contact_name",
        "contact_phone",
        "contact_email",
        "margin",
        "country",
    ):
        v = getattr(supplier_data, f, None)
        if v is not None:
            setattr(s, f, v)


def _apply_feed_mutations(entity: Any, feed_payload: Any) -> None:
    # campos base
    for f in ("kind", "format", "url", "active", "csv_delimiter", "auth_kind"):
        v = getattr(feed_payload, f, None)
        if v is not None:
            setattr(entity, f, v)

    # blobs JSON
    if getattr(feed_payload, "headers", None) is not None:
        entity.headers_json = json.dumps(feed_payload.headers, ensure_ascii=False)
    if getattr(feed_payload, "params", None) is not None:
        entity.params_json = json.dumps(feed_payload.params, ensure_ascii=False)
    if getattr(feed_payload, "extra", None) is not None:
        entity.extra_json = json.dumps(feed_payload.extra, ensure_ascii=False)
    if getattr(feed_payload, "auth", None) is not None:
        entity.auth_json = json.dumps(feed_payload.auth, ensure_ascii=False)


def _upsert_feed_for_supplier(
    feed_repo: SupplierFeedRepository,
    id_supplier: int,
    feed_payload: Any | None,
) -> Any | None:
    if feed_payload is None:
        return None

    def mutate(e: Any) -> None:
        _apply_feed_mutations(e, feed_payload)

    return feed_repo.upsert_for_supplier(id_supplier, mutate)


def _upsert_mapper_for_feed(
    map_repo: MapperRepository,
    feed_repo: SupplierFeedRepository,
    id_supplier: int,
    feed_entity: Any | None,
    mapper_payload: Any | None,
) -> None:
    if mapper_payload is None:
        return

    feed_e = feed_entity or feed_repo.get_by_supplier(id_supplier)
    if not feed_e:
        raise BadRequest("Cannot upsert mapper without a feed for this supplier")

    feed_id = getattr(feed_e, "id", None) or getattr(feed_e, "id_feed", None)
    if feed_id is None:
        raise BadRequest("Feed entity missing id")

    map_repo.upsert_profile(
        feed_id,
        mapper_payload.profile or {},
        bump_version=mapper_payload.bump_version,
    )


# -------------------------- usecase -------------------------- #


def execute(uow: UoW, *, id_supplier: int, payload: SupplierBundleUpdate) -> SupplierDetailOut:
    sup_repo = SupplierRepository(uow.db)
    feed_repo = SupplierFeedRepository(uow.db)
    map_repo = MapperRepository(uow.db)

    try:
        # 1) Supplier
        _update_supplier_fields(sup_repo, id_supplier, payload.supplier)

        # 2) Feed
        feed_entity = _upsert_feed_for_supplier(feed_repo, id_supplier, payload.feed)

        # 3) Mapper (depende do feed)
        _upsert_mapper_for_feed(map_repo, feed_repo, id_supplier, feed_entity, payload.mapper)

        # tudo OK → commit
        uow.commit()

    except NotFound:
        uow.rollback()
        raise
    except IntegrityError as err:
        uow.rollback()
        raise Conflict("Could not update supplier bundle due to integrity constraints") from err
    except Exception as err:
        uow.rollback()
        raise BadRequest("Could not update supplier bundle") from err

    # Devolver o detalhe atualizado
    return uc_get_detail(uow, id_supplier=id_supplier)
