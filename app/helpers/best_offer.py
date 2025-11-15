from app.schemas.products import OfferOut
from app.helpers.number_conversions import as_decimal


def best_offer(offers: list[OfferOut]) -> OfferOut | None:
    best, best_price = None, None
    for o in offers:
        if (o.stock or 0) <= 0:
            continue
        p = as_decimal(o.price)
        if p is None:
            continue
        if best is None or p < best_price:
            best, best_price = o, p
    return best
