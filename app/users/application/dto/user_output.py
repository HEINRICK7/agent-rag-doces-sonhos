"""User output DTO."""

from dataclasses import dataclass
from datetime import datetime

from app.users.domain.entities.user import User


@dataclass(frozen=True, slots=True)
class UserOutput:
    id: str
    name: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, user: User) -> "UserOutput":
        return cls(
            id=str(user.id),
            name=user.name,
            email=str(user.email),
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
