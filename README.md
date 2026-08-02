# pcal

Natural-language calendar invites for Proton Calendar.

```bash
./scripts/install.sh   # re-run after changing code in this repo
pcal --init          # writes ~/.config/pcal/config.toml
# edit that file, then:
pcal "Dinner with Marcelo tomorrow at 7 PM for two hours"
```

Accept the invitation in Proton Mail / Calendar once. That is the only recurring manual step.

## Setup

1. Install Cursor CLI and run `agent login` (model used: `composer-2.5`).
2. Install and sign in to [Proton Mail Bridge](https://proton.me/mail/bridge). Keep Bridge running.
3. In Bridge, open your mailbox → copy the **SMTP** username/password Bridge shows (not your normal Proton password).
4. `./scripts/install.sh` then `pcal --init`, and fill in `~/.config/pcal/config.toml` (`from_email`, `to_email`, `smtp_user`, `smtp_password`). Use the same address for from/to to invite yourself.
5. Bridge SMTP defaults: host `127.0.0.1`, port `1025`, STARTTLS.

## Usage

```bash
pcal "Team standup Mondays at 9am for 30 minutes"
pcal --dry-run "Coffee Friday 3pm at Cafe Brasil"
PCAL_SMTP_PASSWORD='...' pcal "..."   # optional password override
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```
