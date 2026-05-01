#!/bin/bash
cd "$(dirname "$0")"
pip3 install -r requirements.txt -q 2>/dev/null
python3 app.py
