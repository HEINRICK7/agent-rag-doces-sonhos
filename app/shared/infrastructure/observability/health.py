"""Readiness checks for external infrastructure dependencies."""

import asyncio
from typing import Literal, TypedDict

from minio import Minio
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


class ComponentHealth(TypedDict):
    status: Literal["ok", "error"]
    detail: str


class ReadinessReport(TypedDict):
    status: Literal["ready", "not_ready"]
    components: dict[str, ComponentHealth]


class InfrastructureHealth:
    """Check infrastructure without exposing credentials or internal exceptions."""

    def __init__(
        self,
        engine: AsyncEngine,
        redis: Redis,
        minio: Minio,
        minio_bucket: str,
    ) -> None:
        self._engine = engine
        self._redis = redis
        self._minio = minio
        self._minio_bucket = minio_bucket

    async def _database(self) -> tuple[ComponentHealth, ComponentHealth]:
        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
                has_vector = bool(
                    await connection.scalar(
                        text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
                    )
                )
            database: ComponentHealth = {"status": "ok", "detail": "conexão disponível"}
            pgvector: ComponentHealth = {
                "status": "ok" if has_vector else "error",
                "detail": "extensão disponível" if has_vector else "extensão não instalada",
            }
            return database, pgvector
        except Exception:
            error: ComponentHealth = {"status": "error", "detail": "conexão indisponível"}
            return error, {"status": "error", "detail": "não foi possível verificar"}

    async def _redis_check(self) -> ComponentHealth:
        try:
            healthy = bool(await self._redis.ping())
            return {
                "status": "ok" if healthy else "error",
                "detail": "conexão disponível" if healthy else "PING sem resposta",
            }
        except Exception:
            return {"status": "error", "detail": "conexão indisponível"}

    async def _minio_check(self) -> ComponentHealth:
        try:
            exists = await asyncio.to_thread(self._minio.bucket_exists, self._minio_bucket)
            return {
                "status": "ok" if exists else "error",
                "detail": (
                    f"bucket {self._minio_bucket} disponível"
                    if exists
                    else f"bucket {self._minio_bucket} não encontrado"
                ),
            }
        except Exception:
            return {"status": "error", "detail": "conexão indisponível"}

    async def check(self) -> ReadinessReport:
        """Return a deterministic readiness report for every required service."""

        database_result, redis_result, minio_result = await asyncio.gather(
            self._database(),
            self._redis_check(),
            self._minio_check(),
        )
        database, pgvector = database_result
        components = {
            "database": database,
            "pgvector": pgvector,
            "redis": redis_result,
            "minio": minio_result,
        }
        ready = all(component["status"] == "ok" for component in components.values())
        return {"status": "ready" if ready else "not_ready", "components": components}

    async def close(self) -> None:
        """Close clients that own network resources."""

        await self._redis.aclose()
