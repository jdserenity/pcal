# pcal

Natural-language events for your Proton Calendar.

```bash
./scripts/install.sh   # re-run after changing code in this repo
pcal --init          # writes ~/.config/pcal/config.toml
# edit that file, then:
pcal "Dinner with Marcelo tomorrow at 7 PM for two hours"
```

Open the email in Proton Mail and click **Add to Proton Calendar**. That is the only recurring manual step.

## Setup

1. `python3 -m pip install --user --break-system-packages -r requirements.txt` (or run `./scripts/install.sh`, which installs deps too).
2. Install Cursor CLI and run `agent login` (model used: `composer-2.5`).
3. Install and sign in to [Proton Mail Bridge](https://proton.me/mail/bridge). Keep Bridge running.
4. In Bridge, open your mailbox → copy the **SMTP** username/password Bridge shows (not your normal Proton password).
5. `./scripts/install.sh` then `pcal --init`, and fill in `~/.config/pcal/config.toml` (`from_email`, `to_email`, `smtp_user`, `smtp_password`). Use the same address for from and to.
6. Bridge SMTP defaults: host `127.0.0.1`, port `1025`, STARTTLS.

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
