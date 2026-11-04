"""Apache AIops CLI; service reads call governed MCP twins."""

from __future__ import annotations

import json
import sys
from typing import Annotated

import typer
import yaml

from apache_aiops.cli._common import cli_errors, console, governed
from apache_aiops.cli.undo import undo_app
from apache_aiops.governance.paths import ops_home

app = typer.Typer(
    name="apache-aiops", no_args_is_help=True, help="Audited Apache HTTP Server diagnosis."
)
app.add_typer(undo_app, name="undo")
Target = Annotated[str | None, typer.Option("--target", "-t", help="Configured Apache target")]


def _print(result: dict) -> None:
    console.print_json(json.dumps(governed(result)))


@app.command("init")
@cli_errors
def init() -> None:
    """Configure a local Apache HTTP Server target."""
    from apache_aiops.config import TargetConfig

    name = typer.prompt("Target name", default="local")
    probe_url = typer.prompt("HTTP health URL (optional)", default="")
    chosen = TargetConfig(name=name, probe_url=probe_url or None)
    path = ops_home() / "config.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError(f"Config exists at {path}; edit it to add a target.")
    path.write_text(
        yaml.safe_dump({"targets": [{"name": chosen.name, "probe_url": chosen.probe_url}]})
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
