"""Results emitted when an external product is synchronized."""

from dataclasses import dataclass
from enum import StrEnum

from app.catalog.domain.entities.product import Product


class ProductChangeKind(StrEnum):
    """Classification of an external product snapshot."""

    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"


@dataclass(frozen=True, slots=True)
class ProductUpsertResult:
    """Product plus the evidence needed by the synchronization run."""

    product: Product
    change: ProductChangeKind
    previous_fingerprint: str | None
    current_fingerprint: str
