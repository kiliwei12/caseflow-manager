#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -x .venv/bin/gunicorn ]; then
  bash install_local.sh
fi

bash start_local.sh
