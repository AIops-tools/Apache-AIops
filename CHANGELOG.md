# Changelog

## v0.2.2 — 2026-11-14

- Clarify Apache configuration, module, probe and diagnosis tool inputs and results in MCP tool definitions.

## v0.2.1 — 2026-11-08

- Report a completed but unhealthy HTTP probe separately from probe execution failures in `apache_diagnose`; return an explicit tri-state `healthy` verdict.

## v0.2.0 — 2026-11-05

- Expand to 17 governed MCP/CLI tools with build/runtime config, bounded mod_status/error-log reads and privacy-preserving access-status summaries.
- Add configtest-preflighted graceful reload with dry-run and unknown-outcome reporting.
- Preserve stderr output from Apache commands and report partial probe failures explicitly.
- Prevent error-log reads from resolving into this tool's own audit/config directory.
- Add GitHub CI for tests, lint, security scan and build.

## 0.1.0

- Initial local development version; not published.
