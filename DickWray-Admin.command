#!/bin/bash
# ============================================
#  Dick Wray Website Admin
#  Double-click this file to launch
# ============================================

cd "$(dirname "$0")/admin-tool"

# Set up Python environment (first time only)
if [ ! -d "venv" ]; then
    echo "First-time setup — creating Python environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt -q 2>/dev/null

echo ""
echo "🎨  Dick Wray Admin is starting..."
echo "    Opening http://localhost:5555 in your browser"
echo ""
echo "    When you're done, close this window to stop the server."
echo ""

# Open browser after a short delay
(sleep 2 && open http://localhost:5555) &

python3 app.py
