#!/usr/bin/env bash
# Salem Makki Portfolio - one-command local start (macOS / Linux)
set -e
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "Install Python 3 first: https://www.python.org/downloads/"; exit 1; }
[ -x .venv/bin/python ] || python3 -m venv .venv
PY=.venv/bin/python
if [ ! -f instance/.setup_done ]; then
  "$PY" -m pip install --disable-pip-version-check -q -r requirements.txt
  [ -f .env ] || "$PY" -c "import secrets; open('.env','w').write('SECRET_KEY='+secrets.token_hex(32)+'\n')"
  "$PY" -m flask --app run init-db
  "$PY" -m flask --app run seed
  echo "Create your admin account (password: 10+ characters, hidden while typing):"
  "$PY" -m flask --app run create-admin
  mkdir -p instance && touch instance/.setup_done
fi
echo "Website: http://localhost:5000   Dashboard: http://localhost:5000/admin   (Ctrl+C to stop)"
( sleep 3; (xdg-open http://localhost:5000 || open http://localhost:5000) >/dev/null 2>&1 ) &
"$PY" -m flask --app run run
