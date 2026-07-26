"""Pure users domain entity."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.shared.domain.exceptions import ValidationError
from app.users.domain.exceptions import UserAlreadyInactiveError
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.user_id import UserId


def _validate_name(name: str) -> str:
    normalized = name.strip()
    if not normalized:
        raise ValidationError("Nome não pode estar vazio.")
    if len(normalized) > 150:
        raise ValidationError("Nome deve ter no máximo 150 caracteres.")
    return normalized


@dataclass(slots=True)
class User:
    """User aggregate containing its own invariants."""

    id: UserId
    name: str
    email: Email
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.name = _validate_name(self.name)
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValidationError("Datas do usuário devem conter timezone.")

    @classmethod
    def create(cls, name: str, email: Email) -> "User":
        now = datetime.now(UTC)
        return cls(
            id=UserId.new(),
            name=name,
            email=email,
            created_at=now,
            updated_at=now,
        )

    def update_name(self, name: str) -> None:
        self.name = _validate_name(name)
        self.updated_at = datetime.now(UTC)

    def deactivate(self) -> None:
        if not self.is_active:
            raise UserAlreadyInactiveError()
        self.is_active = False
        self.updated_at = datetime.now(UTC)
