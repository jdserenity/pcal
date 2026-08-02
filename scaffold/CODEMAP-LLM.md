# Code map (agent reference)

## Product
- Global macOS CLI `pcal "<natural language event>"` adds an event to the user’s own Proton Calendar by emailing a standards-compliant iCalendar `METHOD:PUBLISH` (no `ATTENDEE`) to their Proton address via Proton Mail Bridge local SMTP (no browser automation, no manual `.ics` import, not for inviting other people).
- User opens the email once and clicks **Add to Proton Calendar**. That is the intended recurring manual step.
- Do not use `METHOD:REQUEST`: when ORGANIZER matches the To address, Proton enters “organizer mode” and shows UI error “Invalid response”.
- Optional fields only when present/inferred: title, start, end or duration, date, location, description, recurrence (`rrule`), timezone, `all_day`. Missing location/description/rrule are omitted from ICS. Timed events default duration 60 minutes when neither end nor duration given. All-day events default end to the next calendar day (ICS `VALUE=DATE`, exclusive end). Default timezone = config `timezone` or local Mac TZ.
- Fail clearly on empty/insufficient requests (agent `{"error":"..."}` or validation errors) rather than silent no-op.
- Config/credentials outside code: `~/.config/pcal/config.toml` from `config.example.toml` via `pcal --init`. Env: `PCAL_CONFIG`, `PCAL_SMTP_PASSWORD`.

## Stack
- Python 3: stdlib (tomllib, zoneinfo, smtplib, email, unittest) + `yaspin` (CLI spinner; `requirements.txt`, installed by `install.sh`).
- Cursor Agent headless: `agent -p --mode ask --model composer-2.5 --output-format text` (model id confirmed `composer-2.5`). Ask mode avoids tool use; response must be JSON.
- Bridge SMTP defaults: `127.0.0.1:1025`, STARTTLS + LOGIN with Bridge mailbox password.

## Modules
- `pcal/cli.py` — entry; `--init`, `--dry-run`, `--config`.
- `pcal/agent_parse.py` — prompt (title = user wording minus scheduling fields; no auto-shorten) + `extract_json` (raw / fenced / embedded).
- `pcal/validate.py` — `EventSpec`; error key short-circuits.
- `pcal/ics.py` — CRLF, escaping, line folding, TZID local wall times or `VALUE=DATE` for all-day, ORGANIZER; always `METHOD:PUBLISH` (no ATTENDEE).
- `pcal/mail.py` — multipart alternative (plain + text/calendar method=PUBLISH) + `.ics` attachment; `starttls` then `login` then `send_message`.
- `pcal/config.py` — load/validate; `require_smtp` only when actually sending.

## Pitfalls
- Bridge must be running; SMTP password is Bridge-generated, not the Proton account password.
- Set `from_email` == `to_email` so the email lands in the same Proton inbox.
- `bin/pcal` inserts repo root on `sys.path` for in-repo runs. `./scripts/install.sh` copies `pcal/` and `config.example.toml` to `~/.local/lib/pcal` and writes a real launcher at `~/.local/bin/pcal` (re-run after repo changes).
- Agent probe (2026-07-31): `composer-2.5` with ask/print returns bare JSON reliably for structured extraction prompts.
