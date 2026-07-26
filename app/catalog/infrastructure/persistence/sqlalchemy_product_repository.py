"""Transactional SQLAlchemy implementation of the product repository."""

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.catalog.application.exceptions import ProductPersistenceError
from app.catalog.domain.entities.product import Product
from app.catalog.domain.entities.product_sync import ProductChangeKind, ProductUpsertResult
from app.catalog.domain.repositories.product_repository import ProductRepository
from app.catalog.domain.services.product_fingerprint import fingerprint_product
from app.catalog.infrastructure.persistence.mappers import (
    product_to_domain,
    product_to_model,
    update_product_model,
)
from app.catalog.infrastructure.persistence.models import (
    ProductModel,
)


class SqlAlchemyProductRepository(ProductRepository):
    """Upsert complete product aggregates inside one database transaction."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def upsert(self, product: Product) -> Product:
        return (await self.upsert_incremental(product)).product

    async def upsert_incremental(self, product: Product) -> ProductUpsertResult:
        incoming_fingerprint = fingerprint_product(product)
        try:
            async with self._session_factory() as session, session.begin():
                model = await self._find_by_external_id(session, product.external_id)
                if model is None:
                    product.source_fingerprint = incoming_fingerprint
                    session.add(product_to_model(product))
                    await session.flush()
                    return ProductUpsertResult(
                        product=product,
                        change=ProductChangeKind.CREATED,
                        previous_fingerprint=None,
                        current_fingerprint=incoming_fingerprint,
                    )

                previous_fingerprint = model.source_fingerprint
                if previous_fingerprint == incoming_fingerprint:
                    current = product_to_domain(model)
                    current.last_synced_at = product.last_synced_at
                    model.last_synced_at = product.last_synced_at
                    await session.flush()
                    return ProductUpsertResult(
                        product=current,
                        change=ProductChangeKind.UNCHANGED,
                        previous_fingerprint=previous_fingerprint,
                        current_fingerprint=incoming_fingerprint,
                    )

                current = product_to_domain(model)
                current.apply_external_snapshot(product, product.last_synced_at)
                current.source_fingerprint = incoming_fingerprint
                update_product_model(model, current)
                await session.flush()
                return ProductUpsertResult(
                    product=current,
                    change=ProductChangeKind.UPDATED,
                    previous_fingerprint=previous_fingerprint,
                    current_fingerprint=incoming_fingerprint,
                )
        except IntegrityError as error:
            raise ProductPersistenceError(product.external_id) from error

    async def get_by_id(self, product_id: UUID) -> Product | None:
        async with self._session_factory() as session:
            result = await session.execute(
                self._with_relations().where(ProductModel.id == product_id)
            )
            model = result.scalar_one_or_none()
            return product_to_domain(model) if model is not None else None

    async def get_by_external_id(self, external_id: str) -> Product | None:
        async with self._session_factory() as session:
            model = await self._find_by_external_id(session, external_id)
            return product_to_domain(model) if model is not None else None

    async def list(self, limit: int, offset: int) -> list[Product]:
        async with self._session_factory() as session:
            result = await session.execute(
                self._with_relations()
                .order_by(ProductModel.created_at, ProductModel.id)
                .limit(limit)
                .offset(offset)
            )
            return [product_to_domain(model) for model in result.scalars().unique().all()]

    async def _find_by_external_id(
        self,
        session: AsyncSession,
        external_id: str,
    ) -> ProductModel | None:
        result = await session.execute(
            self._with_relations().where(ProductModel.external_id == external_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _with_relations() -> Select[tuple[ProductModel]]:
        return select(ProductModel).options(
            selectinload(ProductModel.price_options),
            selectinload(ProductModel.images),
        )
