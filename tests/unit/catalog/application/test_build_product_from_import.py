"""Tests for converting normalized ingestion data into the catalog aggregate."""

import unittest
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.catalog.application.usecases.build_product_from_import import (
    BuildProductFromImportUseCase,
)
from app.catalog.domain.value_objects.product_availability import ProductAvailability
from app.ingestion.application.dto.product_input import (
    PriceOptionInput,
    ProductImageInput,
    ProductImportInput,
)


class BuildProductFromImportUseCaseTestCase(unittest.TestCase):
    def test_builds_product_with_local_identity_and_source_timestamps(self) -> None:
        synchronized_at = datetime(2026, 7, 26, 15, 0, tzinfo=UTC)
        internal_id = UUID("00000000-0000-0000-0000-000000000001")
        source_updated_at = datetime(2026, 7, 25, 20, 0, tzinfo=UTC)
        use_case = BuildProductFromImportUseCase(
            clock=lambda: synchronized_at,
            id_factory=lambda: internal_id,
        )
        input_data = ProductImportInput(
            external_id="product-1",
            name="Bolo artesanal",
            description="Descrição",
            category_external_id="category-1",
            subcategory_external_id=None,
            is_active=True,
            availability="available",
            currency=None,
            stock_quantity=None,
            price_options=(
                PriceOptionInput(
                    external_id="price-1",
                    label="1 unidade",
                    quantity=Decimal("1"),
                    unit="UN",
                    amount=Decimal("10.00"),
                    is_default=True,
                ),
            ),
            images=(
                ProductImageInput(
                    source_url="https://cdn.example.com/product.png",
                    is_primary=True,
                ),
            ),
            source_created_at=None,
            source_updated_at=source_updated_at,
            ignored_fields=(),
        )

        product = use_case.execute(input_data)

        self.assertEqual(product.id, internal_id)
        self.assertEqual(product.external_id, "product-1")
        self.assertEqual(product.availability, ProductAvailability.AVAILABLE)
        self.assertEqual(product.price_options[0].price.amount, Decimal("10.00"))
        self.assertIsNone(product.price_options[0].price.currency)
        self.assertEqual(product.images[0].position, 0)
        self.assertEqual(product.last_synced_at, synchronized_at)
        self.assertEqual(product.source_updated_at, source_updated_at)
