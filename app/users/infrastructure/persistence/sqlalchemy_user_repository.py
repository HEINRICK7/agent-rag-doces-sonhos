"""SQLAlchemy implementation of the users repository contract."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.users.domain.entities.user import User
from app.users.domain.exceptions import EmailAlreadyExistsError
from app.users.domain.repositories.user_repository import UserRepository
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.user_id import UserId
from app.users.infrastructure.persistence.mappers import to_domain, to_model
from app.users.infrastructure.persistence.models import UserModel


class SqlAlchemyUserRepository(UserRepository):
    """Repository that opens one short-lived session per operation."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save(self, user: User) -> None:
        async with self._session_factory() as session:
            session.add(to_model(user))
            try:
                await session.commit()
            except IntegrityError as error:
                await session.rollback()
                raise EmailAlreadyExistsError() from error

    async def get_by_id(self, user_id: UserId) -> User | None:
        async with self._session_factory() as session:
            model = await session.get(UserModel, user_id.value)
            return to_domain(model) if model is not None else None

    async def get_by_email(self, email: Email) -> User | None:
        async with self._session_factory() as session:
            result = await session.execute(select(UserModel).where(UserModel.email == str(email)))
            model = result.scalar_one_or_none()
            return to_domain(model) if model is not None else None

    async def list(self, limit: int, offset: int) -> list[User]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel)
                .order_by(UserModel.created_at, UserModel.id)
                .limit(limit)
                .offset(offset)
            )
            return [to_domain(model) for model in result.scalars().all()]

    async def update(self, user: User) -> None:
        async with self._session_factory() as session:
            model = await session.get(UserModel, user.id.value)
            if model is None:
                return
            model.name = user.name
            model.email = str(user.email)
            model.is_active = user.is_active
            model.updated_at = user.updated_at
            await session.commit()
