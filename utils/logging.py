from collections.abc import MutableMapping
from typing import Any

import structlog


def _clean_format(
    _logger: Any,
    _method_name: str,
    event_dict: MutableMapping[str, Any],
) -> str:
    event = str(event_dict.get("event", ""))
    keys = {k: v for k, v in event_dict.items() if k not in {"event", "log_level"}}

    parts = [f"[{event}]"]

    for k, v in keys.items():
        parts.append(f"{k}={v}")

    return " ".join(parts)


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            _clean_format,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger() -> structlog.stdlib.BoundLogger:
    return structlog.get_logger()
