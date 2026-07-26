"""Tests for the deterministic internal product normalizer."""

import unittest
from dataclasses import replace
from decimal import Decimal

from app.ingestion.application.dto.product_input import (
    PriceOptionInput,
    ProductImageInput,
    ProductImportInput,
)
from app.ingestion.application.exceptions import ProductNormalizationError
from app.ingestion.application.usecases.normalize_product import (
    DESCRIPTION_FALLBACK,
    NormalizeProductUseCase,
)


def product_input(**overrides: object) -> ProductImportInput:
    values: dict[str, object] = {
        "external_id": " product-1 ",
        "name": "  Bolo   de \n chocolate  ",
        "description": "  Massa \t artesanal. ",
        "category_external_id": " category-1 ",
        "subcategory_external_id": " ",
        "is_active": True,
        "availability": "unavailable",
        "currency": " brl ",
        "stock_quantity": Decimal("3.00"),
        "price_options": (
            PriceOptionInput(
                external_id=" price-1 ",
                label="  Caixa   pequena ",
                quantity=Decimal("1.00"),
                unit=" un ",
                amount=Decimal("10.125"),
                is_default=True,
            ),
        ),
        "images": (
            ProductImageInput(
                source_url=" HTTPS://CDN.EXAMPLE.COM/bolo.png#preview ",
                is_primary=False,
            ),
            ProductImageInput(
                source_url="https://cdn.example.com/bolo.png",
                is_primary=True,
            ),
        ),
        "source_created_at": None,
        "source_updated_at": None,
        "ignored_fields": ("futureB", "futureA", "futureB"),
    }
    values.update(overrides)
    return ProductImportInput(**values)  # type: ignore[arg-type]


class NormalizeProductUseCaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.normalizer = NormalizeProductUseCase()

    def test_normalizes_every_supported_product_field(self) -> None:
        normalized = self.normalizer.execute(product_input())

        self.assertEqual(normalized.external_id, "product-1")
        self.assertEqual(normalized.name, "Bolo de chocolate")
        self.assertEqual(normalized.description, "Massa artesanal.")
        self.assertEqual(normalized.category_external_id, "category-1")
        self.assertIsNone(normalized.subcategory_external_id)
        self.assertEqual(normalized.currency, "BRL")
        self.assertEqual(normalized.stock_quantity, Decimal("3"))
        self.assertEqual(normalized.availability, "available")
        self.assertEqual(normalized.price_options[0].external_id, "price-1")
        self.assertEqual(normalized.price_options[0].label, "Caixa pequena")
        self.assertEqual(normalized.price_options[0].unit, "UN")
        self.assertEqual(normalized.price_options[0].quantity, Decimal("1"))
        self.assertEqual(normalized.price_options[0].amount, Decimal("10.13"))
        self.assertEqual(
            normalized.images,
            (
                ProductImageInput(
                    source_url="https://cdn.example.com/bolo.png",
                    is_primary=True,
                ),
            ),
        )
        self.assertEqual(normalized.ignored_fields, ("futureA", "futureB"))

    def test_uses_explicit_description_fallback_and_does_not_invent_currency(self) -> None:
        normalized = self.normalizer.execute(
            product_input(description=" \n ", currency=None, stock_quantity=None)
        )

        self.assertEqual(normalized.description, DESCRIPTION_FALLBACK)
        self.assertIsNone(normalized.currency)
        self.assertEqual(normalized.availability, "unknown")

    def test_selects_exactly_one_default_price_deterministically(self) -> None:
        first = replace(product_input().price_options[0], is_default=False)
        second = replace(
            first,
            external_id="price-2",
            amount=Decimal("20"),
            is_default=False,
        )
        without_default = self.normalizer.execute(product_input(price_options=(first, second)))
        with_multiple_defaults = self.normalizer.execute(
            product_input(
                price_options=(
                    replace(first, is_default=True),
                    replace(second, is_default=True),
                )
            )
        )

        self.assertEqual(
            tuple(price.is_default for price in without_default.price_options),
            (True, False),
        )
        self.assertEqual(
            tuple(price.is_default for price in with_multiple_defaults.price_options),
            (True, False),
        )

    def test_derives_availability_from_activity_and_stock(self) -> None:
        cases = (
            (False, Decimal("5"), "unavailable"),
            (True, Decimal("0"), "out_of_stock"),
            (True, Decimal("5"), "available"),
            (True, None, "unknown"),
        )

        for is_active, stock, expected in cases:
            with self.subTest(is_active=is_active, stock=stock):
                normalized = self.normalizer.execute(
                    product_input(is_active=is_active, stock_quantity=stock)
                )
                self.assertEqual(normalized.availability, expected)

    def test_rejects_missing_or_malformed_identifiers_and_name(self) -> None:
        cases = (
            ("external_id", product_input(external_id=" ")),
            ("external_id", product_input(external_id="product 1")),
            ("name", product_input(name="\n\t")),
            ("category_external_id", product_input(category_external_id="category 1")),
        )

        for field, product in cases:
            with self.subTest(field=field):
                with self.assertRaises(ProductNormalizationError) as context:
                    self.normalizer.execute(product)
                self.assertEqual(context.exception.field, field)

    def test_rejects_invalid_price_contracts(self) -> None:
        valid = product_input().price_options[0]
        cases = (
            ((), "price_options"),
            ((replace(valid, amount=Decimal("-0.01")),), "price_options[0]"),
            ((replace(valid, amount=Decimal("NaN")),), "price_options[0]"),
            ((replace(valid, quantity=Decimal("0")),), "price_options[0]"),
            ((replace(valid, unit="  "),), "price_options[0]"),
        )

        for prices, field in cases:
            with self.subTest(prices=prices):
                with self.assertRaises(ProductNormalizationError) as context:
                    self.normalizer.execute(product_input(price_options=prices))
                self.assertEqual(context.exception.field, field)

    def test_rejects_invalid_stock_currency_and_image_url(self) -> None:
        cases = (
            ("stock_quantity", product_input(stock_quantity=Decimal("-1"))),
            ("stock_quantity", product_input(stock_quantity=Decimal("Infinity"))),
            ("currency", product_input(currency="REAL")),
            (
                "images[0].source_url",
                product_input(images=(ProductImageInput("/bolo.png", True),)),
            ),
            (
                "images[0].source_url",
                product_input(images=(ProductImageInput("https://[invalid", True),)),
            ),
        )

        for field, product in cases:
            with self.subTest(field=field):
                with self.assertRaises(ProductNormalizationError) as context:
                    self.normalizer.execute(product)
                self.assertEqual(context.exception.field, field)
