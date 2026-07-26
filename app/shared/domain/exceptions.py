"""Shared domain and application error types."""


class DomainError(Exception):
    """Base class for expected domain errors."""

    code = "DOMAIN_ERROR"
    message = "Erro de domínio."


class ValidationError(DomainError):
    """Raised when a domain invariant is violated."""

    code = "VALIDATION_ERROR"
    message = "Dados inválidos."


class InfrastructureError(Exception):
    """Raised when an infrastructure operation cannot be completed."""

    code = "INFRASTRUCTURE_ERROR"
    message = "Erro interno de infraestrutura."
