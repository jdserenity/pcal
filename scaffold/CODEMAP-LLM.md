# Code map (agent reference)

## Product
- Global macOS CLI `pcal "<natural language event>"` creates a Proton Calendar event by emailing a standards-compliant iCalendar `METHOD:REQUEST` invitation to the configured Proton address via Proton Mail Bridge local SMTP (no browser automation, no manual `.ics` import).
- User accepts the invitation once in Proton Mail/Calendar; that is the intended recurring manual step.
- Optional fields only when present/inferred: title, start, end or duration, date, location, description, recurrence (`rrule`), timezone. Missing location/description/rrule are omitted from ICS. Default duration 60 minutes when neither end nor duration given. Default timezone = config `timezone` or local Mac TZ.
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
- `pcal/ics.py` — CRLF, escaping, line folding, TZID local wall times, ORGANIZER/ATTENDEE.
- `pcal/mail.py` — multipart alternative (plain + text/calendar method=REQUEST) + `.ics` attachment; `starttls` then `login` then `send_message`.
- `pcal/config.py` — load/validate; `require_smtp` only when actually sending.

## Pitfalls
- Bridge must be running; SMTP password is Bridge-generated, not the Proton account password.
- Self-invite: set `from_email` == `to_email` so the invite lands in the same Proton inbox.
- `bin/pcal` inserts repo root on `sys.path` for in-repo runs. `./scripts/install.sh` copies `pcal/` and `config.example.toml` to `~/.local/lib/pcal` and writes a real launcher at `~/.local/bin/pcal` (re-run after repo changes).
- Agent probe (2026-07-31): `composer-2.5` with ask/print returns bare JSON reliably for structured extraction prompts.
