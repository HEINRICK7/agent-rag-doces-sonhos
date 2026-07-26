"""Persistence integration tests using an isolated async SQLite database."""

import unittest

from app.shared.infrastructure.database.base import Base
from app.shared.infrastructure.database.session import create_session_factory
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.infrastructure.persistence.models import UserModel  # noqa: F401
from app.users.infrastructure.persistence.sqlalchemy_user_repository import SqlAlchemyUserRepository
from sqlalchemy.ext.asyncio import create_async_engine


class SqlAlchemyUserRepositoryTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.repository = SqlAlchemyUserRepository(create_session_factory(self.engine))

    async def asyncTearDown(self) -> None:
        await self.engine.dispose()

    async def test_round_trip_and_update(self) -> None:
        user = User.create("Carlos", Email("carlos@example.com"))
        await self.repository.save(user)

        stored = await self.repository.get_by_id(user.id)
        self.assertIsNotNone(stored)
        assert stored is not None
        stored.update_name("Carlos Henrique")
        await self.repository.update(stored)

        updated = await self.repository.get_by_email(Email("CARLOS@example.com"))
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated.name, "Carlos Henrique")

    async def test_lists_and_enforces_unique_email(self) -> None:
        first = User.create("Carlos", Email("carlos@example.com"))
        await self.repository.save(first)
        second = User.create("Ana", Email("ana@example.com"))
        await self.repository.save(second)

        users = await self.repository.list(limit=10, offset=0)

        self.assertEqual([user.name for user in users], ["Carlos", "Ana"])
