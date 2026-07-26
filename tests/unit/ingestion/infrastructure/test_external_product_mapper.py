"""Tests for the Doces Sonhos external contract mapper."""

import unittest
from decimal import Decimal

from app.ingestion.application.exceptions import ExternalProductMappingError
from app.ingestion.infrastructure.external_api.mapper import (
    map_external_category,
    map_external_product,
    map_external_subcategory,
)


def product_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "72f27e19-7e53-4e3c-ad70-7f686761e88c",
        "name": "Crostini G",
        "description": "Deliciosos crostini...",
        "image": "https://storage.example/products/crostini.png",
        "categoryId": "44e0e6d1-65ad-4eb0-ade4-99c12fd03798",
        "subcategoryId": "b35f0bcd-4418-4ef1-9f58-6e6fd8943477",
        "isActive": True,
        "priceOptions": [
            {
                "id": "f90842c2-1b8c-4f08-8f24-9f2df8b8da4a",
                "label": "1 unid.",
                "quantity": 1,
                "unit": "UN",
                "price": 89,
                "isDefault": True,
            }
        ],
        "createdAt": "2026-07-20T12:00:00Z",
        "updatedAt": "2026-07-24T15:30:00Z",
    }
    payload.update(overrides)
    return payload


class ExternalProductMapperTestCase(unittest.TestCase):
    def test_maps_verified_product_contract_without_float_prices(self) -> None:
        mapped = map_external_product(product_payload())

        self.assertEqual(mapped.external_id, "72f27e19-7e53-4e3c-ad70-7f686761e88c")
        self.assertEqual(mapped.price_options[0].amount, Decimal("89"))
        self.assertEqual(mapped.price_options[0].quantity, Decimal("1"))
        self.assertEqual(
            mapped.images[0].source_url, "https://storage.example/products/crostini.png"
        )
        self.assertEqual(mapped.availability, "unknown")
        self.assertEqual(mapped.source_updated_at.isoformat(), "2026-07-24T15:30:00+00:00")

    def test_maps_optional_stock_currency_and_unknown_fields_explicitly(self) -> None:
        mapped = map_external_product(
            product_payload(
                currency="brl",
                stockQuantity=0,
                futureField="preserved-as-evidence",
            )
        )

        self.assertEqual(mapped.currency, "BRL")
        self.assertEqual(mapped.availability, "out_of_stock")
        self.assertEqual(mapped.ignored_fields, ("futureField",))

    def test_maps_inactive_product_and_missing_image(self) -> None:
        mapped = map_external_product(product_payload(isActive=False, image=None, description=None))

        self.assertEqual(mapped.availability, "unavailable")
        self.assertEqual(mapped.images, ())
        self.assertIsNone(mapped.description)

    def test_rejects_missing_required_product_data(self) -> None:
        invalid = product_payload()
        invalid.pop("priceOptions")

        with self.assertRaises(ExternalProductMappingError) as context:
            map_external_product(invalid)

        self.assertTrue(context.exception.details)

    def test_maps_category_and_subcategory_contracts(self) -> None:
        category = map_external_category(
            {
                "id": "category-1",
                "name": "Natal",
                "icon": "Snowflake",
                "image": None,
                "isActive": True,
                "position": 0,
                "createdAt": "2026-07-20T10:00:00Z",
                "updatedAt": "2026-07-24T15:30:00Z",
            }
        )
        subcategory = map_external_subcategory(
            {
                "id": "subcategory-1",
                "name": "Entradas",
                "categoryId": "category-1",
                "createdAt": "2026-07-20T11:00:00Z",
                "updatedAt": "2026-07-24T16:00:00Z",
            }
        )

        self.assertEqual(category.position, 0)
        self.assertTrue(category.is_active)
        self.assertEqual(category.source_created_at.isoformat(), "2026-07-20T10:00:00+00:00")
        self.assertEqual(subcategory.category_external_id, category.external_id)
        self.assertEqual(
            subcategory.source_created_at.isoformat(),
            "2026-07-20T11:00:00+00:00",
        )
