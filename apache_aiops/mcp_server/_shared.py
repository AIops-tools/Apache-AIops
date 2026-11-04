"""Shared Apache MCP server and sanitized errors."""

from __future__ import annotations

import functools
import logging
import threading
from collections.abc import Callable
from typing import Any, Optional

from mcp.server import MCPServer

from apache_aiops import __version__
from apache_aiops.connection import ApacheCommandError, ApacheWriteUncertainError, ConnectionManager
from apache_aiops.governance import mark_unknown, sanitize

logger = logging.getLogger(__name__)
_ERROR_MAX = 800


def tool_errors(shape: str = "dict") -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                logger.error("Tool %s failed", func.__name__, exc_info=True)
                message = (
                    sanitize(str(exc), _ERROR_MAX)
                    if isinstance(
                        exc, (ApacheCommandError, ValueError, KeyError, FileNotFoundError, OSError)
                    )
                    else f"{type(exc).__name__}: operation failed."
                )
                payload = {
                    "error": message,
                    "hint": "Run 'apache-aiops doctor' and check local command permissions.",
                }
                if isinstance(exc, ApacheWriteUncertainError):
                    return mark_unknown(payload)
                return payload

        return wrapper

    return decorator


mcp = MCPServer(
    "apache-aiops",
    version=__version__,
    instructions=(
        "Governed Apache HTTP Server config, vhost, module and HTTP diagnosis. "
        "Every tool is audited and budgeted."
    ),
)
_manager: Optional[ConnectionManager] = None
_lock = threading.Lock()


def _get_connection(target: Optional[str] = None) -> Any:
    global _manager
    with _lock:
        if _manager is None:
            _manager = ConnectionManager()
        manager = _manager
    return manager.connect(target)
