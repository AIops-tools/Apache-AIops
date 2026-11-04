# Verification — Apache AIops

## Source-backed operations

Apache's [apachectl manual](https://httpd.apache.org/docs/2.4/en/programs/apachectl.html) documents `configtest`. The [virtual-host guide](https://httpd.apache.org/docs/2.4/vhosts/) recommends `apachectl -S` for parsed vhost diagnostics; the [httpd manual](https://httpd.apache.org/docs/2.4/en/programs/httpd.html) documents `-v` and `-M`. Sources checked 2026-11-04. The implementation accepts only these fixed read options.

## Local verification

`tests/test_httpd.py` uses a strict command runner and an HTTPX transport fake. It covers Apache diagnostics printed to stderr, config syntax failure, rejection of an unapproved command, HTTP 503 reporting, and partial diagnosis. Governance invariant tests are copied from the current tool line. The local result is 121 passing tests, Ruff clean, Bandit Medium+ 0, and a successful source/wheel build on 2026-11-04.

## Not yet live verified

No Apache HTTP Server process is available in this environment and Docker's daemon was not running. No real vhost parser output, module listing, reload, TLS deployment or write/undo cycle has been tested. Do not call this production validated or published. The next gate is a disposable Apache 2.4 lab with a malformed vhost, a missing backend and a healthy service, compared to native `apachectl` output.
