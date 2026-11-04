"""Governed Apache HTTP Server read tools."""

from typing import Optional

from apache_aiops.governance import governed_tool
from apache_aiops.mcp_server._shared import _get_connection, mcp, tool_errors
from apache_aiops.ops import httpd


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_version(target: Optional[str] = None) -> dict:
    """[READ] Get Apache HTTP Server version from apachectl -v."""
    return httpd.version(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_config_check(target: Optional[str] = None) -> dict:
    """[READ] Run Apache's native config syntax test."""
    return httpd.config_check(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_vhosts(target: Optional[str] = None) -> dict:
    """[READ] Show Apache's parsed virtual-host mapping."""
    return httpd.vhosts(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_modules(target: Optional[str] = None) -> dict:
    """[READ] List Apache's loaded modules."""
    return httpd.modules(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_probe(target: Optional[str] = None) -> dict:
    """[READ] GET the configured health URL without downloading its body."""
    return httpd.probe(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_diagnose(target: Optional[str] = None) -> dict:
    """[READ] Correlate version, config, vhosts, modules and optional HTTP probe."""
    return httpd.diagnose(_get_connection(target))
