# Apache AIops agent guardrails

| Enforced in code | Location |
|---|---|
| Every MCP tool is audited, budgeted and risk annotated. | `governance/decorators.py`, `mcp_server/_annotations.py` |
| Only fixed read-only `apachectl` argument sets are accepted, and no shell is used. | `connection.py:command` |
| The HTTP probe URL is configured by the operator; the agent cannot choose a URL. | `config.py:TargetConfig`, `mcp_server/tools/httpd.py` |
| HTTP probe reads headers and status without returning a body. | `connection.py:probe` |
| A failed diagnostic probe remains an error with `data: null`. | `ops/httpd.py:diagnose` |

A successful `configtest` proves syntax, not that upstream application backends are healthy. A missing HTTP probe is an unperformed check. No Apache write is available in this first slice.
