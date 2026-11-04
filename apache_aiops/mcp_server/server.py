"""Apache AIops MCP entry point (stdio)."""

import logging

from apache_aiops.mcp_server._annotations import apply_risk_annotations
from apache_aiops.mcp_server._shared import mcp
from apache_aiops.mcp_server.tools import httpd, undo  # noqa: F401 — registration

apply_risk_annotations(mcp)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    mcp.run(transport="stdio")
