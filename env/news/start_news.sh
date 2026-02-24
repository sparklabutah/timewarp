#!/bin/bash
# Start Wikinews application

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Determine theme
THEME_ARG=""
THEME_NAME="Classic"

if [ "$1" = "-1" ]; then
    THEME_ARG="-1"
    THEME_NAME="Classic (Modern News UI)"
elif [ "$1" = "-2" ]; then
    THEME_ARG="-2"
    THEME_NAME="Modern (Dark/Light mode)"
elif [ "$1" = "-3" ]; then
    THEME_ARG="-3"
    THEME_NAME="Wikinews 2002 (Retro)"
elif [ "$1" = "-4" ]; then
    THEME_ARG="-4"
    THEME_NAME="Wikinews 2001 (Ultra-Retro)"
elif [ "$1" = "-5" ]; then
    THEME_ARG="-5"
    THEME_NAME="News 2000 (BBC News Style)"
elif [ "$1" = "-6" ]; then
    THEME_ARG="-6"
    THEME_NAME="Base Minimal"
elif [ "$1" = "-all" ] || [ "$1" = "--all" ]; then
    THEME_ARG="-all"
    THEME_NAME="All themes (servers 1-6)"
else
    THEME_ARG="-1"
    THEME_NAME="Classic (Modern News UI) [default]"
fi

echo "========================================"
echo "Wikinews UI"
echo "========================================"
echo ""
echo "Working directory: $SCRIPT_DIR"
echo "Theme: $THEME_NAME"
echo "Starting the Wikinews reader..."
echo "This may take a few minutes on first run to index articles."
echo ""
echo "Usage: ./start_news.sh [-1|-2|-3|-4|-5|-6|-all]"
echo "  -1: Classic theme (Modern News UI)"
echo "  -2: Modern theme (Dark/Light mode)"
echo "  -3: Wikinews 2002 (Retro theme)"
echo "  -4: Wikinews 2001 (Ultra-Retro theme)"
echo "  -5: News 2000 (BBC News Style)"
echo "  -6: Base Minimal"
echo "  -all: Run all themes on separate ports"
echo ""
echo "Make sure you have Flask installed: pip install -r requirements.txt"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the Flask app
python3 news_app.py $THEME_ARG

