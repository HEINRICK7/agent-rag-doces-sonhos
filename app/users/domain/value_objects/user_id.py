"""User identifier value object."""

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class UserId:
    """Strongly typed UUID used by the users domain."""

    value: UUID

    @classmethod
    def new(cls) -> "UserId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "UserId":
        return cls(UUID(value))

    def __str__(self) -> str:
        return str(self.value)
