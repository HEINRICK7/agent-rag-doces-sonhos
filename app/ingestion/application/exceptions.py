"""Expected failures exposed by an external product source."""

from collections.abc import Sequence


class ProductSourceError(Exception):
    """Base error for failures while reading the external catalog."""

    code = "PRODUCT_SOURCE_ERROR"


class ProductSourceConfigurationError(ProductSourceError):
    """Raised when required connection settings are absent."""

    code = "PRODUCT_SOURCE_CONFIGURATION_ERROR"


class ProductSourceAuthenticationError(ProductSourceError):
    """Raised when the external source rejects configured credentials."""

    code = "PRODUCT_SOURCE_AUTHENTICATION_ERROR"


class ProductSourceRateLimitError(ProductSourceError):
    """Raised when the retry budget is exhausted after rate limiting."""

    code = "PRODUCT_SOURCE_RATE_LIMIT_ERROR"


class ProductSourceUnavailableError(ProductSourceError):
    """Raised after retryable transport or server failures are exhausted."""

    code = "PRODUCT_SOURCE_UNAVAILABLE_ERROR"


class ProductSourceResponseError(ProductSourceError):
    """Raised for a non-retryable HTTP response."""

    code = "PRODUCT_SOURCE_RESPONSE_ERROR"

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"A API externa respondeu com status {status_code}.")


class InvalidProductSourcePayloadError(ProductSourceError):
    """Raised when JSON or pagination data cannot be interpreted safely."""

    code = "INVALID_PRODUCT_SOURCE_PAYLOAD"


class ExternalProductMappingError(ProductSourceError):
    """Raised when a known external payload cannot satisfy the internal DTO."""

    code = "EXTERNAL_PRODUCT_MAPPING_ERROR"

    def __init__(self, message: str, details: Sequence[object]) -> None:
        self.details = tuple(details)
        super().__init__(message)


class CatalogSyncError(Exception):
    """Base error for catalog synchronization orchestration."""

    code = "CATALOG_SYNC_ERROR"


class CatalogSyncAlreadyRunningError(CatalogSyncError):
    """Raised when another synchronization already owns the execution slot."""

    code = "CATALOG_SYNC_ALREADY_RUNNING"

    def __init__(self) -> None:
        super().__init__("Já existe uma sincronização de catálogo em andamento.")


class CatalogSyncExecutionNotFoundError(CatalogSyncError):
    """Raised when a requested execution cannot be reprocessed."""

    code = "CATALOG_SYNC_EXECUTION_NOT_FOUND"

    def __init__(self, execution_id: str) -> None:
        self.execution_id = execution_id
        super().__init__(f"A execução de sincronização {execution_id!r} não foi encontrada.")


class CatalogSyncFailedError(CatalogSyncError):
    """Raised after a source-level failure has been recorded."""

    code = "CATALOG_SYNC_FAILED"

    def __init__(self, execution_id: str) -> None:
        self.execution_id = execution_id
        super().__init__(f"A sincronização {execution_id!r} falhou ao percorrer a fonte.")


class ProductNormalizationError(Exception):
    """Controlled rejection of a mapped product that violates the internal contract."""

    code = "PRODUCT_NORMALIZATION_ERROR"

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"Produto rejeitado no campo {field!r}: {reason}")
