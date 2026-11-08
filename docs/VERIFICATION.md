# Verification — Apache AIops

## Source-backed operations

Apache's [apachectl manual](https://httpd.apache.org/docs/2.4/en/programs/apachectl.html) documents `configtest` and `graceful`. The [virtual-host guide](https://httpd.apache.org/docs/2.4/vhosts/) recommends `apachectl -S`; the [httpd manual](https://httpd.apache.org/docs/2.4/en/programs/httpd.html) documents `-v`, `-V`, `-M`, `-l`, `-L` and runtime config dumping. Apache upstream [source](https://github.com/apache/httpd/blob/trunk/server/main.c) explicitly handles `DUMP_INCLUDES`; native 2.4.67 on this machine also produced the include tree. The [mod_status guide](https://httpd.apache.org/docs/2.4/mod/mod_status.html) documents `/server-status?auto`. The [Apache log guide](https://httpd.apache.org/docs/2.4/en/logs.html) defines common and combined access formats and notes that custom formats are possible; the new summary reports `unparsedLines` and sample parse completeness instead of treating unknown formats as zero. Sources checked 2026-11-04. Read commands use fixed argument lists; graceful is separate and preflighted.

## Local verification

`tests/test_httpd.py` uses a strict command runner, HTTPX transport fake, loopback HTTP server and temporary log. It covers Apache diagnostics printed to stderr, config syntax failure, unapproved-command rejection, HTTP 503, login redirect as unhealthy, mod_status parsing, bounded log reads, privacy-safe access status parsing, escaped-quote protection, refusal to read its own audit directory even after a symlink changes, dry-run no-write, timeout/nonzero-to-unknown and preflight blocking. Governance invariant tests are copied from the current tool line. Current result: 134 passing tests, Ruff clean, Bandit 0 Medium+ and wheel/sdist build, rerun on 2026-11-05. Native `apachectl` 2.4.67 on macOS returned actual version, syntax, virtual-host, loaded/compiled module, static directive, include tree, build and parsed-runtime output. An isolated Apache 2.4.67 process on loopback served a real health page and mod_status metrics; the tool observed both successfully after disabling environment proxy inheritance.

The current 0.2.0 candidate wheel was rebuilt and installed into a new environment outside the source tree; its MCP registry reports 17 tools. Its `access-status` CLI parsed a sample common log from an operator-selected path and returned only status codes/counts, with no raw IP, URL or token. Its CLI read actual native 2.4.67 compiled modules, include tree and static directives; large directive output reported truncation. An earlier 0.2.0 candidate wheel was also installed outside the source tree; `apache_aiops.__file__` resolved under `site-packages`. Its CLI read the isolated service's actual 200 health response and ran a no-write graceful-reload preview that included a real `Syntax OK` preflight.

## Disposable Linux VM verification (2026-11-08)

An isolated Debian container on the `Open-test` Ubuntu VM ran Apache 2.4.69
with the 0.2.0 wheel installed. The CLI read its real version, `Syntax OK`,
`mod_status` metrics and access-log status counts; the health page returned
HTTP 200. A graceful-reload preview changed nothing. The real command was
accepted, and the independent `mod_status` configuration generation increased
from 1 to 2 while health stayed 200. The tool still reported `unknown`, which
is truthful because a successful command and probe do not prove every worker
loaded the new configuration.

An intentionally invalid directive made `config-check` fail and blocked reload;
the configuration generation stayed at 2. After removing it, a valid proxy
rule pointing to an absent backend produced a real HTTP 503. `probe` reported
`healthy: false`. This live run exposed that `diagnose` had returned
`failedProbes: []` and `complete: true` without an overall health verdict.
`diagnose` now also returns `unhealthyProbes: ["http"]` and `healthy: false`
for this case; its regression tests failed before the fix and pass now. The
proxy rule was removed and the health page returned 200 again. Current suite:
136 passing tests, Ruff clean, Bandit 0 Medium+ and wheel/sdist build.

## Still not live verified

The earlier macOS isolated lab could not signal its detached Apache parent;
the Linux container run above closed that gap. Production access-log formats,
TLS deployments and behavior across a live fleet remain untested. Graceful
reload has no safe undo without the prior config file. This disposable lab
run does not establish production readiness.
