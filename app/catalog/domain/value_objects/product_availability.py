"""Explicit product availability states."""

from enum import StrEnum


class ProductAvailability(StrEnum):
    """Availability never inferred from a missing value."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    OUT_OF_STOCK = "out_of_stock"
    UNKNOWN = "unknown"
