#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -x .venv/bin/gunicorn ]; then
  echo "尚未安装，请先运行 bash install_local.sh"
  exit 1
fi

CASEFLOW_PORT="${CASEFLOW_PORT:-8080}"
URL="http://127.0.0.1:${CASEFLOW_PORT}"

if command -v open >/dev/null 2>&1; then
  (sleep 1; open "$URL") &
elif command -v xdg-open >/dev/null 2>&1; then
  (sleep 1; xdg-open "$URL") &
fi

exec .venv/bin/gunicorn --bind "127.0.0.1:${CASEFLOW_PORT}" --workers 1 app:app
