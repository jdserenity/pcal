import unittest
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from pcal.cli import format_event_when, main
from pcal.validate import EventSpec

class CliTests(unittest.TestCase):
  def test_no_args_fails(self):
    code = main([])
    self.assertEqual(code, 2)

  def test_empty_request_fails(self):
    code = main([""])
    self.assertEqual(code, 2)

  @patch("pcal.cli.send_invite")
  @patch("pcal.cli.parse_event_with_agent")
  @patch("pcal.cli.load_config")
  def test_happy_path(self, load_config, parse_event, send_invite):
    cfg = unittest.mock.Mock(
      from_email="me@proton.me",
      to_email="me@proton.me",
      from_name="Me",
      smtp_host="127.0.0.1",
      smtp_port=1025,
      smtp_user="me@proton.me",
      smtp_password="secret",
      timezone="America/Sao_Paulo",
      path="/tmp/config.toml",
    )
    load_config.return_value = cfg
    parse_event.return_value = {
      "title": "Dinner with Marcelo",
      "start": "2026-08-01T19:00:00",
      "duration_minutes": 120,
    }
    code = main(["Dinner with Marcelo tomorrow at 7 PM for two hours"])
    self.assertEqual(code, 0)
    self.assertTrue(send_invite.called)

  @patch("pcal.cli.parse_event_with_agent")
  @patch("pcal.cli.load_config")
  def test_agent_error_payload(self, load_config, parse_event):
    cfg = unittest.mock.Mock(timezone="America/Sao_Paulo", path="/tmp/config.toml")
    load_config.return_value = cfg
    parse_event.return_value = {"error": "Please include a date or time."}
    code = main(["asdf"])
    self.assertEqual(code, 1)

  def test_format_all_day_single_day(self):
    tz = ZoneInfo("America/Sao_Paulo")
    event = EventSpec(
      title="Dog's birthday",
      start=datetime(2026, 8, 19, 0, 0, tzinfo=tz),
      end=datetime(2026, 8, 20, 0, 0, tzinfo=tz),
      timezone="America/Sao_Paulo",
      location=None,
      description=None,
      rrule="FREQ=YEARLY",
      all_day=True,
    )
    self.assertEqual(format_event_when(event), "2026-08-19 (all day)")

if __name__ == "__main__":
  unittest.main()
