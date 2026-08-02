"""Load pcal settings from ~/.config/pcal/config.toml (credentials stay out of the repo)."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

if sys.version_info >= (3, 11):
  import tomllib
else:
  try: import tomllib
  except ImportError: import tomli as tomllib  # type: ignore


class ConfigError(Exception):
  pass


@dataclass(frozen=True) # a frozen dataclass's fields are immutable after creation.
class Config:
  from_email: str
  to_email: str
  from_name: str | None
  smtp_host: str
  smtp_port: int
  smtp_user: str
  smtp_password: str
  timezone: str | None
  path: Path


def default_config_path() -> Path:
  return Path(os.environ.get("PCAL_CONFIG", Path.home() / ".config" / "pcal" / "config.toml"))


def load_config(path: Path | None = None) -> Config:
  path = path or default_config_path()
  if not path.is_file():
    raise ConfigError(
      f"Missing config file: {path}\n"
      "Run: pcal --init\n"
      "Then edit that file with your Proton address and Bridge SMTP password."
    )
  try:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
  except Exception as exc:
    raise ConfigError(f"Could not read config {path}: {exc}") from exc

  def req(key: str) -> str:
    val = data.get(key)
    if not isinstance(val, str) or not val.strip():
      raise ConfigError(f"Config {path} is missing required string field: {key}")
    return val.strip()

  password = os.environ.get("PCAL_SMTP_PASSWORD") or data.get("smtp_password")
  password_ok = isinstance(password, str) and bool(password.strip())

  host = data.get("smtp_host", "127.0.0.1")
  port = data.get("smtp_port", 1025)
  if not isinstance(host, str) or not host.strip():
    raise ConfigError("smtp_host must be a non-empty string")
  if not isinstance(port, int) or port <= 0:
    raise ConfigError("smtp_port must be a positive integer")

  tz = data.get("timezone")
  if tz is not None and (not isinstance(tz, str) or not tz.strip()):
    raise ConfigError("timezone must be a non-empty string when set")
  name = data.get("from_name")
  if name is not None and not isinstance(name, str):
    raise ConfigError("from_name must be a string when set")

  smtp_user = data.get("smtp_user")
  if not isinstance(smtp_user, str) or not smtp_user.strip():
    smtp_user = ""

  return Config(
    from_email=req("from_email"),
    to_email=req("to_email"),
    from_name=(name.strip() if isinstance(name, str) and name.strip() else None),
    smtp_host=host.strip(),
    smtp_port=port,
    smtp_user=smtp_user.strip(),
    smtp_password=(password.strip() if password_ok else ""),
    timezone=(tz.strip() if isinstance(tz, str) else None),
    path=path,
  )


def require_smtp(cfg: Config) -> None:
  if not cfg.smtp_user:
    raise ConfigError(f"Config {cfg.path} is missing required string field: smtp_user")
  if not cfg.smtp_password:
    raise ConfigError(
      f"Config {cfg.path} needs smtp_password (or set PCAL_SMTP_PASSWORD in the environment)."
    )


def write_example_config(dest: Path, example_src: Path) -> None: # This is used by the CLI's --init command to create a config file from an example
  dest.parent.mkdir(parents=True, exist_ok=True)
  if not example_src.is_file():
    raise ConfigError(f"Example config not found: {example_src}")
  if dest.exists():
    raise ConfigError(f"Config already exists: {dest}")
  dest.write_text(example_src.read_text(encoding="utf-8"), encoding="utf-8")
  dest.chmod(0o600)
