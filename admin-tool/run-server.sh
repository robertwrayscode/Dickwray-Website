#!/bin/bash
# Runs the Dick Wray admin server (used by the DickWray Admin app / launchd).
# Keeps running in the background; the dashboard is at http://localhost:5555
cd "$(dirname "$0")"
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
if [ ! -d venv ]; then
    python3 -m venv venv || exit 1
fi
./venv/bin/pip install -q -r requirements.txt >/dev/null 2>&1
export DICKWRAY_NO_BROWSER=1
exec ./venv/bin/python app.py
