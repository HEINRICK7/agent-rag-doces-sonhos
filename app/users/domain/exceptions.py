"""Users domain errors."""

from app.shared.domain.exceptions import ValidationError


class UserNotFoundError(Exception):
    """Raised when a user does not exist."""

    code = "USER_NOT_FOUND"
    message = "Usuário não encontrado."


class EmailAlreadyExistsError(Exception):
    """Raised when an email is already registered."""

    code = "EMAIL_ALREADY_EXISTS"
    message = "E-mail já cadastrado."


class InvalidEmailError(ValidationError):
    """Raised when an email value is invalid."""

    code = "INVALID_EMAIL"
    message = "E-mail inválido."


class UserAlreadyInactiveError(ValidationError):
    """Raised when an inactive user is deactivated again."""

    code = "USER_ALREADY_INACTIVE"
    message = "Usuário já está desativado."
