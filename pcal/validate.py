"""Turn agent JSON into a validated event (title + start required; end defaults to +1 hour)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class ValidationError(Exception):
  pass


@dataclass(frozen=True)
class EventSpec:
  title: str
  start: datetime
  end: datetime
  timezone: str
  location: str | None
  description: str | None
  rrule: str | None
  all_day: bool


def _parse_dt(value: object, label: str, tz: ZoneInfo) -> datetime:
  if not isinstance(value, str) or not value.strip():
    raise ValidationError(f"Missing or invalid {label}.")
  text = value.strip()
  if text.endswith("Z"): text = text[:-1] + "+00:00"
  try:
    dt = datetime.fromisoformat(text)
  except ValueError as exc:
    raise ValidationError(f"Could not parse {label} as a date/time: {value!r}") from exc
  if dt.tzinfo is None: return dt.replace(tzinfo=tz)
  return dt.astimezone(tz)


def _parse_bool(value: object, key: str, *, default: bool = False) -> bool:
  if value in (None, ""):
    return default
  if not isinstance(value, bool):
    raise ValidationError(f"{key} must be a boolean when provided.")
  return value


def _is_date_only(value: object) -> bool:
  if not isinstance(value, str):
    return False
  text = value.strip()
  return "T" not in text and len(text) == 10


def validate_event(data: dict, *, default_tz: str) -> EventSpec:
  if not isinstance(data, dict):
    raise ValidationError("Event payload must be a JSON object.")
  if isinstance(data.get("error"), str) and data["error"].strip():
    raise ValidationError(data["error"].strip())

  title = data.get("title")
  if not isinstance(title, str) or not title.strip():
    raise ValidationError(
      "Not enough information: need at least an event title and a start date/time."
    )

  tz_name = data.get("timezone") or default_tz
  if not isinstance(tz_name, str) or not tz_name.strip():
    raise ValidationError("Timezone is missing.")
  tz_name = tz_name.strip()
  try:
    tz = ZoneInfo(tz_name)
  except ZoneInfoNotFoundError as exc:
    raise ValidationError(f"Unknown timezone: {tz_name}") from exc

  if data.get("start") in (None, ""):
    raise ValidationError(
      "Not enough information: need a start date/time (for example 'tomorrow at 7 PM')."
    )
  start = _parse_dt(data.get("start"), "start", tz)
  all_day = _parse_bool(data.get("all_day"), "all_day") or _is_date_only(data.get("start"))

  end_raw = data.get("end")
  duration = data.get("duration_minutes")
  if all_day:
    if end_raw not in (None, ""):
      end = _parse_dt(end_raw, "end", tz)
    else:
      end = start + timedelta(days=1)
    if end <= start:
      raise ValidationError("End date must be after start date.")
  elif end_raw not in (None, ""):
    end = _parse_dt(end_raw, "end", tz)
    if end <= start:
      raise ValidationError("End time must be after start time.")
  else:
    minutes = 60
    if duration not in (None, ""):
      if isinstance(duration, bool) or not isinstance(duration, (int, float)):
        raise ValidationError("duration_minutes must be a number.")
      minutes = int(duration)
      if minutes <= 0:
        raise ValidationError("duration_minutes must be positive.")
    end = start + timedelta(minutes=minutes)
    if end <= start:
      raise ValidationError("End time must be after start time.")

  def opt(key: str) -> str | None:
    val = data.get(key)
    if val in (None, ""): return None
    if not isinstance(val, str):
      raise ValidationError(f"{key} must be a string when provided.")
    text = val.strip()
    return text or None

  return EventSpec(
    title=title.strip(),
    start=start,
    end=end,
    timezone=tz_name,
    location=opt("location"),
    description=opt("description"),
    rrule=opt("rrule"),
    all_day=all_day,
  )
