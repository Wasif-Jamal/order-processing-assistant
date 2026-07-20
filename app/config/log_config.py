"""Centralized logging configuration."""

import logging
import logging.handlers
from pathlib import Path

from app.config.env_config import settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"


class LogConfig:
    """Configure and provide application loggers.

    The root logger is configured only once. Log messages are written to both
    the console and a daily rotating log file.
    """

    def __init__(self) -> None:
        """Initialize the logging configuration."""
        self._configured = False

    def _configure_root(self) -> None:
        """Configure the root logger if it has not already been configured."""
        if self._configured:
            return

        formatter = logging.Formatter(_LOG_FORMAT)

        _LOG_DIR.mkdir(parents=True, exist_ok=True)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=_LOG_DIR / "app.log",
            when="midnight",
            backupCount=30,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)

        root_logger = logging.getLogger()

        has_console = any(
            isinstance(handler, logging.StreamHandler)
            and not isinstance(handler, logging.FileHandler)
            for handler in root_logger.handlers
        )

        has_file = any(
            isinstance(handler, logging.handlers.TimedRotatingFileHandler)
            for handler in root_logger.handlers
        )

        if not has_console:
            root_logger.addHandler(console_handler)

        if not has_file:
            root_logger.addHandler(file_handler)

        log_level = getattr(
            logging,
            settings.log_level.upper(),
            logging.INFO,
        )

        root_logger.setLevel(log_level)

        self._configured = True

    def get_logger(self, name: str) -> logging.Logger:
        """Return a configured logger.

        Args:
            name: Logger name, typically ``__name__``.

        Returns:
            A configured ``logging.Logger`` instance.
        """
        self._configure_root()
        return logging.getLogger(name)


config = LogConfig()
