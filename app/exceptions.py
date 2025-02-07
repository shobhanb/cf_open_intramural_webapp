from __future__ import annotations

import logging
import sys

log = logging.getLogger(__name__)


def handle_exception(exc_type, exc_value, exc_traceback) -> None:  # noqa: ANN001
    """Handle uncaught exception."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.excepthook(exc_type, exc_value, exc_traceback)
        return
    log.critical("Uncaught Exception", exc_info=(exc_type, exc_value, exc_traceback))
