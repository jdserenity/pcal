"""Ask Cursor Agent (Composer 2.5, headless ask mode) to turn NL into event JSON."""
from __future__ import annotations

import json
import re
import shutil
import subprocess


class AgentParseError(Exception):
  pass


MODEL = "composer-2.5"

PROMPT_TEMPLATE = """You convert a natural-language calendar request into JSON for a CLI tool.

Current local datetime: {now_iso}
Default IANA timezone: {default_tz}

User request:
{request}

Rules:
- Reply with ONLY a single JSON object. No markdown, no prose.
- Infer missing details when reasonable (e.g. "tomorrow at 7 PM").
- Use the default timezone unless the user names another.
- start and end must be ISO-8601 local datetimes WITHOUT a trailing Z unless the instant is UTC. Prefer naive local wall time in the chosen timezone, e.g. "2026-08-01T19:00:00".
- If the user gives a duration ("for two hours") set duration_minutes and omit end, OR set end. Prefer duration_minutes when they gave a duration.
- If no duration or end is given, omit both (the tool defaults to 60 minutes).
- Omit keys that were not provided and cannot be inferred: location, description, rrule, timezone (omit timezone when default is fine).
- rrule must be an iCalendar RRULE value without the "RRULE:" prefix when recurrence is clear (e.g. "FREQ=WEEKLY;BYDAY=MO").
- title should be a short calendar title.
- If the request is genuinely not enough to schedule anything (no usable title/time), return {{"error":"short explanation of what is missing"}} instead.

JSON shape on success:
{{
  "title": "string",
  "start": "YYYY-MM-DDTHH:MM:SS",
  "end": "YYYY-MM-DDTHH:MM:SS",
  "duration_minutes": 120,
  "location": "string",
  "description": "string",
  "rrule": "FREQ=WEEKLY;BYDAY=MO",
  "timezone": "America/Sao_Paulo"
}}
"""

# rrule is not a typo. It refers to recurrence rules.


def extract_json(text: str) -> dict:
  text = text.strip()
  if not text:
    raise AgentParseError("Agent returned an empty response.")
  fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
  if fence:
    blob = fence.group(1)
  else:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
      raise AgentParseError("Agent response did not contain a JSON object.")
    blob = text[start : end + 1]
  try:
    data = json.loads(blob)
  except json.JSONDecodeError as exc:
    raise AgentParseError(f"Agent returned invalid JSON: {exc}") from exc
  if not isinstance(data, dict):
    raise AgentParseError("Agent JSON must be an object.")
  return data


def build_prompt(request: str, *, now_iso: str, default_tz: str) -> str:
  return PROMPT_TEMPLATE.format(now_iso=now_iso, default_tz=default_tz, request=request)


def parse_event_with_agent(request: str, *, now_iso: str, default_tz: str) -> dict:
  if not shutil.which("agent"):
    raise AgentParseError(
      "Cursor Agent CLI (`agent`) not found on PATH. Install Cursor CLI and run `agent login`."
    )
  prompt = build_prompt(request, now_iso=now_iso, default_tz=default_tz)
  cmd = [
    "agent",
    "-p",
    "--mode",
    "ask",
    "--model",
    MODEL,
    "--output-format",
    "text",
    prompt,
  ]
  try:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
  except OSError as exc:
    raise AgentParseError(f"Failed to run Cursor Agent: {exc}") from exc
  if proc.returncode != 0:
    err = (proc.stderr or proc.stdout or "").strip() or f"exit {proc.returncode}"
    raise AgentParseError(f"Cursor Agent failed: {err}")
  return extract_json(proc.stdout)
