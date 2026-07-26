"""Concrete mapped-product pipeline assembled from application stages."""

from collections.abc import Mapping

from app.catalog.application.usecases.build_product_from_import import (
    BuildProductFromImportUseCase,
)
from app.catalog.domain.entities.product_sync import ProductUpsertResult
from app.catalog.domain.repositories.product_repository import ProductRepository
from app.ingestion.application.ports.catalog_item_processor import CatalogItemProcessor
from app.ingestion.application.usecases.normalize_product import NormalizeProductUseCase
from app.ingestion.infrastructure.external_api.mapper import map_external_product


class ProductPipelineProcessor(CatalogItemProcessor):
    """Map and normalize one product before future persistence and indexing stages."""

    def __init__(
        self,
        normalizer: NormalizeProductUseCase,
        product_builder: BuildProductFromImportUseCase,
        products: ProductRepository,
    ) -> None:
        self._normalizer = normalizer
        self._product_builder = product_builder
        self._products = products

    async def process(
        self,
        payload: Mapping[str, object],
        correlation_id: str,
    ) -> ProductUpsertResult:
        del correlation_id
        mapped = map_external_product(payload)
        normalized = self._normalizer.execute(mapped)
        product = self._product_builder.execute(normalized)
        return await self._products.upsert_incremental(product)
