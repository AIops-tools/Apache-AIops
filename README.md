<!-- mcp-name: io.github.AIops-tools/apache-aiops -->
# Apache AIops

A dedicated, governed MCP server, CLI and skill for Apache HTTP Server. The 0.1.0 source tree provides 6 Apache read tools plus `undo_list` and `undo_apply`. It uses Apache's own `apachectl` diagnostics and an optional configured HTTP health URL. Every MCP call is audited and budgeted by the vendored governance harness.

## What it checks

- Apache version, config syntax, parsed virtual hosts and loaded modules.
- Optional HTTP health status without downloading the response body.
- `apache_diagnose` correlates the checks and preserves failures as errors with `data: null`.

## Setup from source

Requires Python 3.11+, `uv`, and `apachectl` on the operator host. Run `uv sync --dev`, `uv run apache-aiops init`, then `uv run apache-aiops doctor`. Manual `~/.apache-aiops/config.yaml`:

```yaml
targets:
  - name: local
    apachectl_bin: apachectl
    probe_url: http://127.0.0.1/health
    timeout: 10
    verify_ssl: true
```

Run `uv run apache-aiops diagnose`. The MCP entry point is `uv run apache-aiops-mcp`. The optional HTTP probe is configured by the operator, not chosen by a tool caller. TLS verification is enabled by default, and `ca_file` accepts a custom CA PEM.

## Scope and verification

This first slice is read-only. It does not edit virtual hosts, reload the service, manage TLS certificates, or change modules. Those actions need a live lab showing config-check, reload result and recovery semantics. See [verification](docs/VERIFICATION.md). Missing operations and live-environment feedback are welcome as issues or PRs.
