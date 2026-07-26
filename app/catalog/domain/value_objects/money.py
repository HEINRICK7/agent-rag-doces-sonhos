"""Money that preserves an explicitly unknown currency."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from app.catalog.domain.exceptions import InvalidCatalogValueError

MONEY_PRECISION = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class Money:
    """Non-negative monetary amount with optional, never inferred, currency."""

    amount: Decimal
    currency: str | None = None

    def __post_init__(self) -> None:
        if not self.amount.is_finite() or self.amount < 0:
            raise InvalidCatalogValueError(
                "money.amount",
                "valor deve ser finito e não negativo.",
            )
        try:
            normalized_amount = self.amount.quantize(
                MONEY_PRECISION,
                rounding=ROUND_HALF_UP,
            )
        except InvalidOperation as error:
            raise InvalidCatalogValueError(
                "money.amount",
                "valor excede a precisão suportada.",
            ) from error

        normalized_currency = self.currency.strip().upper() if self.currency else None
        if normalized_currency is not None and (
            len(normalized_currency) != 3 or not normalized_currency.isalpha()
        ):
            raise InvalidCatalogValueError(
                "money.currency",
                "moeda deve usar três letras.",
            )
        object.__setattr__(self, "amount", normalized_amount)
        object.__setattr__(self, "currency", normalized_currency)

    @property
    def has_known_currency(self) -> bool:
        return self.currency is not None
