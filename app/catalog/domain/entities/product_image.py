"""Product image metadata independent from its future storage adapter."""

from dataclasses import dataclass
from urllib.parse import urlsplit

from app.catalog.domain.exceptions import InvalidCatalogValueError


@dataclass(frozen=True, slots=True)
class ProductImage:
    """External image reference with room for a future internal object key."""

    source_url: str
    position: int
    is_primary: bool
    storage_key: str | None = None

    def __post_init__(self) -> None:
        normalized_url = self.source_url.strip()
        try:
            parts = urlsplit(normalized_url)
        except ValueError as error:
            raise InvalidCatalogValueError(
                "product_image.source_url",
                "URL inválida.",
            ) from error
        if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
            raise InvalidCatalogValueError(
                "product_image.source_url",
                "URL absoluta HTTP(S) obrigatória.",
            )
        if self.position < 0:
            raise InvalidCatalogValueError(
                "product_image.position",
                "posição não pode ser negativa.",
            )
        normalized_key = self.storage_key.strip() if self.storage_key else None
        object.__setattr__(self, "source_url", normalized_url)
        object.__setattr__(self, "storage_key", normalized_key or None)
