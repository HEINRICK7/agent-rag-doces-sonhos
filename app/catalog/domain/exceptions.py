"""Catalog domain failures."""


class CatalogDomainError(ValueError):
    """Base failure for invalid catalog state or transitions."""


class InvalidCatalogValueError(CatalogDomainError):
    """Raised when a catalog value violates an invariant."""

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"Valor inválido em {field!r}: {reason}")


class ExternalProductIdentityMismatchError(CatalogDomainError):
    """Raised when an external snapshot targets another product."""

    def __init__(self, expected: str, received: str) -> None:
        self.expected = expected
        self.received = received
        super().__init__(
            f"Snapshot externo pertence a {received!r}; produto esperado: {expected!r}."
        )
