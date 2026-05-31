#!/usr/bin/env bash
# Install citation-import as a macOS launchd daemon.
# Run this once after cloning and configuring ~/.citation_import.toml.

set -euo pipefail

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$(command -v python3)"
HOME_DIR="$HOME"
PYTHON_DIR="$(dirname "$PYTHON")"
PLIST_TEMPLATE="$INSTALL_DIR/launchd/com.citation-import.plist.template"
PLIST_DEST="$HOME/Library/LaunchAgents/local.citation-import.plist"

echo "==> citation-import installer"
echo "    Install dir : $INSTALL_DIR"
echo "    Python      : $PYTHON"
echo "    Plist dest  : $PLIST_DEST"
echo ""

# --- Install Python dependencies ---
echo "==> Installing Python dependencies..."
"$PYTHON" -m pip install -q -r "$INSTALL_DIR/requirements.txt"
echo "    Done."

# --- Create ~/.citation_import.toml if missing ---
CONFIG="$HOME/.citation_import.toml"
if [ ! -f "$CONFIG" ]; then
    echo "==> Creating $CONFIG from example..."
    cp "$INSTALL_DIR/config.example.toml" "$CONFIG"
    echo "    Edit $CONFIG to set your target_bib path."
fi

# --- Generate launchd plist from template ---
echo "==> Generating launchd plist..."
sed \
    -e "s|__PYTHON__|$PYTHON|g" \
    -e "s|__INSTALL_DIR__|$INSTALL_DIR|g" \
    -e "s|__HOME__|$HOME_DIR|g" \
    -e "s|__PYTHON_DIR__|$PYTHON_DIR|g" \
    "$PLIST_TEMPLATE" > "$PLIST_DEST"
echo "    Written to $PLIST_DEST"

# --- Load (or reload) the agent ---
if launchctl list | grep -q "local.citation-import"; then
    echo "==> Reloading existing launchd agent..."
    launchctl unload "$PLIST_DEST"
fi
echo "==> Loading launchd agent..."
launchctl load "$PLIST_DEST"

echo ""
echo "Done! The watcher is running in the background."
echo "Log: $HOME/.citation_import.log"
echo ""
echo "To stop:  launchctl unload ~/Library/LaunchAgents/local.citation-import.plist"
echo "To start: launchctl load  ~/Library/LaunchAgents/local.citation-import.plist"
