"""Persistence contract for users."""

from typing import Protocol

from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.user_id import UserId


class UserRepository(Protocol):
    """Repository contract implemented by infrastructure adapters."""

    async def save(self, user: User) -> None: ...

    async def get_by_id(self, user_id: UserId) -> User | None: ...

    async def get_by_email(self, email: Email) -> User | None: ...

    async def list(self, limit: int, offset: int) -> list[User]: ...

    async def update(self, user: User) -> None: ...
