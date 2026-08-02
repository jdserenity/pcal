import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from pcal.ics import build_invite_ics
from pcal.validate import EventSpec

class IcsTests(unittest.TestCase):
  def _event(self, **kwargs):
    tz = ZoneInfo("America/Sao_Paulo")
    start = datetime(2026, 8, 1, 19, 0, tzinfo=tz)
    end = datetime(2026, 8, 1, 21, 0, tzinfo=tz)
    base = dict(
      title="Dinner with Marcelo",
      start=start,
      end=end,
      timezone="America/Sao_Paulo",
      location=None,
      description=None,
      rrule=None,
    )
    base.update(kwargs)
    return EventSpec(**base)

  def test_method_request_and_core_fields(self):
    ics = build_invite_ics(
      self._event(),
      uid="test-uid@pcal",
      organizer_email="me@proton.me",
      organizer_name="Me",
      attendee_email="me@proton.me",
      dtstamp=datetime(2026, 7, 31, 12, 0, 0, tzinfo=ZoneInfo("UTC")),
    )
    self.assertIn("BEGIN:VCALENDAR", ics)
    self.assertIn("METHOD:REQUEST", ics)
    self.assertIn("BEGIN:VEVENT", ics)
    self.assertIn("UID:test-uid@pcal", ics)
    self.assertIn("SUMMARY:Dinner with Marcelo", ics)
    self.assertIn("DTSTART;TZID=America/Sao_Paulo:20260801T190000", ics)
    self.assertIn("DTEND;TZID=America/Sao_Paulo:20260801T210000", ics)
    self.assertIn("ORGANIZER;CN=Me:mailto:me@proton.me", ics)
    self.assertIn("ATTENDEE;", ics)
    self.assertIn("mailto:me@proton.me", ics)
    self.assertIn("END:VEVENT", ics)
    self.assertIn("END:VCALENDAR", ics)
    self.assertTrue(ics.endswith("\r\n") or "\r\n" in ics)

  def test_omits_location_when_absent(self):
    ics = build_invite_ics(
      self._event(location=None),
      uid="u@pcal",
      organizer_email="a@b.c",
      organizer_name=None,
      attendee_email="a@b.c",
    )
    self.assertNotIn("LOCATION:", ics)

  def test_includes_optional_fields(self):
    ics = build_invite_ics(
      self._event(location="Cafe", description="Bring dessert", rrule="FREQ=WEEKLY;BYDAY=FR"),
      uid="u@pcal",
      organizer_email="a@b.c",
      organizer_name=None,
      attendee_email="a@b.c",
    )
    self.assertIn("LOCATION:Cafe", ics)
    self.assertIn("DESCRIPTION:Bring dessert", ics)
    self.assertIn("RRULE:FREQ=WEEKLY;BYDAY=FR", ics)

  def test_escapes_text(self):
    ics = build_invite_ics(
      self._event(title="Dinner; with\nMarcelo, maybe", description="Line1\nLine2"),
      uid="u@pcal",
      organizer_email="a@b.c",
      organizer_name=None,
      attendee_email="a@b.c",
    )
    self.assertIn(r"SUMMARY:Dinner\; with\nMarcelo\, maybe", ics)
    self.assertIn(r"DESCRIPTION:Line1\nLine2", ics)

  def test_folds_long_lines(self):
    long_title = "A" * 100
    ics = build_invite_ics(
      self._event(title=long_title),
      uid="u@pcal",
      organizer_email="a@b.c",
      organizer_name=None,
      attendee_email="a@b.c",
    )
    # RFC 5545 line folding: CRLF + space continuation
    self.assertIn("\r\n ", ics)

if __name__ == "__main__":
  unittest.main()
