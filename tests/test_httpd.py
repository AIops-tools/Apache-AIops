"""Apache control-command and HTTP-probe semantics against strict fakes."""

import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest
import yaml
from typer.testing import CliRunner

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


def test_new_fixed_read_commands_have_no_shell_or_dynamic_arguments():
    seen = []

    def runner(argv, **kwargs):
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, "details\n", "")

    conn = ApacheConnection(TargetConfig("lab"), runner=runner)
    assert httpd.config_includes(conn)["output"] == "details\n"
    httpd.compiled_modules(conn)
    httpd.static_directives(conn)
    assert seen == [
        ["apachectl", "-t", "-D", "DUMP_INCLUDES"],
        ["apachectl", "-l"], ["apachectl", "-L"],
    ]
    with pytest.raises(ValueError, match="fixed read-only"):
        conn.command("-D", "DUMP_INCLUDES; bad")


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


def test_http_probe_does_not_call_login_redirect_healthy():
    client = httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(302, headers={"Location": "/login"})))
    target = TargetConfig("lab", probe_url="http://127.0.0.1/health")
    result = ApacheConnection(target, runner=_runner, client=client).probe()
    assert result["statusCode"] == 302
    assert result["healthy"] is False
    assert result["location"] == "/login"


def test_diagnose_names_an_unhealthy_http_probe_even_when_all_probes_return():
    client = httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(503)))
    conn = ApacheConnection(
        TargetConfig("lab", probe_url="http://127.0.0.1/health"),
        runner=_runner, client=client,
    )
    result = httpd.diagnose(conn)
    assert result["complete"] is True
    assert result["failedProbes"] == []
    assert result["unhealthyProbes"] == ["http"]
    assert result["healthy"] is False


def test_diagnose_without_http_probe_does_not_claim_service_health():
    result = httpd.diagnose(ApacheConnection(TargetConfig("lab"), runner=_runner))
    assert result["complete"] is True
    assert result["healthy"] is None


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


def test_mod_status_is_bounded_and_rejects_html():
    def handler(request):
        assert str(request.url) == "http://127.0.0.1/server-status?auto"
        return httpx.Response(200, text="BusyWorkers: 3\nIdleWorkers: 7\n")

    target = TargetConfig("lab", status_url="http://127.0.0.1/server-status?auto")
    conn = ApacheConnection(target, runner=_runner,
                            client=httpx.Client(transport=httpx.MockTransport(handler)))
    result = conn.server_status()
    assert result["fields"] == {"BusyWorkers": "3", "IdleWorkers": "7"}
    assert result["truncated"] is False

    html = httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, text="Host: fake status page\n")))
    with pytest.raises(ApacheCommandError, match="mod_status"):
        ApacheConnection(target, runner=_runner, client=html).server_status()


def test_error_log_only_reads_configured_path_and_reports_truncation(tmp_path):
    path = tmp_path / "error.log"
    path.write_text("\n".join(f"line {i}" for i in range(10)))
    conn = ApacheConnection(TargetConfig("lab", error_log=str(path)), runner=_runner)
    assert conn.error_log(limit=2) == {
        "items": [{"line": "line 8"}, {"line": "line 9"}],
        "returned": 2, "limit": 2, "truncated": True,
    }
    with pytest.raises(ValueError, match="absolute"):
        TargetConfig("lab", error_log="../secret")


def test_access_status_summarizes_common_log_without_exposing_requests(tmp_path):
    path = tmp_path / "access.log"
    path.write_text(
        '192.0.2.1 - user [10/Oct/2000:13:55:36 -0700] "GET /?token=secret HTTP/1.1" 200 42\n'
        '192.0.2.2 - - [10/Oct/2000:13:56:36 -0700] "POST /private HTTP/1.1" 503 10 '
        '"https://ref.example/" "agent"\n'
        'custom format with private data\n'
    )
    conn = ApacheConnection(TargetConfig("lab", access_log=str(path)), runner=_runner)
    result = conn.access_status(limit=3)
    assert result["items"] == [{"statusCode": 200}, {"statusCode": 503}]
    assert result["returned"] == 2 and result["unparsedLines"] == 1
    assert result["sampleParseComplete"] is False
    assert result["statusClasses"]["5xx"] == 1
    assert "secret" not in str(result) and "192.0.2.1" not in str(result)
    assert conn.access_status(limit=1)["truncated"] is True
    with pytest.raises(ValueError, match="absolute"):
        TargetConfig("lab", access_log="../private")


def test_access_status_ignores_escaped_quote_and_fake_status_inside_request(tmp_path):
    path = tmp_path / "access.log"
    path.write_text(
        '192.0.2.1 - - [10/Oct/2000:13:55:36 -0700] '
        '"GET /\\" 503 / HTTP/1.1" 200 42\n'
    )
    result = ApacheConnection(TargetConfig("lab", access_log=str(path))).access_status()
    assert result["items"] == [{"statusCode": 200}]
    assert result["statusClasses"]["5xx"] == 0


