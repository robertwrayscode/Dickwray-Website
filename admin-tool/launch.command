#!/bin/bash
# Dick Wray Website — Admin Tool
# Double-click this file in Finder to launch the admin panel

cd "$(dirname "$0")"

echo "================================================"
echo "  Dick Wray Website — Admin Tool"
echo "================================================"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Setting up virtual environment (first time only)..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment."
        echo "Press any key to close..."
        read -n 1
        exit 1
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
echo "Checking dependencies..."
pip install -r requirements.txt -q 2>&1

echo "Starting admin server..."
echo ""
echo "Admin panel will open at: http://localhost:5555"
echo "Press Ctrl+C in this window to stop the server."
echo ""

# Open browser after a short delay
(sleep 2 && open http://localhost:5555) &

# Start the Flask app
python3 app.py

deactivate 2>/dev/null
echo ""
echo "Server stopped."
echo "Press any key to close..."
read -n 1
