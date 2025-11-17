from __future__ import annotations
from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.base import Base, utcnow


class CatalogUpdateStream(Base):
    __tablename__ = "catalog_update_stream"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Produto em causa
    id_product: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Opcional: id do produto no e-commerce (snapshot na altura do evento)
    id_ecommerce: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # Tipo de evento: por agora vamos focar em "product_state_changed"
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="product_state_changed", index=True
    )

    # Prioridade: 10 = crítico (stock foi para 0), 5 = normal, 1 = baixo
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5, index=True)

    # Estado do processamento: pending | processing | done | failed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)

    # Payload JSON string (snapshot dos dados a sincronizar)
    payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    # Controlo de reprocessamento
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    available_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    product = relationship("Product", backref="catalog_update_events")
