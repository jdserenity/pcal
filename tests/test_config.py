import os, tempfile, unittest
from pathlib import Path

from pcal.config import ConfigError, load_config, write_example_config

class ConfigTests(unittest.TestCase):
  def test_loads_required_fields(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / "config.toml"
      path.write_text(
        'from_email = "a@proton.me"\n'
        'to_email = "a@proton.me"\n'
        'smtp_user = "a@proton.me"\n'
        'smtp_password = "secret"\n'
        'timezone = "America/Sao_Paulo"\n',
        encoding="utf-8",
      )
      cfg = load_config(path)
      self.assertEqual(cfg.from_email, "a@proton.me")
      self.assertEqual(cfg.to_email, "a@proton.me")
      self.assertEqual(cfg.smtp_host, "127.0.0.1")
      self.assertEqual(cfg.smtp_port, 1025)
      self.assertEqual(cfg.smtp_password, "secret")
      self.assertEqual(cfg.timezone, "America/Sao_Paulo")

  def test_missing_file_is_clear(self):
    with self.assertRaises(ConfigError) as ctx:
      load_config(Path("/tmp/pcal-missing-config-does-not-exist.toml"))
    self.assertIn("config", str(ctx.exception).lower())

  def test_missing_password_loads_but_require_smtp_fails(self):
    from pcal.config import require_smtp
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / "config.toml"
      path.write_text('from_email = "a@proton.me"\nto_email = "a@proton.me"\nsmtp_user = "a@proton.me"\n', encoding="utf-8")
      cfg = load_config(path)
      self.assertEqual(cfg.smtp_password, "")
      with self.assertRaises(ConfigError) as ctx:
        require_smtp(cfg)
      self.assertIn("smtp_password", str(ctx.exception))

  def test_env_override_password(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / "config.toml"
      path.write_text(
        'from_email = "a@proton.me"\nto_email = "a@proton.me"\nsmtp_user = "a@proton.me"\nsmtp_password = "filepass"\n',
        encoding="utf-8",
      )
      old = os.environ.get("PCAL_SMTP_PASSWORD")
      os.environ["PCAL_SMTP_PASSWORD"] = "envpass"
      try:
        cfg = load_config(path)
        self.assertEqual(cfg.smtp_password, "envpass")
      finally:
        if old is None: os.environ.pop("PCAL_SMTP_PASSWORD", None)
        else: os.environ["PCAL_SMTP_PASSWORD"] = old

  def test_write_example_config(self):
    with tempfile.TemporaryDirectory() as tmp:
      dest = Path(tmp) / "config.toml"
      write_example_config(dest, Path(__file__).resolve().parents[1] / "config.example.toml")
      self.assertTrue(dest.is_file())
      self.assertIn("smtp_password", dest.read_text(encoding="utf-8"))

if __name__ == "__main__":
  unittest.main()
