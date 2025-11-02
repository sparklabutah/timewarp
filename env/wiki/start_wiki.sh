############## Scripts in progress ##########

#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Determine theme
THEME_ARG=""
THEME_NAME="Classic"

if [ "$1" = "-1" ]; then
    THEME_ARG="-1"
    THEME_NAME="Classic (Wikipedia-style)"
elif [ "$1" = "-2" ]; then
    THEME_ARG="-2"
    THEME_NAME="Modern (Dark/Light mode)"
elif [ "$1" = "-3" ]; then
    THEME_ARG="-3"
    THEME_NAME="Wikipedia 2002 (Retro)"
elif [ "$1" = "-4" ]; then
    THEME_ARG="-4"
    THEME_NAME="Wikipedia 2001 (Ultra-Retro)"
elif [ "$1" = "-5" ]; then
    THEME_ARG="-5"
    THEME_NAME="Wikipedia 2004"
elif [ "$1" = "-6" ]; then
    THEME_ARG="-6"
    THEME_NAME="Wikipedia 2025 (Modern)"
else
    THEME_ARG="-1"
    THEME_NAME="Classic (Wikipedia-style) [default]"
fi

echo "========================================"
echo "Simple Wikipedia UI"
echo "========================================"
echo ""
echo "Working directory: $SCRIPT_DIR"
echo "Theme: $THEME_NAME"
echo "Starting the Wikipedia reader..."
echo "This may take a few minutes on first run to index articles."
echo ""
echo "Usage: ./start_wiki.sh [-1|-2|-3|-4|-5|-6]"
echo "  -1: Classic theme (Wikipedia-style)"
echo "  -2: Modern theme (Dark/Light mode)"
echo "  -3: Wikipedia 2002 (Retro theme)"
echo "  -4: Wikipedia 2001 (Ultra-Retro theme)"
echo "  -5: Wikipedia 2004"
echo "  -6: Wikipedia 2025 (Modern)"
echo ""

python3 wiki_app.py $THEME_ARG

