# app/models/Supplier.py
# SQLAlchemy model for Supplier entity


from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, Integer, Numeric
from app.infra.base import Base, utcnow

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    logo_image: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    margin: Mapped[float] = mapped_column(Numeric(7,4), nullable=False, default=0)
    country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=utcnow, nullable=True)
    
    feeds: Mapped[list["SupplierFeed"]] = relationship(back_populates="supplier", cascade="all,delete-orphan")
