"""Apache AIops CLI; service reads call governed MCP twins."""

from __future__ import annotations

import json
import sys
from typing import Annotated

import typer
import yaml

from apache_aiops.cli._common import cli_errors, console, double_confirm, governed
from apache_aiops.cli.undo import undo_app
from apache_aiops.governance.paths import ops_home

app = typer.Typer(
    name="apache-aiops", no_args_is_help=True, help="Audited Apache HTTP Server diagnosis."
)
app.add_typer(undo_app, name="undo")
Target = Annotated[str | None, typer.Option("--target", "-t", help="Configured Apache target")]


def _print(result: dict) -> None:
    console.print_json(json.dumps(governed(result)))


@app.command("config-includes")
@cli_errors
def config_includes(target: Target = None) -> None:
    """Show the parsed Apache config include tree."""
    from apache_aiops.mcp_server.tools.httpd import apache_config_includes
    _print(apache_config_includes(target=target))


@app.command("compiled-modules")
@cli_errors
def compiled_modules(target: Target = None) -> None:
    """List modules compiled into Apache."""
    from apache_aiops.mcp_server.tools.httpd import apache_compiled_modules
    _print(apache_compiled_modules(target=target))


@app.command("static-directives")
@cli_errors
def static_directives(target: Target = None) -> None:
    """List directives supplied by static Apache modules."""
    from apache_aiops.mcp_server.tools.httpd import apache_static_directives
    _print(apache_static_directives(target=target))


@app.command("build")
@cli_errors
def build(target: Target = None) -> None:
    """Show Apache build flags and paths."""
    from apache_aiops.mcp_server.tools.httpd import apache_build
    _print(apache_build(target=target))


@app.command("runtime-config")
@cli_errors
def runtime_config(target: Target = None) -> None:
    """Show parsed Apache runtime configuration."""
    from apache_aiops.mcp_server.tools.httpd import apache_runtime_config
    _print(apache_runtime_config(target=target))


@app.command("server-status")
@cli_errors
def server_status(target: Target = None) -> None:
    """Show configured mod_status auto metrics."""
    from apache_aiops.mcp_server.tools.httpd import apache_server_status
    _print(apache_server_status(target=target))


@app.command("error-log")
@cli_errors
def error_log(limit: int = 50, target: Target = None) -> None:
    """Tail the operator-configured Apache error log."""
    from apache_aiops.mcp_server.tools.httpd import apache_error_log
    _print(apache_error_log(limit=limit, target=target))


@app.command("access-status")
@cli_errors
def access_status(limit: int = 200, target: Target = None) -> None:
    """Summarize recent common/combined access-log status codes."""
    from apache_aiops.mcp_server.tools.httpd import apache_access_status
    _print(apache_access_status(limit=limit, target=target))


@app.command("graceful-reload")
@cli_errors
def graceful_reload(dry_run: bool = False, target: Target = None) -> None:
    """Check config and request an Apache graceful reload."""
    from apache_aiops.mcp_server.tools.httpd import apache_graceful_reload
    if not dry_run:
        double_confirm("gracefully reload Apache", target or "default")
    _print(apache_graceful_reload(dry_run=dry_run, target=target))


@app.command("init")
@cli_errors
def init() -> None:
    """Configure a local Apache HTTP Server target."""
    from apache_aiops.config import TargetConfig

    name = typer.prompt("Target name", default="local")
    probe_url = typer.prompt("HTTP health URL (optional)", default="")
    status_url = typer.prompt("mod_status auto URL (optional)", default="")
    error_log = typer.prompt("Absolute error log path (optional)", default="")
    access_log = typer.prompt("Absolute access log path (optional)", default="")
    chosen = TargetConfig(
        name=name, probe_url=probe_url or None, status_url=status_url or None,
        error_log=error_log or None, access_log=access_log or None,
    )
    path = ops_home() / "config.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError(f"Config exists at {path}; edit it to add a target.")
    path.write_text(
        yaml.safe_dump({"targets": [{
            "name": chosen.name, "probe_url": chosen.probe_url,
            "status_url": chosen.status_url, "error_log": chosen.error_log,
            "access_log": chosen.access_log,
        }]})
    )
    path.chmod(0o600)
    console.print(f"Configured {name} at {path}")


@app.command("version")
@cli_errors
def version(target: Target = None) -> None:
    """Show Apache version."""
    from apache_aiops.mcp_server.tools.httpd import apache_version

    _print(apache_version(target=target))


@app.command("config-check")
@cli_errors
def config_check(target: Target = None) -> None:
    """Run Apache config syntax test."""
    from apache_aiops.mcp_server.tools.httpd import apache_config_check

    _print(apache_config_check(target=target))


@app.command("vhosts")
@cli_errors
def vhosts(target: Target = None) -> None:
    """Show parsed virtual-host map."""
    from apache_aiops.mcp_server.tools.httpd import apache_vhosts

    _print(apache_vhosts(target=target))


@app.command("modules")
@cli_errors
def modules(target: Target = None) -> None:
    """List loaded Apache modules."""
    from apache_aiops.mcp_server.tools.httpd import apache_modules

    _print(apache_modules(target=target))


@app.command("probe")
@cli_errors
def probe(target: Target = None) -> None:
    """Probe configured HTTP health URL."""
    from apache_aiops.mcp_server.tools.httpd import apache_probe

    _print(apache_probe(target=target))


@app.command("diagnose")
@cli_errors
def diagnose(target: Target = None) -> None:
    """Correlate Apache config and HTTP probes."""
    from apache_aiops.mcp_server.tools.httpd import apache_diagnose

    _print(apache_diagnose(target=target))


@app.command("doctor")
@cli_errors
def doctor(target: Target = None) -> None:
    """Test access to apachectl -v."""
    from apache_aiops.mcp_server.tools.httpd import apache_version

    _print(apache_version(target=target))


@app.command("mcp")
@cli_errors
def mcp_cmd() -> None:
    """Start stdio MCP server."""
    if sys.version_info < (3, 11):
        raise typer.Exit(2)
    from apache_aiops.mcp_server.server import main

    main()


if __name__ == "__main__":
    app()
