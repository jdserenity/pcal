import json, unittest
from unittest.mock import patch

from pcal.agent_parse import AgentParseError, extract_json, parse_event_with_agent

class ExtractJsonTests(unittest.TestCase):
  def test_raw_object(self):
    self.assertEqual(extract_json('{"title": "Dinner"}'), {"title": "Dinner"})

  def test_fenced_block(self):
    text = 'Sure.\n```json\n{"title": "Dinner", "start": "2026-08-01T19:00:00"}\n```\n'
    self.assertEqual(extract_json(text)["title"], "Dinner")

  def test_embedded_object(self):
    text = 'Here you go: {"title": "X", "start": "2026-08-01T19:00:00"} thanks'
    self.assertEqual(extract_json(text)["title"], "X")

  def test_invalid_fails(self):
    with self.assertRaises(AgentParseError):
      extract_json("no json here")

class AgentParseTests(unittest.TestCase):
  @patch("pcal.agent_parse.subprocess.run")
  def test_calls_agent_with_composer(self, run):
    payload = {"title": "Dinner", "start": "2026-08-01T19:00:00", "duration_minutes": 120}
    run.return_value = unittest.mock.Mock(returncode=0, stdout=json.dumps(payload), stderr="")
    result = parse_event_with_agent(
      'Dinner with Marcelo tomorrow at 7 PM for two hours',
      now_iso="2026-07-31T10:00:00-03:00",
      default_tz="America/Sao_Paulo",
    )
    self.assertEqual(result["title"], "Dinner")
    args = run.call_args.args[0]
    self.assertEqual(args[0], "agent")
    self.assertIn("-p", args)
    self.assertIn("--model", args)
    self.assertIn("composer-2.5", args)
    self.assertIn("--mode", args)
    self.assertIn("ask", args)

  @patch("pcal.agent_parse.subprocess.run")
  def test_nonzero_exit_fails(self, run):
    run.return_value = unittest.mock.Mock(returncode=1, stdout="", stderr="boom")
    with self.assertRaises(AgentParseError) as ctx:
      parse_event_with_agent("x", now_iso="2026-07-31T10:00:00-03:00", default_tz="UTC")
    self.assertIn("agent", str(ctx.exception).lower())

if __name__ == "__main__":
  unittest.main()
