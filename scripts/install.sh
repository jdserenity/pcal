#!/usr/bin/env bash
# Install the global `pcal` command into ~/.local/bin
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)" # Bash doesn’t give you a clean __file__ like Python does. `cd` uses the current working directory of where the script was called *from*, not the script's location, so one can't just use `cd ..` and $0 needs to be used. `dirnam` is the name of the dir that holds the current path ($0). So it's basically the parent dir but it's not one dir above.
# So the command does something like: go (cd) one above (/..) the dir that this script lives in (dirname "$0")
BIN_DIR="${HOME}/.local/bin" # In bash, ${HOME} and $HOME are the same thing — both expand to the value of the HOME environment variable. The curly braces are optional parameter-expansion syntax. So this isn’t “HOME without $” — it’s $HOME with braces.
INSTALL_DIR="${HOME}/.local/lib/pcal"
mkdir -p "$BIN_DIR" "$INSTALL_DIR"
chmod +x "$ROOT/bin/pcal" # ensures the pcal launcher can be executed directly instead of only via python or sh
rm -rf "$INSTALL_DIR/pcal" # ensures a clean install. Won't fail if the target doesn't exist. `-f` ("force") suppresses errors for missing files/directories.
cp -R "$ROOT/pcal" "$INSTALL_DIR/"
cp "$ROOT/config.example.toml" "$INSTALL_DIR/"
cp "$ROOT/bin/pcal" "$BIN_DIR/pcal"
chmod +x "$BIN_DIR/pcal"
echo "Installed."
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    echo "Note: $BIN_DIR is not on your PATH. Add this to ~/.zshrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    ;;
esac
CONFIG_FILE="${PCAL_CONFIG:-$HOME/.config/pcal/config.toml}" # The line uses Bash's ${VAR:-default} syntax, so if PCAL_CONFIG isn't set, it defaults to $HOME/.config/pcal/config.toml
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Next: pcal --init   # then edit $CONFIG_FILE"
fi
echo "Re-run ./scripts/install.sh after changing code in this repo."
