import unittest
from email import message_from_bytes
from unittest.mock import MagicMock, patch

from pcal.mail import build_invite_message, send_invite
from pcal.validate import EventSpec
from datetime import datetime
from zoneinfo import ZoneInfo

class MailTests(unittest.TestCase):
  def _event(self):
    tz = ZoneInfo("America/Sao_Paulo")
    return EventSpec(
      title="Dinner",
      start=datetime(2026, 8, 1, 19, 0, tzinfo=tz),
      end=datetime(2026, 8, 1, 21, 0, tzinfo=tz),
      timezone="America/Sao_Paulo",
      location=None,
      description=None,
      rrule=None,
    )

  def test_message_has_calendar_parts(self):
    ics = "BEGIN:VCALENDAR\r\nMETHOD:REQUEST\r\nEND:VCALENDAR\r\n"
    msg = build_invite_message(
      event=self._event(),
      ics_body=ics,
      from_email="me@proton.me",
      from_name="Me",
      to_email="me@proton.me",
    )
    raw = msg.as_bytes()
    parsed = message_from_bytes(raw)
    self.assertEqual(parsed["From"], "Me <me@proton.me>")
    self.assertEqual(parsed["To"], "me@proton.me")
    self.assertIn("Dinner", parsed["Subject"])
    types = []
    for part in parsed.walk():
      types.append(part.get_content_type())
    self.assertIn("text/calendar", types)
    calendar_parts = [p for p in parsed.walk() if p.get_content_type() == "text/calendar"]
    self.assertTrue(calendar_parts)
    self.assertEqual(calendar_parts[0].get_param("method"), "REQUEST")

  @patch("pcal.mail.smtplib.SMTP")
  def test_send_uses_starttls_and_auth(self, smtp_cls):
    client = MagicMock()
    smtp_cls.return_value.__enter__.return_value = client
    smtp_cls.return_value = client
    ics = "BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n"
    send_invite(
      event=self._event(),
      ics_body=ics,
      from_email="me@proton.me",
      from_name="Me",
      to_email="me@proton.me",
      smtp_host="127.0.0.1",
      smtp_port=1025,
      smtp_user="me@proton.me",
      smtp_password="secret",
    )
    smtp_cls.assert_called_with("127.0.0.1", 1025, timeout=30)
    client.starttls.assert_called_once()
    client.login.assert_called_once_with("me@proton.me", "secret")
    self.assertTrue(client.send_message.called)
    client.quit.assert_called_once()

if __name__ == "__main__":
  unittest.main()
