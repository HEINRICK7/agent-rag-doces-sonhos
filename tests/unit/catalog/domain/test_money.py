"""Tests for catalog money."""

import unittest
from decimal import Decimal

from app.catalog.domain.exceptions import InvalidCatalogValueError
from app.catalog.domain.value_objects.money import Money


class MoneyTestCase(unittest.TestCase):
    def test_normalizes_amount_and_known_currency(self) -> None:
        money = Money(Decimal("10.125"), " brl ")

        self.assertEqual(money.amount, Decimal("10.13"))
        self.assertEqual(money.currency, "BRL")
        self.assertTrue(money.has_known_currency)

    def test_preserves_unknown_currency_explicitly(self) -> None:
        money = Money(Decimal("10"), None)

        self.assertEqual(money.amount, Decimal("10.00"))
        self.assertIsNone(money.currency)
        self.assertFalse(money.has_known_currency)

    def test_rejects_negative_non_finite_and_invalid_currency(self) -> None:
        cases = (
            (Decimal("-0.01"), None, "money.amount"),
            (Decimal("NaN"), None, "money.amount"),
            (Decimal("Infinity"), None, "money.amount"),
            (Decimal("10"), "REAL", "money.currency"),
        )

        for amount, currency, field in cases:
            with self.subTest(amount=amount, currency=currency):
                with self.assertRaises(InvalidCatalogValueError) as context:
                    Money(amount, currency)
                self.assertEqual(context.exception.field, field)
