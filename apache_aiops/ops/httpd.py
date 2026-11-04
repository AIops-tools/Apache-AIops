"""Read-only Apache HTTP Server diagnosis."""

from __future__ import annotations

from apache_aiops.connection import ApacheConnection


def version(conn: ApacheConnection) -> dict:
    return conn.command("-v")


def build(conn: ApacheConnection) -> dict:
    return conn.command("-V")


def runtime_config(conn: ApacheConnection) -> dict:
    return conn.command("-t", "-D", "DUMP_RUN_CFG")


def server_status(conn: ApacheConnection) -> dict:
    return conn.server_status()


def error_log(conn: ApacheConnection, limit: int = 50) -> dict:
    return conn.error_log(limit)


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
    return {
        "probes": probes,
        "failedProbes": failed,
        "complete": not failed,
        "httpProbeConfigured": bool(conn.target.probe_url),
    }
