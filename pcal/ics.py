"""Build RFC 5545 iCalendar METHOD:PUBLISH events Proton Calendar accepts."""
from __future__ import annotations

from datetime import datetime, timezone

from pcal.validate import EventSpec


def _escape(text: str) -> str:
  return (
    text.replace("\\", "\\\\")
    .replace(";", r"\;")
    .replace(",", r"\,")
    .replace("\r\n", r"\n")
    .replace("\n", r"\n")
    .replace("\r", r"\n")
  )


def _fold(line: str) -> str:
  # RFC 5545 §3.1: lines SHOULD be folded at 75 octets; continuation starts with space.
  if len(line.encode("utf-8")) <= 75: return line
  out: list[str] = []
  buf = ""
  for ch in line:
    candidate = buf + ch
    if len(candidate.encode("utf-8")) > 75:
      out.append(buf)
      buf = " " + ch
    else:
      buf = candidate
  if buf: out.append(buf)
  return "\r\n".join(out)


def _fmt_local(dt: datetime) -> str:
  return dt.strftime("%Y%m%dT%H%M%S")


def _fmt_date(dt: datetime) -> str:
  return dt.strftime("%Y%m%d")


def _fmt_utc(dt: datetime) -> str:
  return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_invite_ics(
  event: EventSpec,
  *,
  uid: str,
  organizer_email: str,
  organizer_name: str | None,
  dtstamp: datetime | None = None,
) -> str:
  stamp = dtstamp or datetime.now(timezone.utc)
  lines = [
    "BEGIN:VCALENDAR",
    "PRODID:-//pcal//EN",
    "VERSION:2.0",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "BEGIN:VEVENT",
    f"UID:{uid}",
    f"DTSTAMP:{_fmt_utc(stamp)}",
  ]
  if event.all_day:
    lines.append(f"DTSTART;VALUE=DATE:{_fmt_date(event.start)}")
    lines.append(f"DTEND;VALUE=DATE:{_fmt_date(event.end)}")
  else:
    lines.extend([
      f"DTSTART;TZID={event.timezone}:{_fmt_local(event.start)}",
      f"DTEND;TZID={event.timezone}:{_fmt_local(event.end)}",
    ])
  lines.append(f"SUMMARY:{_escape(event.title)}")
  if event.description:
    lines.append(f"DESCRIPTION:{_escape(event.description)}")
  if event.location:
    lines.append(f"LOCATION:{_escape(event.location)}")
  if event.rrule:
    lines.append(f"RRULE:{event.rrule.strip()}")
  if organizer_name:
    lines.append(f"ORGANIZER;CN={_escape(organizer_name)}:mailto:{organizer_email}")
  else:
    lines.append(f"ORGANIZER:mailto:{organizer_email}")
  lines.extend(["STATUS:CONFIRMED", "SEQUENCE:0", "TRANSP:OPAQUE", "END:VEVENT", "END:VCALENDAR", ""])
  return "\r\n".join(_fold(line) for line in lines)
