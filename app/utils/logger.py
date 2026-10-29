"""
logger.py - Centralized logging configuration.

Usage in any module:
    from app.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Processing document...")
"""

import logging
import sys


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Create and return a configured logger.

    Args:
        name: Logger name, typically __name__ of the calling module.
        level: Logging level (default: INFO).

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if the logger already exists.
    if not logger.handlers:
        logger.setLevel(level)

        # Console handler with a readable format.
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
