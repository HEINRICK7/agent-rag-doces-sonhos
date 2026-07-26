"""Logging configuration."""

import logging


def configure_logging(level: str) -> None:
    """Configure a compact, container-friendly log format once."""

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )
