from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.repositories.procurement.read.supplier_item_read_repo import (
    SupplierItemReadRepository,
)
from app.repositories.catalog.write.product_active_offer_write_repo import (
    ProductActiveOfferWriteRepository,
)
from app.models.product_active_offer import ProductActiveOffer


@dataclass
class BestOfferResult:
    id_supplier: int
    id_supplier_item: int
    unit_cost: float
    stock: int


def get_best_offer_for_product(
    db: Session,
    *,
    id_product: int,
) -> BestOfferResult | None:
    """
    Decide a melhor oferta para um produto com base nas SupplierItem.

    Regras:
    - só considera ofertas com stock > 0
    - ordena por:
        1) menor preço (price)
        2) em empate: maior stock
        3) em empate: menor id_supplier (determinístico)
    """
    if not id_product:
        return None

    si_repo = SupplierItemReadRepository(db)

    # Idealmente tens algo como isto no repo:
    # list_offers_for_product(id_product, only_in_stock=True)
    offers = si_repo.list_offers_for_product(id_product=id_product, only_in_stock=True)

    best: BestOfferResult | None = None

    for item in offers:
        # assumindo que item tem atributos id, id_supplier, price, stock
        if item.price is None or item.stock is None:
            continue

        candidate = BestOfferResult(
            id_supplier=item.id_supplier,
            id_supplier_item=item.id,
            unit_cost=float(item.price),
            stock=int(item.stock),
        )

        if best is None:
            best = candidate
            continue

        # preço menor → melhor
        if candidate.unit_cost < best.unit_cost:
            best = candidate
            continue

        # se preço igual → maior stock
        if candidate.unit_cost == best.unit_cost:
            if candidate.stock > best.stock:
                best = candidate
                continue
            # se stock igual → menor id_supplier
            if candidate.stock == best.stock and candidate.id_supplier < best.id_supplier:
                best = candidate
                continue

    return best


def recalculate_active_offer_for_product(
    db: Session,
    *,
    id_product: int,
) -> ProductActiveOffer:
    """
    Recalcula a oferta ativa de um produto com base nas SupplierItem atuais.

    - Se existir uma best offer → atualiza ProductActiveOffer com supplier/item/custo/stock.
    - Se não existir nenhuma (sem stock) → mantém o registo mas zera supplier/item e stock.

    NÃO faz commit — fica a cargo do UoW/usecase chamador.
    """
    pao_repo = ProductActiveOfferWriteRepository(db)

    best = get_best_offer_for_product(db, id_product=id_product)

    if best is None:
        # Sem ofertas com stock > 0 → oferta ativa "vazia"
        entity = pao_repo.upsert(
            id_product=id_product,
            id_supplier=None,
            id_supplier_item=None,
            unit_cost=None,
            unit_price_sent=None,  # preço PS vem na fase seguinte (margens)
            stock_sent=0,
        )
    else:
        entity = pao_repo.upsert(
            id_product=id_product,
            id_supplier=best.id_supplier,
            id_supplier_item=best.id_supplier_item,
            unit_cost=best.unit_cost,
            unit_price_sent=None,  # a calcular quando formos syncar com PS
            stock_sent=best.stock,
        )

    return entity
