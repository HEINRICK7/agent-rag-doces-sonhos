"""Exercise the catalog migration upgrade and downgrade operations on SQLite."""

import importlib
import unittest
from unittest.mock import patch

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect


class CatalogMigrationTestCase(unittest.TestCase):
    def test_upgrade_and_downgrade(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        migration = importlib.import_module("migrations.versions.0003_create_catalog")
        expected_tables = {
            "categories",
            "products",
            "product_price_options",
            "product_images",
            "catalog_sync_executions",
            "catalog_sync_errors",
        }

        with engine.begin() as connection:
            operations = Operations(MigrationContext.configure(connection))
            with patch.object(migration, "op", operations):
                migration.upgrade()
                self.assertTrue(expected_tables.issubset(inspect(connection).get_table_names()))
                migration.downgrade()
                self.assertTrue(expected_tables.isdisjoint(inspect(connection).get_table_names()))

        engine.dispose()

    def test_incremental_evidence_upgrade_and_downgrade(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        base = importlib.import_module("migrations.versions.0003_create_catalog")
        migration = importlib.import_module(
            "migrations.versions.0004_incremental_sync_evidence"
        )

        with engine.begin() as connection:
            operations = Operations(MigrationContext.configure(connection))
            with patch.object(base, "op", operations):
                base.upgrade()
            with patch.object(migration, "op", operations):
                migration.upgrade()
                columns = {
                    column["name"] for column in inspect(connection).get_columns("products")
                }
                self.assertIn("source_fingerprint", columns)
                self.assertIn("catalog_sync_changes", inspect(connection).get_table_names())
                migration.downgrade()
                self.assertNotIn(
                    "source_fingerprint",
                    {column["name"] for column in inspect(connection).get_columns("products")},
                )
                self.assertNotIn("catalog_sync_changes", inspect(connection).get_table_names())
            with patch.object(base, "op", operations):
                base.downgrade()

        engine.dispose()
