"""Concrete mapped-product pipeline assembled from application stages."""

from collections.abc import Mapping

from app.ingestion.application.dto.product_input import ProductImportInput
from app.ingestion.application.ports.catalog_item_processor import CatalogItemProcessor
from app.ingestion.application.usecases.normalize_product import NormalizeProductUseCase
from app.ingestion.infrastructure.external_api.mapper import map_external_product


class ProductPipelineProcessor(CatalogItemProcessor):
    """Map and normalize one product before future persistence and indexing stages."""

    def __init__(self, normalizer: NormalizeProductUseCase) -> None:
        self._normalizer = normalizer

    async def process(
        self,
        payload: Mapping[str, object],
        correlation_id: str,
    ) -> ProductImportInput:
        del correlation_id
        mapped = map_external_product(payload)
        return self._normalizer.execute(mapped)
