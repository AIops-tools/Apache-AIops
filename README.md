<!-- mcp-name: io.github.AIops-tools/apache-aiops -->
# Apache AIops

A dedicated, governed MCP server, CLI and skill for Apache HTTP Server with 16 MCP tools. It uses Apache's own `apachectl` diagnostics, optional operator-configured HTTP health and `mod_status` URLs, and a bounded operator-configured error log. Every call is audited and budgeted by the vendored governance harness.

## What it checks

- Apache version, config syntax, parsed virtual hosts and loaded modules.
- Build options and parsed runtime configuration.
- Parsed config include tree, compiled modules and directives from static modules.
- Optional machine-readable `mod_status` metrics and bounded error-log tail.
- Optional HTTP health status without downloading the response body.
- `apache_diagnose` correlates the checks and preserves failures as errors with `data: null`.

## Setup from source

Requires Python 3.11+, `uv`, and `apachectl` on the operator host. Run `uv sync --dev`, `uv run apache-aiops init`, then `uv run apache-aiops doctor`. Manual `~/.apache-aiops/config.yaml`:

```yaml
targets:
  - name: local
    apachectl_bin: apachectl
    probe_url: http://127.0.0.1/health
    status_url: http://127.0.0.1/server-status?auto
    error_log: /var/log/apache2/error.log
    timeout: 10
    verify_ssl: true
```

Run `uv run apache-aiops diagnose`. The MCP entry point is `uv run apache-aiops-mcp`. The optional HTTP probe is configured by the operator, not chosen by a tool caller. TLS verification is enabled by default, and `ca_file` accepts a custom CA PEM.

## Scope and verification

`graceful-reload` first runs `configtest`, supports dry-run and two CLI confirmations, and reports an unknown final outcome even if the command returned: existing workers may still serve the old config. It has no safe inverse when the prior config file is not snapshotted. Vhost editing, TLS certificate management and module changes remain outside this release. See [verification](docs/VERIFICATION.md). Missing operations and live-environment feedback are welcome as issues or PRs.
