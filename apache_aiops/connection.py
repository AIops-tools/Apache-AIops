"""Bounded Apache control commands and HTTP probe; no shell interpolation."""

from __future__ import annotations

import atexit
import subprocess
import threading
from pathlib import Path
from typing import Any

import httpx

from apache_aiops.config import AppConfig, TargetConfig, load_config

_OUTPUT_MAX = 12000


class ApacheCommandError(Exception):
    pass


class ApacheWriteUncertainError(ApacheCommandError):
    """Graceful restart may have reached Apache before the response was lost."""


class ApacheConnection:
    def __init__(
        self, target: TargetConfig, runner: Any = subprocess.run, client: Any | None = None
    ) -> None:
        self.target = target
        self._run = runner
        self._client = client or httpx.Client(
            timeout=target.timeout, verify=target.verify, follow_redirects=False,
            trust_env=False,
        )

    def close(self) -> None:
        self._client.close()

    def command(self, *args: str) -> dict:
        allowed = {("-v",), ("-V",), ("-S",), ("-M",), ("-l",), ("-L",),
                   ("configtest",), ("-t", "-D", "DUMP_RUN_CFG"),
                   ("-t", "-D", "DUMP_INCLUDES")}
        if args not in allowed:
            raise ValueError("Only fixed read-only apachectl options are supported.")
        argv = [self.target.apachectl_bin, *args]
        try:
            result = self._run(
                argv, capture_output=True, text=True, timeout=self.target.timeout, check=False
            )
        except FileNotFoundError as exc:
            raise ApacheCommandError(
                f"Missing '{argv[0]}'; install Apache HTTP Server or configure its path."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ApacheCommandError(
                f"Apache command timed out after {self.target.timeout:g}s."
            ) from exc
        combined = "\n".join(part for part in (result.stdout, result.stderr) if part)
        if result.returncode != 0:
            raise ApacheCommandError(
                f"apachectl {' '.join(args)} failed (exit {result.returncode}): {combined[:800]}"
            )
        return {
            "output": combined[:_OUTPUT_MAX] + ("…" if len(combined) > _OUTPUT_MAX else ""),
            "truncated": len(combined) > _OUTPUT_MAX,
        }

    def graceful(self) -> dict:
        argv = [self.target.apachectl_bin, "graceful"]
        try:
            result = self._run(
                argv, capture_output=True, text=True, timeout=self.target.timeout, check=False
            )
        except FileNotFoundError as exc:
            raise ApacheCommandError(f"Missing '{argv[0]}'.") from exc
        except subprocess.TimeoutExpired as exc:
            raise ApacheWriteUncertainError(
                "Apache graceful reload timed out; it may have run."
            ) from exc
        if result.returncode != 0:
            raise ApacheWriteUncertainError(
                f"Apache graceful reload returned exit {result.returncode}; check state: "
                f"{(result.stderr or result.stdout or '')[:800]}"
            )
        return {"output": (result.stdout or result.stderr or "")[:800]}

    def server_status(self) -> dict:
        if not self.target.status_url:
            raise ValueError("No status_url configured for this Apache target.")
        try:
            with self._client.stream("GET", self.target.status_url) as response:
                if response.status_code != 200:
                    raise ApacheCommandError(
                        f"Apache mod_status returned HTTP {response.status_code}."
                    )
                chunks = bytearray()
                truncated = False
                for chunk in response.iter_bytes():
                    chunks.extend(chunk[: max(0, 16385 - len(chunks))])
                    if len(chunks) > 16384:
                        truncated = True
                        break
                lines = chunks[:16384].decode("utf-8", errors="replace").splitlines()
                fields = {}
                for line in lines:
                    if ": " in line:
                        key, value = line.split(": ", 1)
                        fields[key] = value
                known = {"BusyWorkers", "IdleWorkers", "Total Accesses", "Scoreboard"}
                if not known & fields.keys():
                    raise ApacheCommandError(
                        "Apache status URL did not return mod_status auto data."
                    )
                return {"fields": fields, "truncated": truncated, "url": self.target.status_url}
        except httpx.HTTPError as exc:
            raise ApacheCommandError(f"Apache status probe failed: {type(exc).__name__}.") from exc

    def error_log(self, limit: int = 50) -> dict:
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200.")
        if not self.target.error_log:
            raise ValueError("No error_log configured for this Apache target.")
        path = Path(self.target.error_log)
        with path.open("rb") as stream:
            size = stream.seek(0, 2)
            start = max(0, size - 65536)
            stream.seek(start)
            raw = stream.read(65536)
        lines = raw.decode("utf-8", errors="replace").splitlines()
        if start and lines:
            lines = lines[1:]
        selected = lines[-limit:]
        return {
            "items": [{"line": line[:800] + ("…" if len(line) > 800 else "")}
                      for line in selected],
            "returned": len(selected), "limit": limit,
            "truncated": bool(start or len(lines) > limit or any(len(x) > 800 for x in selected)),
        }

    def probe(self) -> dict:
        if not self.target.probe_url:
            raise ValueError("No probe_url configured for this Apache target.")
        try:
            with self._client.stream("GET", self.target.probe_url) as response:
                return {
                    "url": self.target.probe_url,
                    "statusCode": response.status_code,
                    "healthy": 200 <= response.status_code < 300,
                    "location": response.headers.get("location"),
                }
        except httpx.ConnectTimeout as exc:
            raise ApacheCommandError(
                "Could not connect to the configured Apache probe URL."
            ) from exc
        except httpx.TimeoutException as exc:
            raise ApacheCommandError(
                "Apache HTTP probe timed out; inspect the service and backend."
            ) from exc
        except httpx.HTTPError as exc:
            raise ApacheCommandError(f"Apache HTTP probe failed: {type(exc).__name__}.") from exc


class ConnectionManager:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()
        self._connections: dict[str, ApacheConnection] = {}
        self._lock = threading.Lock()
        atexit.register(self.close)

    def connect(self, target: str | None = None) -> ApacheConnection:
        chosen = self.config.get_target(target)
        with self._lock:
            if chosen.name not in self._connections:
                self._connections[chosen.name] = ApacheConnection(chosen)
            return self._connections[chosen.name]

    def close(self) -> None:
        with self._lock:
            for connection in self._connections.values():
                connection.close()
            self._connections.clear()
