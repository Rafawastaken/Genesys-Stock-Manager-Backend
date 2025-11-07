# app/repositories/brand_repo.py
from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.errors import InvalidArgument, NotFound
from app.models.brand import Brand
from app.core.normalize import normalize_simple, normalize_key_ci  # << usar os helpers

MAX_NAME_LEN = 200


class BrandRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id_brand: int) -> Brand | None:
        return self.db.get(Brand, id_brand)

    def get_required(self, id_brand: int) -> Brand:
        b = self.get(id_brand)
        if not b:
            raise NotFound("Brand not found")
        return b

    def get_by_name(self, name: str) -> Brand | None:
        """
        Lookup case-insensitive com trim no lado da BD:
        evita duplicados como 'Vulcano', ' VULCANO ' ou 'vulcano'.
        """
        key = normalize_key_ci(name, MAX_NAME_LEN)
        if not key:
            return None
        return (
            self.db.execute(select(Brand).where(func.lower(func.btrim(Brand.name)) == key).limit(1))
            .scalars()
            .first()
        )

    def get_or_create(self, name: str) -> Brand:
        """
        Normaliza antes de gravar (trim, remove símbolos, colapsa espaços, truncate),
        faz dedupe CI e protege contra corridas com IntegrityError (índice único CI).
        """
        shown = normalize_simple(name, MAX_NAME_LEN)  # o que fica guardado/mostrado
        key = normalize_key_ci(name, MAX_NAME_LEN)  # só para dedupe/lookup

        if not key:
            raise InvalidArgument("Brand name is empty")

        existing = self.get_by_name(shown)
        if existing:
            return existing

        b = Brand(name=shown)
        self.db.add(b)
        try:
            self.db.flush()  # sem commit; UoW decide
            return b
        except IntegrityError:
            # outra transação inseriu a mesma brand entre o lookup e o flush
            self.db.rollback()
            again = self.get_by_name(shown)
            if again:
                return again
            raise

    def list(self, *, q: str | None, page: int, page_size: int):
        stmt = select(Brand)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(Brand.name.ilike(like))
        stmt = stmt.order_by(Brand.name.asc())

        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        rows = self.db.execute(stmt.limit(page_size).offset((page - 1) * page_size)).scalars().all()
        return rows, int(total)

    def create(self, name: str) -> Brand:
        return self.get_or_create(name)

    def update(self, id_brand: int, *, name: str | None = None) -> Brand:
        b = self.get_required(id_brand)
        if name is not None:
            shown = normalize_simple(name, MAX_NAME_LEN)
            key = normalize_key_ci(name, MAX_NAME_LEN)
            if not key:
                raise InvalidArgument("Brand name is empty")

            other = self.get_by_name(shown)  # CI
            if other and other.id != b.id:
                raise InvalidArgument("Brand name already exists")

            b.name = shown
        self.db.flush()
        return b

    def delete(self, id_brand: int) -> None:
        b = self.get_required(id_brand)
        self.db.delete(b)
