"""Deterministic fingerprint for the source-owned product snapshot."""

import hashlib
import json
from datetime import datetime
from decimal import Decimal

from app.catalog.domain.entities.product import Product


def fingerprint_product(product: Product) -> str:
    """Return a stable hash for fields supplied by the external catalog.

    Local identity, protection flags and local timestamps are intentionally
    excluded so that a repeated import can be recognized even when the local
    aggregate was rehydrated with a different UUID.
    """

    payload = {
        "external_id": product.external_id,
        "name": product.name,
        "description": product.description,
        "category_external_id": product.category_external_id,
        "subcategory_external_id": product.subcategory_external_id,
        "is_active": product.is_active,
        "availability": product.availability.value,
        "price_options": [
            {
                "external_id": option.external_id,
                "label": option.label,
                "quantity": _decimal(option.quantity),
                "unit": option.unit,
                "amount": _decimal(option.price.amount),
                "currency": option.price.currency,
                "is_default": option.is_default,
            }
            for option in product.price_options
        ],
        "images": [
            {
                "source_url": image.source_url,
                "position": image.position,
                "is_primary": image.is_primary,
                "storage_key": image.storage_key,
            }
            for image in product.images
        ],
        "source_created_at": _timestamp(product.source_created_at),
        "source_updated_at": _timestamp(product.source_updated_at),
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _decimal(value: Decimal) -> str:
    return format(value, "f")


def _timestamp(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None
