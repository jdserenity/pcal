"""Send a calendar invitation over Proton Mail Bridge's local SMTP service."""
from __future__ import annotations

import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from pcal.validate import EventSpec


def build_invite_message(
  *,
  event: EventSpec,
  ics_body: str,
  from_email: str,
  from_name: str | None,
  to_email: str,
) -> MIMEMultipart:
  msg = MIMEMultipart("mixed")
  msg["From"] = formataddr((from_name or "", from_email))
  msg["To"] = to_email
  msg["Subject"] = f"Invitation: {event.title}"

  alt = MIMEMultipart("alternative")
  when = event.start.strftime("%Y-%m-%d %H:%M")
  plain = (
    f"Calendar invitation: {event.title}\n"
    f"When: {when} ({event.timezone})\n"
    f"Accept this invitation in Proton Mail / Proton Calendar to add it to your calendar.\n"
  )
  alt.attach(MIMEText(plain, "plain", "utf-8"))

  cal = MIMEText(ics_body, "calendar", "utf-8")
  cal.set_param("method", "REQUEST")
  cal.set_param("name", "invite.ics")
  alt.attach(cal)
  msg.attach(alt)

  attach = MIMEBase("text", "calendar", method="REQUEST", name="invite.ics")
  attach.set_payload(ics_body.encode("utf-8"))
  attach.add_header("Content-Disposition", "attachment", filename="invite.ics")
  attach.add_header("Content-Transfer-Encoding", "8bit")
  attach.set_param("method", "REQUEST")
  attach.set_param("charset", "UTF-8")
  msg.attach(attach)
  return msg


def send_invite(
  *,
  event: EventSpec,
  ics_body: str,
  from_email: str,
  from_name: str | None,
  to_email: str,
  smtp_host: str,
  smtp_port: int,
  smtp_user: str,
  smtp_password: str,
) -> None:
  msg = build_invite_message(
    event=event,
    ics_body=ics_body,
    from_email=from_email,
    from_name=from_name,
    to_email=to_email,
  )
  client = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
  try:
    client.ehlo()
    client.starttls()
    client.ehlo()
    client.login(smtp_user, smtp_password)
    client.send_message(msg)
  finally:
    try: client.quit()
    except Exception: client.close()
