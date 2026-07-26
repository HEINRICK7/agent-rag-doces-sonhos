"""Configuration tests."""

import unittest

from app.shared.configuration.settings import Settings
from pydantic import ValidationError as PydanticValidationError


class SettingsTestCase(unittest.TestCase):
    def test_has_safe_development_defaults(self) -> None:
        settings = Settings(_env_file=None)

        self.assertEqual(settings.api_prefix, "/api/v1")
        self.assertEqual(settings.app_env, "development")

    def test_parses_comma_separated_cors_origins(self) -> None:
        settings = Settings(_env_file=None, cors_origins="http://a,http://b")

        self.assertEqual(settings.cors_origins, ["http://a", "http://b"])

    def test_rejects_invalid_environment_and_database_url(self) -> None:
        with self.assertRaises(PydanticValidationError):
            Settings(_env_file=None, app_env="invalid")  # type: ignore[arg-type]
        with self.assertRaises(PydanticValidationError):
            Settings(_env_file=None, database_url="not-a-url")
        with self.assertRaises(PydanticValidationError):
            Settings(_env_file=None, redis_url="not-a-url")

    def test_requires_minio_connection_values(self) -> None:
        with self.assertRaises(PydanticValidationError):
            Settings(_env_file=None, minio_endpoint="")

    def test_validates_external_api_settings_without_requiring_credentials(self) -> None:
        settings = Settings(_env_file=None, external_api_base_url="")

        self.assertIsNone(settings.external_api_base_url)
        self.assertEqual(settings.external_api_pagination_mode, "none")
        with self.assertRaises(PydanticValidationError):
            Settings(_env_file=None, external_api_base_url="catalog.example.test")
        with self.assertRaises(PydanticValidationError):
            Settings(_env_file=None, external_api_page_size=0)

    def test_rejects_debug_and_docs_in_production(self) -> None:
        with self.assertRaises(PydanticValidationError):
            Settings(_env_file=None, app_env="production", app_debug=True)
        with self.assertRaises(PydanticValidationError):
            Settings(_env_file=None, app_env="production", app_debug=False, docs_enabled=True)
