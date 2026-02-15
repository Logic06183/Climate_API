"""
Logging configuration for Climate Toolkit.

Provides centralized logging with configurable levels and outputs.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import LoggingConfig, get_config


def setup_logger(
    name: str = "climate_toolkit",
    config: Optional[LoggingConfig] = None,
) -> logging.Logger:
    """
    Set up and configure a logger instance.

    Args:
        name: Name for the logger (default: "climate_toolkit")
        config: Logging configuration (uses global config if None)

    Returns:
        Configured logger instance
    """
    if config is None:
        config = get_config().logging

    logger = logging.getLogger(name)
    logger.setLevel(config.level)

    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(config.level)

    # Create formatter
    formatter = logging.Formatter(
        fmt=config.format,
        datefmt=config.date_format,
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if configured)
    if config.log_to_file and config.log_file:
        # Ensure log directory exists
        log_file = Path(config.log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(config.level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to avoid duplicate logs
    logger.propagate = False

    return logger


# Global logger instance
_global_logger: Optional[logging.Logger] = None


def get_logger(name: str = "climate_toolkit") -> logging.Logger:
    """
    Get the global logger instance.

    Args:
        name: Logger name (default: "climate_toolkit")

    Returns:
        Logger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_logger(name)
    return _global_logger


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        logger_name = f"climate_toolkit.{self.__class__.__name__}"
        return logging.getLogger(logger_name)
