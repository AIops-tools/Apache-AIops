---
name: apache-aiops
slug: apache-aiops
displayName: "Apache AIops"
summary: "Governed Apache HTTP Server config, virtual-host, module and HTTP diagnosis."
license: MIT
homepage: https://github.com/AIops-tools/Apache-AIops
tags: [aiops, mcp, governance, apache, httpd]
description: >
  Use this skill when a user needs to inspect or diagnose an Apache HTTP Server instance, verify config syntax, inspect parsed virtual hosts and modules, or check an operator-configured HTTP health URL. This first slice is read-only and requires local apachectl access.
installer:
  kind: uv
  package: apache-aiops
argument-hint: "[Apache target or vhost symptom]"
allowed-tools:
  - Bash
metadata: {"openclaw":{"requires":{"anyBins":["uvx"]},"optional":{"env":["APACHE_AIOPS_CONFIG"]},"homepage":"https://github.com/AIops-tools/Apache-AIops","emoji":"🪶","os":["macos","linux"]}}
---

# Apache AIops

Start with `apache-aiops diagnose` for version, syntax, virtual hosts, modules and optional HTTP status. Use `apache-aiops vhosts` when a request reaches the wrong site, and `apache-aiops config-check` when a reload fails. `apache-aiops init` configures a local target; `apache-aiops doctor` checks `apachectl` access.

Read `failedProbes` and `complete` before summarizing results. An unconfigured HTTP probe is reported as `httpProbeConfigured: false`; do not infer that the service is responding. The MCP server registers 6 Apache read tools plus `undo_list` and `undo_apply`; this version records no Apache undo token. See [guardrails](references/agent-guardrails.md) and [capabilities](references/capabilities.md).
