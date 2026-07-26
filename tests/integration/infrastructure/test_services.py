"""Integration tests for the local Docker infrastructure."""

import os
import unittest

from app.shared.infrastructure.database.session import create_engine
from app.shared.infrastructure.observability.health import InfrastructureHealth
from minio import Minio
from redis.asyncio import Redis


@unittest.skipUnless(
    os.getenv("RUN_INFRASTRUCTURE_TESTS") == "1",
    "requires the local Docker infrastructure",
)
class InfrastructureServicesTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_engine(
            os.getenv(
                "INFRA_DATABASE_URL",
                "postgresql+asyncpg://postgres:postgres@localhost:5433/app",
            )
        )
        self.redis = Redis.from_url(
            os.getenv("INFRA_REDIS_URL", "redis://localhost:6380/0"),
            decode_responses=True,
        )
        self.health = InfrastructureHealth(
            self.engine,
            self.redis,
            Minio(
                os.getenv("INFRA_MINIO_ENDPOINT", "localhost:9010"),
                access_key=os.getenv("MINIO_ACCESS_KEY", "minio"),
                secret_key=os.getenv("MINIO_SECRET_KEY", "minio-secret"),
                secure=False,
            ),
            os.getenv("MINIO_BUCKET", "products"),
        )

    async def asyncTearDown(self) -> None:
        await self.health.close()
        await self.engine.dispose()

    async def test_all_required_services_are_ready(self) -> None:
        report = await self.health.check()

        self.assertEqual(report["status"], "ready")
        self.assertEqual(
            {name: component["status"] for name, component in report["components"].items()},
            {
                "database": "ok",
                "pgvector": "ok",
                "redis": "ok",
                "minio": "ok",
            },
        )
