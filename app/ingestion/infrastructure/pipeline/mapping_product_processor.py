"""Current product pipeline stage: validate and map the external contract."""

from collections.abc import Mapping

from app.ingestion.application.dto.product_input import ProductImportInput
from app.ingestion.application.ports.catalog_item_processor import CatalogItemProcessor
from app.ingestion.infrastructure.external_api.mapper import map_external_product


class MappingProductProcessor(CatalogItemProcessor):
    """Map external products; later modules can decorate this with persistence and indexing."""

    async def process(
        self,
        payload: Mapping[str, object],
        correlation_id: str,
    ) -> ProductImportInput:
        del correlation_id
        return map_external_product(payload)
