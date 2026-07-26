"""Unit tests for users application use cases."""

import unittest

from app.shared.domain.exceptions import ValidationError
from app.users.application.dto.create_user_input import CreateUserInput
from app.users.application.usecases.create_user import CreateUserUseCase
from app.users.application.usecases.deactivate_user import DeactivateUserUseCase
from app.users.application.usecases.get_user import GetUserUseCase
from app.users.application.usecases.list_users import ListUsersUseCase
from app.users.application.usecases.update_user_name import UpdateUserNameUseCase
from app.users.domain.exceptions import EmailAlreadyExistsError, UserNotFoundError
from app.users.domain.value_objects.user_id import UserId

from tests.fixtures.in_memory_user_repository import InMemoryUserRepository


class UserUseCasesTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.repository = InMemoryUserRepository()
        self.create = CreateUserUseCase(self.repository)
        self.get = GetUserUseCase(self.repository)
        self.list = ListUsersUseCase(self.repository)
        self.update = UpdateUserNameUseCase(self.repository)
        self.deactivate = DeactivateUserUseCase(self.repository)

    async def test_creates_and_gets_user(self) -> None:
        created = await self.create.execute(CreateUserInput("Carlos", "carlos@example.com"))

        found = await self.get.execute(UserId.from_string(created.id))

        self.assertEqual(found.email, "carlos@example.com")

    async def test_rejects_duplicate_email(self) -> None:
        input_data = CreateUserInput("Carlos", "carlos@example.com")
        await self.create.execute(input_data)

        with self.assertRaises(EmailAlreadyExistsError):
            await self.create.execute(input_data)

    async def test_lists_with_pagination_and_rejects_invalid_limit(self) -> None:
        await self.create.execute(CreateUserInput("Carlos", "carlos@example.com"))
        await self.create.execute(CreateUserInput("Ana", "ana@example.com"))

        users = await self.list.execute(limit=1, offset=1)

        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].name, "Ana")
        with self.assertRaises(ValidationError):
            await self.list.execute(limit=0)

    async def test_updates_and_deactivates_user(self) -> None:
        created = await self.create.execute(CreateUserInput("Carlos", "carlos@example.com"))
        user_id = UserId.from_string(created.id)

        updated = await self.update.execute(user_id, "Carlos Henrique")
        deactivated = await self.deactivate.execute(user_id)

        self.assertEqual(updated.name, "Carlos Henrique")
        self.assertFalse(deactivated.is_active)

    async def test_raises_when_user_does_not_exist(self) -> None:
        with self.assertRaises(UserNotFoundError):
            await self.get.execute(UserId.new())
