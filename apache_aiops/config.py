"""Local Apache HTTP Server target configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from apache_aiops.governance.paths import ops_home


@dataclass(frozen=True)
class TargetConfig:
    name: str
    apachectl_bin: str = "apachectl"
    probe_url: str | None = None
    status_url: str | None = None
    error_log: str | None = None
    access_log: str | None = None
    timeout: float = 10.0
    verify_ssl: bool = True
    ca_file: str | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.apachectl_bin or self.apachectl_bin.startswith("-"):
            raise ValueError("name and apachectl_bin are required.")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive.")
        for configured_url in (self.probe_url, self.status_url):
            if not configured_url:
                continue
            url = urlsplit(configured_url)
            if url.scheme not in ("http", "https") or not url.hostname or url.username:
                raise ValueError("Probe/status URL must be HTTP(S) without embedded credentials.")
        for configured_log in (self.error_log, self.access_log):
            if not configured_log:
                continue
            path = Path(configured_log)
            if not path.is_absolute():
                raise ValueError("Log path must be an absolute operator-configured path.")
            if path.resolve().is_relative_to(ops_home().resolve()):
                raise ValueError("Log path cannot read this tool's audit/config directory.")

    @property
    def verify(self) -> bool | str:
        return self.ca_file or True if self.verify_ssl else False


@dataclass(frozen=True)
class AppConfig:
    targets: tuple[TargetConfig, ...] = ()

    def get_target(self, name: str | None = None) -> TargetConfig:
        if name is None:
            if not self.targets:
                raise ValueError("No Apache target configured. Run 'apache-aiops init'.")
            return self.targets[0]
        for target in self.targets:
            if target.name == name:
                return target
        raise KeyError(f"Unknown Apache target '{name}'.")


def load_config(path: Path | None = None) -> AppConfig:
    path = path or Path(os.environ.get("APACHE_AIOPS_CONFIG", ops_home() / "config.yaml"))
    if not path.is_file():
        raise FileNotFoundError(f"No Apache config at {path}. Run 'apache-aiops init'.")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict) or not isinstance(raw.get("targets"), list):
        raise ValueError("Apache config must have a targets list.")
    return AppConfig(tuple(TargetConfig(**entry) for entry in raw["targets"]))
