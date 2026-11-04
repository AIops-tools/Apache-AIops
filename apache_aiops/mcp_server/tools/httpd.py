"""Governed Apache HTTP Server read tools."""

from typing import Optional

from apache_aiops.governance import governed_tool, mark_unknown
from apache_aiops.mcp_server._shared import _get_connection, mcp, tool_errors
from apache_aiops.ops import httpd


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_config_includes(target: Optional[str] = None) -> dict:
    """[READ] Show Apache's parsed config include tree with bounded output."""
    return httpd.config_includes(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_compiled_modules(target: Optional[str] = None) -> dict:
    """[READ] List modules compiled into Apache, excluding dynamic modules."""
    return httpd.compiled_modules(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_static_directives(target: Optional[str] = None) -> dict:
    """[READ] List directives from Apache's static modules with bounded output."""
    return httpd.static_directives(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_build(target: Optional[str] = None) -> dict:
    """[READ] Show Apache build options and compiled paths."""
    return httpd.build(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_runtime_config(target: Optional[str] = None) -> dict:
    """[READ] Dump Apache's parsed runtime configuration."""
    return httpd.runtime_config(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_server_status(target: Optional[str] = None) -> dict:
    """[READ] Get bounded machine-readable mod_status metrics from configured URL."""
    return httpd.server_status(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_error_log(limit: int = 50, target: Optional[str] = None) -> dict:
    """[READ] Tail an operator-configured Apache error log, with explicit truncation."""
    return httpd.error_log(_get_connection(target), limit)


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_access_status(limit: int = 200, target: Optional[str] = None) -> dict:
    """[READ] Count HTTP statuses in recent common/combined access logs, without raw requests."""
    return httpd.access_status(_get_connection(target), limit)


@mcp.tool()
@governed_tool(risk_level="medium")
@tool_errors()
def apache_graceful_reload(dry_run: bool = False, target: Optional[str] = None) -> dict:
    """[WRITE] Config-check then request a graceful reload; outcome needs operator check."""
    conn = _get_connection(target)
    check = httpd.config_check(conn)
    before = httpd.probe(conn) if conn.target.probe_url else None
    if dry_run:
        return {"dryRun": True, "configCheck": check, "probeBefore": before,
                "wouldRun": "apachectl graceful"}
    response = conn.graceful()
    try:
        after = httpd.probe(conn) if conn.target.probe_url else None
    except Exception as exc:
        return mark_unknown({"accepted": True, "response": response, "probeAfter": None,
                             "probeError": f"Probe failed after reload: {type(exc).__name__}"})
    return mark_unknown({
        "accepted": True, "response": response, "probeBefore": before,
        "probeAfter": after,
        "note": "A successful command/probe does not prove all workers loaded new config.",
    })


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
