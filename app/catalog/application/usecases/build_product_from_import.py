"""Build the catalog aggregate from a normalized ingestion contract."""

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.catalog.domain.entities.product import Product
from app.catalog.domain.entities.product_image import ProductImage
from app.catalog.domain.entities.product_price_option import ProductPriceOption
from app.catalog.domain.value_objects.money import Money
from app.catalog.domain.value_objects.product_availability import ProductAvailability
from app.ingestion.application.dto.product_input import ProductImportInput

Clock = Callable[[], datetime]
IdFactory = Callable[[], UUID]


class BuildProductFromImportUseCase:
    """Translate the normalized ingestion DTO into a valid catalog aggregate."""

    def __init__(
        self,
        *,
        clock: Clock | None = None,
        id_factory: IdFactory | None = None,
    ) -> None:
        self._clock = clock or _utc_now
        self._id_factory = id_factory or uuid4

    def execute(self, product: ProductImportInput) -> Product:
        synchronized_at = self._clock()
        return Product(
            id=self._id_factory(),
            external_id=product.external_id,
            name=product.name,
            description=product.description or "",
            category_external_id=product.category_external_id,
            subcategory_external_id=product.subcategory_external_id,
            is_active=product.is_active,
            availability=ProductAvailability(product.availability),
            price_options=tuple(
                ProductPriceOption(
                    external_id=option.external_id,
                    label=option.label,
                    quantity=option.quantity,
                    unit=option.unit,
                    price=Money(option.amount, product.currency),
                    is_default=option.is_default,
                )
                for option in product.price_options
            ),
            images=tuple(
                ProductImage(
                    source_url=image.source_url,
                    position=index,
                    is_primary=image.is_primary,
                )
                for index, image in enumerate(product.images)
            ),
            created_at=synchronized_at,
            updated_at=synchronized_at,
            last_synced_at=synchronized_at,
            source_created_at=product.source_created_at,
            source_updated_at=product.source_updated_at,
        )


def _utc_now() -> datetime:
    return datetime.now(UTC)
