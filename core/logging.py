from __future__ import annotations

import logging

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging(level: str = "INFO") -> None:
    numeric_level = logging.getLevelName(level.upper())
    if isinstance(numeric_level, str):
        numeric_level = logging.INFO
    logging.basicConfig(level=numeric_level, format=LOG_FORMAT)


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name or "ebay-agent")