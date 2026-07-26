"""SQLAlchemy models for catalog products, prices, images and categories."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.infrastructure.database.base import Base


class ProductModel(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_external_id", "external_id", unique=True),
        Index("ix_products_category_external_id", "category_external_id"),
        Index("ix_products_last_synced_at", "last_synced_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category_external_id: Mapped[str | None] = mapped_column(String(128))
    subcategory_external_id: Mapped[str | None] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    availability: Mapped[str] = mapped_column(String(32), nullable=False)
    protected_fields: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    price_options: Mapped[list[ProductPriceOptionModel]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProductPriceOptionModel.position",
    )
    images: Mapped[list[ProductImageModel]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProductImageModel.position",
    )


class ProductPriceOptionModel(Base):
    __tablename__ = "product_price_options"

    product_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(128))
    label: Mapped[str | None] = mapped_column(String(250))
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3))
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False)

    product: Mapped[ProductModel] = relationship(back_populates="price_options")


class ProductImageModel(Base):
    __tablename__ = "product_images"

    product_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(500))
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False)

    product: Mapped[ProductModel] = relationship(back_populates="images")


class CategoryModel(Base):
    __tablename__ = "categories"
    __table_args__ = (Index("ix_categories_external_id", "external_id", unique=True),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(128))
    image_url: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
