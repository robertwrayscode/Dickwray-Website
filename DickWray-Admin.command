#!/bin/bash
# Dick Wray Website Admin Tool — Double-click to launch
cd "$(dirname "$0")/admin-tool"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt -q 2>&1
(sleep 2 && open http://localhost:5555) &
python3 app.py
