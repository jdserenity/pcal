import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class InstallTests(unittest.TestCase):
  def test_install_copies_package_and_launcher(self):
    with tempfile.TemporaryDirectory() as tmp:
      home = Path(tmp) / "home"
      home.mkdir()
      env = {**os.environ, "HOME": str(home)}
      subprocess.run(["bash", str(REPO / "scripts" / "install.sh")], check=True, env=env)
      launcher = home / ".local" / "bin" / "pcal"
      pkg_cli = home / ".local" / "lib" / "pcal" / "pcal" / "cli.py"
      example = home / ".local" / "lib" / "pcal" / "config.example.toml"
      self.assertTrue(launcher.is_file())
      self.assertFalse(launcher.is_symlink())
      self.assertTrue(pkg_cli.is_file())
      self.assertTrue(example.is_file())
      help_run = subprocess.run([str(launcher), "--help"], check=True, capture_output=True, text=True, env=env)
      self.assertIn("pcal", help_run.stdout)
      config_dest = home / ".config" / "pcal" / "config.toml"
      init_run = subprocess.run(
        [str(launcher), "--init", "--config", str(config_dest)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
      )
      self.assertTrue(config_dest.is_file())
      self.assertIn(str(config_dest), init_run.stdout)

  def test_install_skips_init_hint_when_config_exists(self):
    with tempfile.TemporaryDirectory() as tmp:
      home = Path(tmp) / "home"
      home.mkdir()
      config = home / ".config" / "pcal" / "config.toml"
      config.parent.mkdir(parents=True)
      config.write_text("from_email = \"you@proton.me\"\n", encoding="utf-8")
      env = {**os.environ, "HOME": str(home)}
      run = subprocess.run(
        ["bash", str(REPO / "scripts" / "install.sh")],
        check=True,
        capture_output=True,
        text=True,
        env=env,
      )
      self.assertNotIn("pcal --init", run.stdout)
