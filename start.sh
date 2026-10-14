#!/usr/bin/env bash
# Launch the desktop app from a source checkout (macOS and Linux).
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
  exec python3 desktop.py "$@"
fi
exec python desktop.py "$@"
