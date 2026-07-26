"""In-memory repository used by unit tests."""

from app.users.domain.entities.user import User
from app.users.domain.repositories.user_repository import UserRepository
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.user_id import UserId


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self.users: dict[UserId, User] = {}

    async def save(self, user: User) -> None:
        self.users[user.id] = user

    async def get_by_id(self, user_id: UserId) -> User | None:
        return self.users.get(user_id)

    async def get_by_email(self, email: Email) -> User | None:
        return next((user for user in self.users.values() if user.email == email), None)

    async def list(self, limit: int, offset: int) -> list[User]:
        users = sorted(self.users.values(), key=lambda user: user.created_at)
        return users[offset : offset + limit]

    async def update(self, user: User) -> None:
        self.users[user.id] = user
