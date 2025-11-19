# app/domains/catalog/services/active_offer.py
from __future__ import annotations

from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models.product_active_offer import ProductActiveOffer
from app.repositories.catalog.write.product_active_offer_write_repo import (
    ProductActiveOfferWriteRepository,
)
from app.repositories.procurement.read.supplier_item_read_repo import (
    SupplierItemReadRepository,
)


@dataclass
class ActiveOfferCandidate:
    id_supplier: int
    id_supplier_item: int | None  # <-- AGORA PODE SER None
    unit_cost: float
    stock: int


def _get(obj, key: str):
    """
    Helper para lidar tanto com dicts como com ORM objects/row mappings.
    """
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def choose_active_offer_candidate(
    db: Session,
    *,
    id_product: int,
) -> ActiveOfferCandidate | None:
    """
    Decide a melhor oferta para um produto com base nas SupplierItem.

    Regras:
    - se existirem ofertas com stock > 0:
        → escolhe a melhor ENTRE essas (menor preço, depois maior stock,
          depois menor id_supplier para desempatar)
    - se NÃO existirem ofertas com stock > 0 mas existirem ofertas:
        → escolhe a melhor oferta global (mesma ordenação), mesmo com stock = 0
    - se não houver ofertas:
        → devolve None
    """
    if not id_product:
        return None

    si_repo = SupplierItemReadRepository(db)

    # Read repo devolve rows/dicts com campos tipo:
    # id_product, id_supplier, price, stock, ...
    offers = si_repo.list_offers_for_product(id_product, only_in_stock=False)

    best_any: ActiveOfferCandidate | None = None
    best_in_stock: ActiveOfferCandidate | None = None

    for item in offers:
        raw_price = _get(item, "price")
        raw_stock = _get(item, "stock")
        id_supplier = _get(item, "id_supplier")
        # pode NÃO existir; tudo bem
        raw_id_supplier_item = _get(item, "id_supplier_item") or _get(item, "id")

        if raw_price is None or raw_stock is None or id_supplier is None:
            # sem estes não dá mesmo para decidir
            continue

        try:
            unit_cost = float(raw_price)
            stock = int(raw_stock)
        except (TypeError, ValueError):
            continue

        id_supplier_item = int(raw_id_supplier_item) if raw_id_supplier_item is not None else None

        candidate = ActiveOfferCandidate(
            id_supplier=int(id_supplier),
            id_supplier_item=id_supplier_item,
            unit_cost=unit_cost,
            stock=stock,
        )

        # -------- best_any (independente de stock) --------
        if best_any is None:
            best_any = candidate
        else:
            if candidate.unit_cost < best_any.unit_cost:
                best_any = candidate
            elif candidate.unit_cost == best_any.unit_cost:
                if candidate.stock > best_any.stock or (
                    candidate.stock == best_any.stock
                    and candidate.id_supplier < best_any.id_supplier
                ):
                    best_any = candidate

        # -------- best_in_stock (stock > 0) --------
        if stock > 0:
            if best_in_stock is None:
                best_in_stock = candidate
            else:
                if candidate.unit_cost < best_in_stock.unit_cost:
                    best_in_stock = candidate
                elif candidate.unit_cost == best_in_stock.unit_cost:
                    if candidate.stock > best_in_stock.stock or (
                        candidate.stock == best_in_stock.stock
                        and candidate.id_supplier < best_in_stock.id_supplier
                    ):
                        best_in_stock = candidate

    # Preferir SEMPRE quem tem stock > 0, se existir
    if best_in_stock is not None:
        return best_in_stock

    # Caso contrário, se houver alguma oferta (mesmo stock 0), usar essa
    return best_any


def recalculate_active_offer_for_product(
    db: Session,
    *,
    id_product: int,
) -> ProductActiveOffer:
    """
    Recalcula a oferta ativa de um produto com base nas SupplierItem atuais.

    - Se existir uma best offer → atualiza ProductActiveOffer com supplier/item/custo/stock.
    - Se não existir nenhuma (sem qualquer oferta) → limpa supplier/item e stock.

    NOTA: Mesmo que a best offer tenha stock = 0, o registo fica com esse
    supplier e stock_sent = 0 — útil para UI/análise. O PrestaShop continuará
    a ver stock 0, não há risco de vender o que não existe.
    """
    pao_repo = ProductActiveOfferWriteRepository(db)

    best = choose_active_offer_candidate(db, id_product=id_product)

    if best is None:
        # Sem ofertas → oferta ativa completamente vazia
        entity = pao_repo.upsert(
            id_product=id_product,
            id_supplier=None,
            id_supplier_item=None,
            unit_cost=None,
            unit_price_sent=None,
            stock_sent=0,
        )
    else:
        entity = pao_repo.upsert(
            id_product=id_product,
            id_supplier=best.id_supplier,
            id_supplier_item=best.id_supplier_item,  # pode ser None, está ok
            unit_cost=best.unit_cost,
            unit_price_sent=None,  # a calcular quando formos syncar com PS
            stock_sent=best.stock,
        )

    return entity
