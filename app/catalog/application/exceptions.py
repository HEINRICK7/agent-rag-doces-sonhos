"""Catalog application failures."""


class ProductPersistenceError(Exception):
    """Raised when a product cannot be persisted atomically."""

    code = "PRODUCT_PERSISTENCE_ERROR"

    def __init__(self, external_id: str) -> None:
        self.external_id = external_id
        super().__init__(f"Não foi possível persistir o produto {external_id!r}.")
