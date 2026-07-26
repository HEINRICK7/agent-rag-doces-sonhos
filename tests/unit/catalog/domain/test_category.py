"""Tests for the category entity."""

import unittest
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.catalog.domain.entities.category import Category
from app.catalog.domain.exceptions import InvalidCatalogValueError


class CategoryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 7, 26, 14, 0, tzinfo=UTC)

    def category(self, **overrides: object) -> Category:
        values: dict[str, object] = {
            "id": UUID("00000000-0000-0000-0000-000000000010"),
            "external_id": " category-1 ",
            "name": " Doces   artesanais ",
            "is_active": True,
            "created_at": self.now,
            "updated_at": self.now,
            "last_synced_at": self.now,
            "position": 0,
        }
        values.update(overrides)
        return Category(**values)  # type: ignore[arg-type]

    def test_normalizes_identity_and_name(self) -> None:
        category = self.category()

        self.assertEqual(category.external_id, "category-1")
        self.assertEqual(category.name, "Doces artesanais")

    def test_activates_deactivates_and_records_sync(self) -> None:
        category = self.category()
        changed_at = self.now + timedelta(hours=1)
        synced_at = changed_at + timedelta(hours=1)

        category.deactivate(changed_at)
        self.assertFalse(category.is_active)
        category.activate(synced_at)
        category.record_sync(synced_at, synced_at)

        self.assertTrue(category.is_active)
        self.assertEqual(category.last_synced_at, synced_at)
        self.assertEqual(category.source_updated_at, synced_at)

    def test_rejects_missing_fields_and_negative_position(self) -> None:
        cases = (
            ("category.external_id", {"external_id": " "}),
            ("category.name", {"name": "\n"}),
            ("category.position", {"position": -1}),
        )

        for field, overrides in cases:
            with self.subTest(field=field):
                with self.assertRaises(InvalidCatalogValueError) as context:
                    self.category(**overrides)
                self.assertEqual(context.exception.field, field)
