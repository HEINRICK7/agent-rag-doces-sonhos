"""Tests for product invariants and external update policy."""

import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from app.catalog.domain.entities.product import Product, ProductProtectedField
from app.catalog.domain.entities.product_image import ProductImage
from app.catalog.domain.entities.product_price_option import ProductPriceOption
from app.catalog.domain.exceptions import (
    ExternalProductIdentityMismatchError,
    InvalidCatalogValueError,
)
from app.catalog.domain.services.product_fingerprint import fingerprint_product
from app.catalog.domain.value_objects.money import Money
from app.catalog.domain.value_objects.product_availability import ProductAvailability


class ProductTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 7, 26, 14, 0, tzinfo=UTC)
        self.price = ProductPriceOption(
            external_id="price-1",
            label="1 unidade",
            quantity=Decimal("1"),
            unit="un",
            price=Money(Decimal("10"), None),
            is_default=True,
        )
        self.image = ProductImage(
            source_url="https://cdn.example.com/product.png",
            position=0,
            is_primary=True,
        )

    def product(self, **overrides: object) -> Product:
        values: dict[str, object] = {
            "id": UUID("00000000-0000-0000-0000-000000000001"),
            "external_id": " product-1 ",
            "name": " Bolo   artesanal ",
            "description": " Massa fresca ",
            "category_external_id": "category-1",
            "subcategory_external_id": None,
            "is_active": True,
            "availability": ProductAvailability.AVAILABLE,
            "price_options": (self.price,),
            "images": (self.image,),
            "created_at": self.now,
            "updated_at": self.now,
            "last_synced_at": self.now,
        }
        values.update(overrides)
        return Product(**values)  # type: ignore[arg-type]

    def test_creates_product_with_explicit_invariants(self) -> None:
        product = self.product()

        self.assertEqual(product.external_id, "product-1")
        self.assertEqual(product.name, "Bolo artesanal")
        self.assertEqual(product.availability, ProductAvailability.AVAILABLE)
        self.assertEqual(product.price_options[0].unit, "UN")

    def test_rejects_invalid_identity_text_prices_images_and_state(self) -> None:
        second_primary = replace(self.image, position=1)
        cases = (
            ("product.external_id", {"external_id": " "}),
            ("product.external_id", {"external_id": "product 1"}),
            ("product.name", {"name": " "}),
            ("product.description", {"description": "\n"}),
            ("product.price_options", {"price_options": ()}),
            (
                "product.price_options",
                {"price_options": (replace(self.price, is_default=False),)},
            ),
            ("product.images", {"images": (self.image, second_primary)}),
            (
                "product.availability",
                {
                    "is_active": False,
                    "availability": ProductAvailability.AVAILABLE,
                },
            ),
        )

        for field, overrides in cases:
            with self.subTest(field=field):
                with self.assertRaises(InvalidCatalogValueError) as context:
                    self.product(**overrides)
                self.assertEqual(context.exception.field, field)

    def test_activates_deactivates_and_records_last_sync(self) -> None:
        product = self.product()
        changed_at = self.now + timedelta(hours=1)
        synced_at = changed_at + timedelta(hours=1)

        product.deactivate(changed_at)
        self.assertFalse(product.is_active)
        self.assertEqual(product.availability, ProductAvailability.UNAVAILABLE)
        product.activate(changed_at, ProductAvailability.OUT_OF_STOCK)
        product.record_sync(synced_at, synced_at)

        self.assertTrue(product.is_active)
        self.assertEqual(product.availability, ProductAvailability.OUT_OF_STOCK)
        self.assertEqual(product.last_synced_at, synced_at)
        self.assertEqual(product.source_updated_at, synced_at)

    def test_rejects_activating_with_unavailable_state(self) -> None:
        with self.assertRaises(InvalidCatalogValueError):
            self.product().activate(self.now, ProductAvailability.UNAVAILABLE)

    def test_external_snapshot_respects_protected_local_fields(self) -> None:
        product = self.product()
        product.protect(ProductProtectedField.NAME)
        product.protect(ProductProtectedField.DESCRIPTION)
        product.protect(ProductProtectedField.CATEGORY)
        incoming_price = replace(self.price, price=Money(Decimal("15"), None))
        snapshot = self.product(
            id=UUID("00000000-0000-0000-0000-000000000002"),
            name="Nome externo",
            description="Descrição externa",
            category_external_id="category-2",
            subcategory_external_id="subcategory-2",
            availability=ProductAvailability.OUT_OF_STOCK,
            price_options=(incoming_price,),
            images=(),
        )
        synced_at = self.now + timedelta(hours=3)

        product.apply_external_snapshot(snapshot, synced_at)

        self.assertEqual(product.name, "Bolo artesanal")
        self.assertEqual(product.description, "Massa fresca")
        self.assertEqual(product.category_external_id, "category-1")
        self.assertEqual(product.price_options[0].price.amount, Decimal("15.00"))
        self.assertEqual(product.availability, ProductAvailability.OUT_OF_STOCK)
        self.assertEqual(product.last_synced_at, synced_at)

    def test_unprotected_fields_follow_source_and_protection_can_be_removed(self) -> None:
        product = self.product()
        product.protect(ProductProtectedField.NAME)
        product.unprotect(ProductProtectedField.NAME)
        snapshot = self.product(
            id=UUID("00000000-0000-0000-0000-000000000002"),
            name="Nome externo",
            description="Descrição externa",
            category_external_id="category-2",
        )

        product.apply_external_snapshot(snapshot, self.now)

        self.assertEqual(product.name, "Nome externo")
        self.assertEqual(product.description, "Descrição externa")
        self.assertEqual(product.category_external_id, "category-2")

    def test_rejects_snapshot_from_another_external_product(self) -> None:
        with self.assertRaises(ExternalProductIdentityMismatchError):
            self.product().apply_external_snapshot(
                self.product(external_id="product-2"),
                self.now,
            )

    def test_product_image_and_price_option_validate_their_own_values(self) -> None:
        with self.assertRaises(InvalidCatalogValueError):
            ProductImage("/relative.png", 0, True)
        with self.assertRaises(InvalidCatalogValueError):
            ProductImage("https://cdn.example.com/a.png", -1, True)
        with self.assertRaises(InvalidCatalogValueError):
            replace(self.price, quantity=Decimal("0"))
        with self.assertRaises(InvalidCatalogValueError):
            replace(self.price, unit=" ")

    def test_fingerprint_is_stable_and_tracks_source_changes_only(self) -> None:
        product = self.product()
        same_snapshot = self.product(
            id=UUID("00000000-0000-0000-0000-000000000099"),
            created_at=self.now + timedelta(days=1),
            updated_at=self.now + timedelta(days=1),
            last_synced_at=self.now + timedelta(days=1),
        )

        self.assertEqual(fingerprint_product(product), fingerprint_product(same_snapshot))
        self.assertNotEqual(
            fingerprint_product(product),
            fingerprint_product(
                self.product(price_options=(replace(self.price, price=Money(Decimal("11"), None)),))
            ),
        )
