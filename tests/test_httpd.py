"""Apache control-command and HTTP-probe semantics against strict fakes."""

import subprocess

import httpx
import pytest

from apache_aiops.config import TargetConfig
from apache_aiops.connection import ApacheCommandError, ApacheConnection
from apache_aiops.ops import httpd


def _runner(argv, **kwargs):
    assert kwargs["capture_output"] is True and kwargs["check"] is False
    assert isinstance(argv, list)
    values = {
        ("apachectl", "-v"): ("Server version: Apache/2.4.62\n", ""),
        ("apachectl", "configtest"): ("", "Syntax OK\n"),
        ("apachectl", "-S"): ("", "*:80 is a NameVirtualHost\n"),
        ("apachectl", "-M"): ("Loaded Modules:\n proxy_module (shared)\n", ""),
    }
    if tuple(argv) not in values:
        raise AssertionError(f"Unexpected command {argv}")
    stdout, stderr = values[tuple(argv)]
    return subprocess.CompletedProcess(argv, 0, stdout, stderr)


def test_config_and_vhosts_include_stderr_output():
    conn = ApacheConnection(TargetConfig("lab"), runner=_runner)
    assert "Syntax OK" in httpd.config_check(conn)["output"]
    assert "NameVirtualHost" in httpd.vhosts(conn)["output"]


def test_unapproved_command_is_rejected_before_runner():
    conn = ApacheConnection(TargetConfig("lab"), runner=_runner)
    with pytest.raises(ValueError, match="fixed read-only"):
        conn.command("restart")


def test_http_probe_reports_503_as_unhealthy_without_reading_body():
    calls = []

    def handler(request):
        calls.append((request.method, str(request.url)))
        return httpx.Response(503, text="large private response body")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    target = TargetConfig("lab", probe_url="http://127.0.0.1/health")
    conn = ApacheConnection(target, runner=_runner, client=client)
    result = httpd.probe(conn)
    assert result["healthy"] is False
    assert result["statusCode"] == 503
    assert "body" not in result
    assert calls == [("GET", "http://127.0.0.1/health")]


def test_config_failure_is_error_and_diagnosis_is_incomplete():
    def runner(argv, **kwargs):
        if argv == ["apachectl", "configtest"]:
            return subprocess.CompletedProcess(argv, 1, "", "Syntax error on line 3")
        return _runner(argv, **kwargs)

    conn = ApacheConnection(TargetConfig("lab"), runner=runner)
    with pytest.raises(ApacheCommandError, match="Syntax error"):
        httpd.config_check(conn)
    result = httpd.diagnose(conn)
    assert result["complete"] is False
    assert result["failedProbes"] == ["config"]
    assert result["probes"]["config"]["data"] is None


def test_probe_url_cannot_embed_credentials():
    with pytest.raises(ValueError, match="embedded credentials"):
        TargetConfig("lab", probe_url="https://user:secret@example.org/health")
