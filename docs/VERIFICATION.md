# Verification — Apache AIops

## Source-backed operations

Apache's [apachectl manual](https://httpd.apache.org/docs/2.4/en/programs/apachectl.html) documents `configtest` and `graceful`. The [virtual-host guide](https://httpd.apache.org/docs/2.4/vhosts/) recommends `apachectl -S`; the [httpd manual](https://httpd.apache.org/docs/2.4/en/programs/httpd.html) documents `-v`, `-V`, `-M` and runtime config dumping. The [mod_status guide](https://httpd.apache.org/docs/2.4/mod/mod_status.html) documents `/server-status?auto`. Sources checked 2026-11-04. Read commands use fixed argument lists; graceful is separate and preflighted.

## Local verification

`tests/test_httpd.py` uses a strict command runner, HTTPX transport fake, loopback HTTP server and temporary log. It covers Apache diagnostics printed to stderr, config syntax failure, unapproved-command rejection, HTTP 503, login redirect as unhealthy, mod_status parsing, bounded log reads, dry-run no-write, timeout/nonzero-to-unknown and preflight blocking. Governance invariant tests are copied from the current tool line. Current result: 127 passing tests, Ruff clean, Bandit 0 Medium+ and wheel/sdist build on 2026-11-04. Native `apachectl` 2.4.67 on macOS returned actual version, syntax, virtual-host, module, build and parsed-runtime output. An isolated Apache 2.4.67 process on loopback served a real health page and mod_status metrics; the tool observed both successfully after disabling environment proxy inheritance.

The 0.2.0 wheel was installed into a new environment outside the source tree; `apache_aiops.__file__` resolved under `site-packages`. Its CLI read the isolated service's actual 200 health response and ran a no-write graceful-reload preview that included a real `Syntax OK` preflight.

## Not yet live verified

The isolated lab's graceful reload could not signal its detached parent within the filesystem/process sandbox; the command returned nonzero and the tool correctly marked the outcome unknown. No successful isolated live reload, TLS deployment or write cycle has been tested. Graceful reload has no safe undo without the prior config file. Do not call the package production validated. The next gate is a disposable Apache 2.4 lab with a malformed vhost and a missing backend where graceful reload and recovery can be observed end to end.
