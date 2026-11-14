"""Governed Apache HTTP Server read tools."""

from typing import Annotated, Optional

from pydantic import Field

from apache_aiops.governance import governed_tool, mark_unknown
from apache_aiops.mcp_server._shared import _get_connection, mcp, tool_errors
from apache_aiops.ops import httpd


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_config_includes(
    target: Annotated[
        Optional[str],
        Field(description=("Configured target name; omit to use the default connection.")),
    ] = None,
) -> dict:
    """[READ] Show Apache's parsed config include tree with bounded output.

    Result: structured data or an explicit, sanitized operation error.
    """
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
def apache_static_directives(
    target: Annotated[
        Optional[str],
        Field(description=("Configured target name; omit to use the default connection.")),
    ] = None,
) -> dict:
    """[READ] List directives from Apache's static modules with bounded output.

    Result: structured data or an explicit, sanitized operation error.
    """
    return httpd.static_directives(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_build(
    target: Annotated[
        Optional[str],
        Field(description=("Configured target name; omit to use the default connection.")),
    ] = None,
) -> dict:
    """[READ] Show Apache build options and compiled paths.

    Result: structured data or an explicit, sanitized operation error.
    """
    return httpd.build(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_runtime_config(
    target: Annotated[
        Optional[str],
        Field(description=("Configured target name; omit to use the default connection.")),
    ] = None,
) -> dict:
    """[READ] Dump Apache's parsed runtime configuration.

    Result: structured data or an explicit, sanitized operation error.
    """
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
def apache_error_log(
    limit: Annotated[
        int,
        Field(
            description=("Maximum number of records to return; the operation enforces its bound.")
        ),
    ] = 50,
    target: Annotated[
        Optional[str],
        Field(description=("Configured target name; omit to use the default connection.")),
    ] = None,
) -> dict:
    """[READ] Tail an operator-configured Apache error log, with explicit truncation.

    Result: structured data or an explicit, sanitized operation error.
    """
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
        return {
            "dryRun": True,
            "configCheck": check,
            "probeBefore": before,
            "wouldRun": "apachectl graceful",
        }
    response = conn.graceful()
    try:
        after = httpd.probe(conn) if conn.target.probe_url else None
    except Exception as exc:
        return mark_unknown(
            {
                "accepted": True,
                "response": response,
                "probeAfter": None,
                "probeError": f"Probe failed after reload: {type(exc).__name__}",
            }
        )
    return mark_unknown(
        {
            "accepted": True,
            "response": response,
            "probeBefore": before,
            "probeAfter": after,
            "note": "A successful command/probe does not prove all workers loaded new config.",
        }
    )


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_version(target: Optional[str] = None) -> dict:
    """[READ] Get Apache HTTP Server version from apachectl -v."""
    return httpd.version(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_config_check(
    target: Annotated[
        Optional[str],
        Field(description=("Configured target name; omit to use the default connection.")),
    ] = None,
) -> dict:
    """[READ] Run Apache's native config syntax test.

    Use before a reload to check syntax; use apache_diagnose for correlated service and HTTP
    probe results.

    Result: structured data or an explicit, sanitized operation error.
    """
    return httpd.config_check(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_vhosts(
    target: Annotated[
        Optional[str],
        Field(description=("Configured target name; omit to use the default connection.")),
    ] = None,
) -> dict:
    """[READ] Show Apache's parsed virtual-host mapping.

    Result: structured data or an explicit, sanitized operation error.
    """
    return httpd.vhosts(_get_connection(target))


@mcp.tool()
@governed_tool(risk_level="low")
@tool_errors()
def apache_modules(
    target: Annotated[
        Optional[str],
        Field(description=("Configured target name; omit to use the default connection.")),
    ] = None,
) -> dict:
    """[READ] List Apache's loaded modules.

    Use for currently loaded modules; use apache_compiled_modules for modules built into the
    binary.

    Result: structured data or an explicit, sanitized operation error.
    """
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
def apache_diagnose(
    target: Annotated[
        Optional[str],
        Field(description=("Configured target name; omit to use the default connection.")),
    ] = None,
) -> dict:
    """[READ] Correlate version, config, vhosts, modules and optional HTTP probe.

    Use for cross-probe triage; use apache_config_check for syntax validation alone.

    Result: structured data or an explicit, sanitized operation error.
    """
    return httpd.diagnose(_get_connection(target))
