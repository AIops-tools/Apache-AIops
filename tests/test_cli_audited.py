"""CLI Apache HTTP Server reads call the same governed MCP functions."""

import ast
from pathlib import Path

from typer.testing import CliRunner


def test_apache_read_commands_delegate_to_mcp_tools():
    path = Path(__file__).parents[1] / "apache_aiops/cli/_root.py"
    tree = ast.parse(path.read_text())
    commands = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and any(
            isinstance(d, ast.Call)
            and isinstance(d.func, ast.Attribute)
            and d.func.attr == "command"
            for d in node.decorator_list
        )
    }
    reads = {"version", "config_check", "vhosts", "modules", "probe", "diagnose", "doctor"}
    assert reads <= commands.keys()
    for name in reads:
        imports = [node for node in ast.walk(commands[name]) if isinstance(node, ast.ImportFrom)]
        assert any(
            (node.module or "").startswith("apache_aiops.mcp_server.tools") for node in imports
        )


def test_cli_help_lists_apache_operations():
    from apache_aiops.cli import app

    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("version", "config-check", "vhosts", "modules", "diagnose"):
        assert command in result.output
