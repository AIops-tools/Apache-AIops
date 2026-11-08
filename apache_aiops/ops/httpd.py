"""Read-only Apache HTTP Server diagnosis."""

from __future__ import annotations

from apache_aiops.connection import ApacheConnection


def version(conn: ApacheConnection) -> dict:
    return conn.command("-v")


def build(conn: ApacheConnection) -> dict:
    return conn.command("-V")


def runtime_config(conn: ApacheConnection) -> dict:
    return conn.command("-t", "-D", "DUMP_RUN_CFG")


def config_includes(conn: ApacheConnection) -> dict:
    return conn.command("-t", "-D", "DUMP_INCLUDES")


def compiled_modules(conn: ApacheConnection) -> dict:
    return conn.command("-l")


def static_directives(conn: ApacheConnection) -> dict:
    return conn.command("-L")


def server_status(conn: ApacheConnection) -> dict:
    return conn.server_status()


def error_log(conn: ApacheConnection, limit: int = 50) -> dict:
    return conn.error_log(limit)


def access_status(conn: ApacheConnection, limit: int = 200) -> dict:
    return conn.access_status(limit)


def config_check(conn: ApacheConnection) -> dict:
    return conn.command("configtest")


def vhosts(conn: ApacheConnection) -> dict:
    return conn.command("-S")


def modules(conn: ApacheConnection) -> dict:
    return conn.command("-M")


def probe(conn: ApacheConnection) -> dict:
    return conn.probe()


def diagnose(conn: ApacheConnection) -> dict:
    probes = {}
    checks = [
        ("version", lambda: version(conn)),
        ("config", lambda: config_check(conn)),
        ("vhosts", lambda: vhosts(conn)),
        ("modules", lambda: modules(conn)),
    ]
    if conn.target.probe_url:
        checks.append(("http", lambda: probe(conn)))
    for name, call in checks:
        try:
            probes[name] = {"data": call(), "error": None}
        except Exception as exc:
            probes[name] = {"data": None, "error": f"{type(exc).__name__}: {exc}"}
    failed = [name for name, result in probes.items() if result["error"] is not None]
    http_data = probes.get("http", {}).get("data")
    unhealthy = (
        ["http"] if isinstance(http_data, dict) and http_data.get("healthy") is False else []
    )
    if unhealthy:
        healthy = False
    elif failed or not isinstance(http_data, dict):
        healthy = None
    else:
        healthy = True if http_data.get("healthy") is True else None
    return {
        "probes": probes,
        "failedProbes": failed,
        "unhealthyProbes": unhealthy,
        "complete": not failed,
        "healthy": healthy,
        "httpProbeConfigured": bool(conn.target.probe_url),
    }
