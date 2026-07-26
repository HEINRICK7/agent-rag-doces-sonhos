"""Mappers between pure domain and SQLAlchemy models."""

from datetime import UTC, datetime

from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.user_id import UserId
from app.users.infrastructure.persistence.models import UserModel


def to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id.value,
        name=user.name,
        email=str(user.email),
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def to_domain(model: UserModel) -> User:
    created_at = _as_utc(model.created_at)
    updated_at = _as_utc(model.updated_at)
    return User(
        id=UserId(model.id),
        name=model.name,
        email=Email(model.email),
        is_active=model.is_active,
        created_at=created_at,
        updated_at=updated_at,
    )


def _as_utc(value: datetime) -> datetime:
    """Restore UTC information for drivers that return naive timestamps."""

    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
