import unittest
from pcal.validate import EventSpec, ValidationError, validate_event

class ValidateTests(unittest.TestCase):
  def test_requires_title_and_start(self):
    with self.assertRaises(ValidationError) as ctx:
      validate_event({"title": "", "start": None}, default_tz="America/Sao_Paulo")
    msg = str(ctx.exception).lower()
    self.assertTrue("title" in msg or "start" in msg or "not enough" in msg)

  def test_accepts_minimal_event(self):
    ev = validate_event(
      {"title": "Dinner", "start": "2026-08-01T19:00:00"},
      default_tz="America/Sao_Paulo",
    )
    self.assertIsInstance(ev, EventSpec)
    self.assertEqual(ev.title, "Dinner")
    self.assertEqual(ev.timezone, "America/Sao_Paulo")
    self.assertIsNotNone(ev.end)
    self.assertIsNone(ev.location)

  def test_duration_sets_end(self):
    ev = validate_event(
      {"title": "Dinner", "start": "2026-08-01T19:00:00", "duration_minutes": 120},
      default_tz="America/Sao_Paulo",
    )
    self.assertEqual((ev.end - ev.start).total_seconds(), 7200)

  def test_explicit_end_wins(self):
    ev = validate_event(
      {
        "title": "Dinner",
        "start": "2026-08-01T19:00:00",
        "end": "2026-08-01T20:30:00",
        "duration_minutes": 999,
      },
      default_tz="America/Sao_Paulo",
    )
    self.assertEqual((ev.end - ev.start).total_seconds(), 5400)

  def test_end_before_start_fails(self):
    with self.assertRaises(ValidationError):
      validate_event(
        {"title": "X", "start": "2026-08-01T19:00:00", "end": "2026-08-01T18:00:00"},
        default_tz="America/Sao_Paulo",
      )

  def test_optional_fields(self):
    ev = validate_event(
      {
        "title": "Standup",
        "start": "2026-08-01T09:00:00",
        "location": "Zoom",
        "description": "Daily sync",
        "rrule": "FREQ=WEEKLY;BYDAY=MO",
        "timezone": "UTC",
      },
      default_tz="America/Sao_Paulo",
    )
    self.assertEqual(ev.location, "Zoom")
    self.assertEqual(ev.description, "Daily sync")
    self.assertEqual(ev.rrule, "FREQ=WEEKLY;BYDAY=MO")
    self.assertEqual(ev.timezone, "UTC")

  def test_error_payload_fails_clearly(self):
    with self.assertRaises(ValidationError) as ctx:
      validate_event({"error": "Need a date or time"}, default_tz="America/Sao_Paulo")
    self.assertIn("Need a date or time", str(ctx.exception))

if __name__ == "__main__":
  unittest.main()
