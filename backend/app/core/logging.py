"""Application logging configuration.

Uvicorn only configures its own loggers, leaving the root logger without a
handler, so application logs would otherwise be silent. This attaches a single
console handler to the root logger (once) with a consistent, timestamped format.
"""

import logging

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(level: int = logging.INFO) -> None:
    """Attach a console handler to the root logger if none is present."""
    root = logging.getLogger()
    root.setLevel(level)
    if root.handlers:
        return
    # Handlers already configured (e.g. on reload), so avoid duplicating output.

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root.addHandler(handler)
