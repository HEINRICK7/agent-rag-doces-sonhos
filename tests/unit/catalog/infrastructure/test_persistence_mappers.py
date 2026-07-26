"""Tests for catalog persistence mappers not exercised by the product repository."""

import unittest
from datetime import UTC, datetime
from uuid import UUID

from app.catalog.domain.entities.category import Category
from app.catalog.infrastructure.persistence.mappers import (
    category_to_domain,
    category_to_model,
)


class CatalogPersistenceMappersTestCase(unittest.TestCase):
    def test_category_round_trip(self) -> None:
        now = datetime(2026, 7, 26, 16, 0, tzinfo=UTC)
        category = Category(
            id=UUID("00000000-0000-0000-0000-000000000010"),
            external_id="category-1",
            name="Doces",
            icon="cake",
            image_url="https://cdn.example.com/category.png",
            position=1,
            is_active=True,
            created_at=now,
            updated_at=now,
            last_synced_at=now,
            source_created_at=now,
            source_updated_at=now,
        )

        restored = category_to_domain(category_to_model(category))

        self.assertEqual(restored.id, category.id)
        self.assertEqual(restored.external_id, category.external_id)
        self.assertEqual(restored.name, category.name)
        self.assertEqual(restored.last_synced_at, now)
