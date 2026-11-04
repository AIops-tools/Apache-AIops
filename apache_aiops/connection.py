"""Bounded Apache control commands and HTTP probe; no shell interpolation."""

from __future__ import annotations

import atexit
import subprocess
import threading
from typing import Any

import httpx

from apache_aiops.config import AppConfig, TargetConfig, load_config

_OUTPUT_MAX = 12000


class ApacheCommandError(Exception):
    pass


class ApacheConnection:
    def __init__(
        self, target: TargetConfig, runner: Any = subprocess.run, client: Any | None = None
    ) -> None:
        self.target = target
        self._run = runner
        self._client = client or httpx.Client(
            timeout=target.timeout, verify=target.verify, follow_redirects=False
        )

    def close(self) -> None:
        self._client.close()

    def command(self, *args: str) -> dict:
        allowed = {("-v",), ("-V",), ("-S",), ("-M",), ("configtest",)}
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

    def probe(self) -> dict:
        if not self.target.probe_url:
            raise ValueError("No probe_url configured for this Apache target.")
        try:
            with self._client.stream("GET", self.target.probe_url) as response:
                return {
                    "url": self.target.probe_url,
                    "statusCode": response.status_code,
                    "healthy": 200 <= response.status_code < 400,
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
