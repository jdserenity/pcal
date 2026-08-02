"""pcal CLI: natural-language → Cursor Agent → ICS invite via Proton Mail Bridge SMTP."""
from __future__ import annotations

import argparse
import os
import sys
import traceback
import uuid
from datetime import datetime
from pathlib import Path

from pcal.agent_parse import AgentParseError, parse_event_with_agent
from pcal.config import ConfigError, default_config_path, load_config, require_smtp, write_example_config
from pcal.ics import build_invite_ics
from pcal.mail import send_invite
from pcal.validate import ValidationError, validate_event


def local_timezone_name() -> str:
  tz = datetime.now().astimezone().tzinfo
  key = getattr(tz, "key", None)
  if isinstance(key, str) and key: return key
  path = Path("/etc/localtime")
  try:
    target = os.path.realpath(path)
    marker = f"{os.sep}zoneinfo{os.sep}"
    if marker in target: return target.split(marker, 1)[1]
  except OSError:
    pass
  return "UTC"


def example_config_src() -> Path:
  return Path(__file__).resolve().parent.parent / "config.example.toml"


def build_parser() -> argparse.ArgumentParser:
  p = argparse.ArgumentParser(
    prog="pcal",
    description="Create a Proton Calendar event from natural language via a calendar invitation email.",
  )
  p.add_argument("request", nargs="*", help="Natural-language event description") # This isn't a --request flag, this is just whatever the request is. Using nargs="*" allows flexible input (multiple words). Naming helps reference this argument in code (e.g., args.request).
  p.add_argument("--init", action="store_true", help="Write ~/.config/pcal/config.toml from the example")
  p.add_argument("--dry-run", action="store_true", help="Parse and print the ICS; do not send email")
  p.add_argument("--config", type=Path, default=None, help="Path to config.toml")
  return p


def main(argv: list[str] | None = None) -> int:
  argv = sys.argv[1:] if argv is None else argv
  parser = build_parser()
  args = parser.parse_args(argv)

  if args.init:
    dest = args.config or default_config_path()
    try:
      write_example_config(dest, example_config_src())
    except ConfigError as exc:
      print(f"pcal: {exc}", file=sys.stderr)
      return 1
    print(f"Wrote {dest}")
    print("Edit it with your Proton address and the SMTP password from Proton Mail Bridge.")
    return 0

  request = " ".join(args.request).strip()
  if not request:
    print("pcal: pass an event description, e.g. pcal \"Dinner tomorrow at 7 PM\"", file=sys.stderr)
    return 2

  try:
    cfg = load_config(args.config)
  except ConfigError as exc:
    print(f"pcal: {exc}", file=sys.stderr)
    return 1

  default_tz = cfg.timezone or local_timezone_name()
  now_iso = datetime.now().astimezone().isoformat(timespec="seconds")

  try:
    payload = parse_event_with_agent(request, now_iso=now_iso, default_tz=default_tz)
    event = validate_event(payload, default_tz=default_tz)
  except (AgentParseError, ValidationError) as exc:
    print(f"pcal: {exc}", file=sys.stderr)
    return 1
  except Exception as exc:
    print(f"pcal: unexpected parse failure: {exc}", file=sys.stderr)
    if os.environ.get("PCAL_DEBUG"): traceback.print_exc()
    return 1

  uid = f"{uuid.uuid4()}@pcal"
  ics = build_invite_ics(
    event,
    uid=uid,
    organizer_email=cfg.from_email,
    organizer_name=cfg.from_name,
    attendee_email=cfg.to_email,
  )

  when = f"{event.start.strftime('%Y-%m-%d %H:%M')}–{event.end.strftime('%H:%M')} {event.timezone}"
  print(f"Event: {event.title}")
  print(f"When:  {when}")
  if event.location: print(f"Where: {event.location}")
  if event.rrule: print(f"Repeat: {event.rrule}")

  if args.dry_run:
    print("--- ICS ---")
    print(ics)
    return 0

  try:
    require_smtp(cfg)
  except ConfigError as exc:
    print(f"pcal: {exc}", file=sys.stderr)
    return 1

  try:
    send_invite(
      event=event,
      ics_body=ics,
      from_email=cfg.from_email,
      from_name=cfg.from_name,
      to_email=cfg.to_email,
      smtp_host=cfg.smtp_host,
      smtp_port=cfg.smtp_port,
      smtp_user=cfg.smtp_user,
      smtp_password=cfg.smtp_password,
    )
  except Exception as exc:
    print(
      f"pcal: failed to send via SMTP ({cfg.smtp_host}:{cfg.smtp_port}): {exc}\n"
      "Is Proton Mail Bridge running and are smtp_user / smtp_password correct?",
      file=sys.stderr,
    )
    return 1

  print(f"Invitation sent to {cfg.to_email}. Accept it in Proton Calendar to add the event.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
