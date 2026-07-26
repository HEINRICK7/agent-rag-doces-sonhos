"""Infrastructure readiness unit tests."""

import unittest

from app.shared.infrastructure.observability.health import InfrastructureHealth


class FakeConnection:
    def __init__(self, has_vector: bool) -> None:
        self.has_vector = has_vector

    async def execute(self, _statement: object) -> None:
        return None

    async def scalar(self, _statement: object) -> bool:
        return self.has_vector


class FakeConnectionContext:
    def __init__(self, has_vector: bool, fails: bool = False) -> None:
        self.connection = FakeConnection(has_vector)
        self.fails = fails

    async def __aenter__(self) -> FakeConnection:
        if self.fails:
            raise ConnectionError
        return self.connection

    async def __aexit__(self, *_args: object) -> None:
        return None


class FakeEngine:
    def __init__(self, has_vector: bool = True, fails: bool = False) -> None:
        self.has_vector = has_vector
        self.fails = fails

    def connect(self) -> FakeConnectionContext:
        return FakeConnectionContext(self.has_vector, self.fails)


class FakeRedis:
    def __init__(self, healthy: bool = True, fails: bool = False) -> None:
        self.healthy = healthy
        self.fails = fails
        self.closed = False

    async def ping(self) -> bool:
        if self.fails:
            raise ConnectionError
        return self.healthy

    async def aclose(self) -> None:
        self.closed = True


class FakeMinio:
    def __init__(self, bucket_exists: bool = True, fails: bool = False) -> None:
        self.exists = bucket_exists
        self.fails = fails

    def bucket_exists(self, _bucket: str) -> bool:
        if self.fails:
            raise ConnectionError
        return self.exists


def health_service(
    *,
    has_vector: bool = True,
    database_fails: bool = False,
    redis_healthy: bool = True,
    redis_fails: bool = False,
    bucket_exists: bool = True,
    minio_fails: bool = False,
) -> tuple[InfrastructureHealth, FakeRedis]:
    redis = FakeRedis(redis_healthy, redis_fails)
    health = InfrastructureHealth(
        FakeEngine(has_vector, database_fails),  # type: ignore[arg-type]
        redis,  # type: ignore[arg-type]
        FakeMinio(bucket_exists, minio_fails),  # type: ignore[arg-type]
        "products",
    )
    return health, redis


class InfrastructureHealthTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_reports_every_component_as_ready(self) -> None:
        health, _ = health_service()

        report = await health.check()

        self.assertEqual(report["status"], "ready")
        self.assertTrue(
            all(component["status"] == "ok" for component in report["components"].values())
        )

    async def test_reports_missing_pgvector_and_bucket(self) -> None:
        health, _ = health_service(has_vector=False, bucket_exists=False)

        report = await health.check()

        self.assertEqual(report["status"], "not_ready")
        self.assertEqual(report["components"]["pgvector"]["detail"], "extensão não instalada")
        self.assertEqual(
            report["components"]["minio"]["detail"],
            "bucket products não encontrado",
        )

    async def test_hides_connection_errors_from_readiness_response(self) -> None:
        health, _ = health_service(
            database_fails=True,
            redis_fails=True,
            minio_fails=True,
        )

        report = await health.check()

        self.assertEqual(report["status"], "not_ready")
        self.assertTrue(
            all(component["status"] == "error" for component in report["components"].values())
        )

    async def test_closes_redis_client(self) -> None:
        health, redis = health_service()

        await health.close()

        self.assertTrue(redis.closed)