def test_access_status_marks_bounded_tail_as_truncated(tmp_path):
    path = tmp_path / "access.log"
    path.write_text(
        "x" * 70000 + "\n"
        '192.0.2.1 - - [10/Oct/2000:13:55:36 -0700] "GET / HTTP/1.1" 503 4\n'
    )
    result = ApacheConnection(TargetConfig("lab", access_log=str(path))).access_status()
    assert result["items"] == [{"statusCode": 503}]
    assert result["truncated"] is True


def test_log_symlink_swapped_into_audit_home_is_rejected_at_read(monkeypatch, tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "audit.db").write_text("private")
    original = tmp_path / "access.log"
    original.write_text("safe")
    link = tmp_path / "current.log"
    link.symlink_to(original)
    monkeypatch.setenv("APACHE_AIOPS_HOME", str(state))
    conn = ApacheConnection(TargetConfig("lab", access_log=str(link)), runner=_runner)
    link.unlink()
    link.symlink_to(state / "audit.db")
    with pytest.raises(ValueError, match="audit/config"):
        conn.access_status()


def test_init_records_operator_selected_status_and_log_paths(monkeypatch, tmp_path):
    from apache_aiops.cli import app

    monkeypatch.setenv("APACHE_AIOPS_HOME", str(tmp_path / "state"))
    supplied = "lab\nhttp://127.0.0.1/health\nhttp://127.0.0.1/status?auto\n"
    supplied += f"{tmp_path}/error.log\n{tmp_path}/access.log\n"
    result = CliRunner().invoke(app, ["init"], input=supplied)
    assert result.exit_code == 0, result.output
    target = yaml.safe_load((tmp_path / "state" / "config.yaml").read_text())["targets"][0]
    assert target["status_url"] == "http://127.0.0.1/status?auto"
    assert target["access_log"] == str(tmp_path / "access.log")


def test_error_log_refuses_own_audit_directory_even_through_symlink(monkeypatch, tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "audit.db").write_text("private")
    link = tmp_path / "linked-audit"
    link.symlink_to(state / "audit.db")
    monkeypatch.setenv("APACHE_AIOPS_HOME", str(state))
    with pytest.raises(ValueError, match="audit/config"):
        TargetConfig("lab", error_log=str(link))


def test_graceful_reload_preflights_and_reports_unknown(monkeypatch, tmp_path):
    from apache_aiops.governance.audit import reset_engine
    from apache_aiops.mcp_server.tools import httpd as tools

    seen = []

    def runner(argv, **kwargs):
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, "Syntax OK", "")

    conn = ApacheConnection(TargetConfig("lab"), runner=runner)
    monkeypatch.setattr(tools, "_get_connection", lambda target=None: conn)
    monkeypatch.setenv("APACHE_AIOPS_HOME", str(tmp_path))
    reset_engine()
    try:
        assert tools.apache_graceful_reload(dry_run=True)["dryRun"] is True
        assert ["apachectl", "graceful"] not in seen
        result = tools.apache_graceful_reload()
        assert result["outcomeUnknown"] is True
        assert ["apachectl", "graceful"] in seen
    finally:
        reset_engine()


def test_graceful_timeout_unknown_but_syntax_error_blocks_write(monkeypatch, tmp_path):
    from apache_aiops.governance.audit import reset_engine
    from apache_aiops.mcp_server.tools import httpd as tools

    failure = "timeout"
    seen = []

    def runner(argv, **kwargs):
        seen.append(argv)
        if argv == ["apachectl", "configtest"] and failure == "syntax":
            return subprocess.CompletedProcess(argv, 1, "", "Syntax error")
        if argv == ["apachectl", "graceful"]:
            if failure == "exit-nonzero":
                return subprocess.CompletedProcess(argv, 1, "", "signal maybe sent")
            raise subprocess.TimeoutExpired(argv, 10)
        return subprocess.CompletedProcess(argv, 0, "Syntax OK", "")

    conn = ApacheConnection(TargetConfig("lab"), runner=runner)
    monkeypatch.setattr(tools, "_get_connection", lambda target=None: conn)
    monkeypatch.setenv("APACHE_AIOPS_HOME", str(tmp_path))
    reset_engine()
    try:
        assert tools.apache_graceful_reload()["outcomeUnknown"] is True
        failure = "exit-nonzero"
        assert tools.apache_graceful_reload()["outcomeUnknown"] is True
        failure = "syntax"
        seen.clear()
        result = tools.apache_graceful_reload()
        assert "Syntax error" in result["error"]
        assert ["apachectl", "graceful"] not in seen
    finally:
        reset_engine()


def test_operator_loopback_probe_bypasses_environment_proxy(monkeypatch):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"healthy")

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("ALL_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("NO_PROXY", "")
    try:
        target = TargetConfig("lab", probe_url=f"http://127.0.0.1:{server.server_port}/health")
        conn = ApacheConnection(target, runner=_runner)
        assert conn.probe()["statusCode"] == 200
        conn.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
