"""Commercial option offered for a product."""

from dataclasses import dataclass
from decimal import Decimal

from app.catalog.domain.exceptions import InvalidCatalogValueError
from app.catalog.domain.value_objects.money import Money


@dataclass(frozen=True, slots=True)
class ProductPriceOption:
    """Quantity, unit and price exposed as one commercial choice."""

    external_id: str | None
    label: str | None
    quantity: Decimal
    unit: str
    price: Money
    is_default: bool

    def __post_init__(self) -> None:
        if not self.quantity.is_finite() or self.quantity <= 0:
            raise InvalidCatalogValueError(
                "product_price_option.quantity",
                "quantidade deve ser finita e positiva.",
            )
        unit = self.unit.strip().upper()
        if not unit:
            raise InvalidCatalogValueError(
                "product_price_option.unit",
                "unidade obrigatória.",
            )
        external_id = self.external_id.strip() if self.external_id else None
        label = " ".join(self.label.split()) if self.label else None
        object.__setattr__(self, "external_id", external_id or None)
        object.__setattr__(self, "label", label or None)
        object.__setattr__(self, "quantity", self.quantity.normalize())
        object.__setattr__(self, "unit", unit)
