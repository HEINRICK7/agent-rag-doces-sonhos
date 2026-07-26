"""Email value object."""

import re
from dataclasses import dataclass

from app.users.domain.exceptions import InvalidEmailError

_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@dataclass(frozen=True, slots=True)
class Email:
    """Normalized and validated email address."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not _EMAIL_PATTERN.fullmatch(normalized):
            raise InvalidEmailError()
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
