# Security

Report vulnerabilities privately through the repository's GitHub security advisory flow when available. Do not post private virtual-host names, configuration dumps, credentials or health URLs in public issues.

Read commands accept only fixed `apachectl` options; the fixed `graceful` write first runs `configtest`. Commands execute as argument lists without a shell. The process account's permissions control which configuration and operator-selected error log it can inspect. HTTP probe and status URLs come from operator configuration, never agent parameters. The health probe does not return a body; `mod_status` output is bounded. TLS validation is enabled by default. Graceful reload has dry-run, CLI double confirmation and an unknown final outcome until checked.
