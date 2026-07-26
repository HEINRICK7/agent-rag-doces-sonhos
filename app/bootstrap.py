"""Composition root for the application."""

import punq  # type: ignore[import-untyped]
from minio import Minio
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.ingestion.application.ports.catalog_item_processor import CatalogItemProcessor
from app.ingestion.application.ports.catalog_sync_repository import (
    CatalogSyncExecutionRepository,
)
from app.ingestion.application.ports.product_source import ProductSource
from app.ingestion.application.usecases.normalize_product import NormalizeProductUseCase
from app.ingestion.application.usecases.start_catalog_sync import StartCatalogSyncUseCase
from app.ingestion.infrastructure.external_api.product_api_client import ProductApiClient
from app.ingestion.infrastructure.persistence.in_memory_catalog_sync_repository import (
    InMemoryCatalogSyncExecutionRepository,
)
from app.ingestion.infrastructure.pipeline.product_pipeline_processor import (
    ProductPipelineProcessor,
)
from app.shared.configuration.settings import Settings
from app.shared.infrastructure.database.session import create_engine, create_session_factory
from app.shared.infrastructure.observability.health import InfrastructureHealth
from app.users.application.usecases.create_user import CreateUserUseCase
from app.users.application.usecases.deactivate_user import DeactivateUserUseCase
from app.users.application.usecases.get_user import GetUserUseCase
from app.users.application.usecases.list_users import ListUsersUseCase
from app.users.application.usecases.update_user_name import UpdateUserNameUseCase
from app.users.domain.repositories.user_repository import UserRepository
from app.users.infrastructure.persistence.sqlalchemy_user_repository import SqlAlchemyUserRepository


def build_container(
    settings: Settings,
) -> tuple[punq.Container, AsyncEngine, InfrastructureHealth, ProductApiClient]:
    """Build all infrastructure and application dependencies in one place."""

    engine = create_engine(settings.database_url)
    session_factory: async_sessionmaker[AsyncSession] = create_session_factory(engine)
    repository = SqlAlchemyUserRepository(session_factory)
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    minio = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )
    infrastructure_health = InfrastructureHealth(engine, redis, minio, settings.minio_bucket)
    product_source = ProductApiClient(settings)
    normalize_product = NormalizeProductUseCase()
    catalog_item_processor = ProductPipelineProcessor(normalize_product)
    catalog_sync_executions = InMemoryCatalogSyncExecutionRepository()
    start_catalog_sync = StartCatalogSyncUseCase(
        product_source,
        catalog_item_processor,
        catalog_sync_executions,
    )

    container = punq.Container()
    container.register(Settings, instance=settings)
    container.register(ProductSource, instance=product_source)
    container.register(CatalogItemProcessor, instance=catalog_item_processor)
    container.register(CatalogSyncExecutionRepository, instance=catalog_sync_executions)
    container.register(NormalizeProductUseCase, instance=normalize_product)
    container.register(StartCatalogSyncUseCase, instance=start_catalog_sync)
    container.register(UserRepository, instance=repository)
    container.register(CreateUserUseCase, instance=CreateUserUseCase(repository))
    container.register(GetUserUseCase, instance=GetUserUseCase(repository))
    container.register(ListUsersUseCase, instance=ListUsersUseCase(repository))
    container.register(UpdateUserNameUseCase, instance=UpdateUserNameUseCase(repository))
    container.register(DeactivateUserUseCase, instance=DeactivateUserUseCase(repository))
    container.register(InfrastructureHealth, instance=infrastructure_health)
    return container, engine, infrastructure_health, product_source
