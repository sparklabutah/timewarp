#!/bin/bash
# Start WebShop application

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Determine theme
THEME_ARG=""
THEME_NAME="Classic"

if [ "$1" = "-1" ]; then
    THEME_ARG="-1"
    THEME_NAME="WebShop 2000"
elif [ "$1" = "-2" ]; then
    THEME_ARG="-2"
    THEME_NAME="WebShop 2005"
elif [ "$1" = "-3" ]; then
    THEME_ARG="-3"
    THEME_NAME="WebShop 2010"
elif [ "$1" = "-4" ]; then
    THEME_ARG="-4"
    THEME_NAME="WebShop 2015"
elif [ "$1" = "-5" ]; then
    THEME_ARG="-5"
    THEME_NAME="WebShop 2025"
elif [ "$1" = "-6" ]; then
    THEME_ARG="-6"
    THEME_NAME="Classic"
elif [ "$1" = "-all" ] || [ "$1" = "--all" ]; then
    THEME_ARG="-all"
    THEME_NAME="All themes (servers 1-6)"
else
    THEME_ARG="-6"
    THEME_NAME="Classic [default]"
fi

echo "========================================"
echo "WebShop UI"
echo "========================================"
echo ""
echo "Working directory: $SCRIPT_DIR"
echo "Theme: $THEME_NAME"
echo "Starting the WebShop..."
echo ""
echo "Usage: ./start_webshop.sh [-1|-2|-3|-4|-5|-6|-all]"
echo "  -1: WebShop 2000"
echo "  -2: WebShop 2005"
echo "  -3: WebShop 2010"
echo "  -4: WebShop 2015"
echo "  -5: WebShop 2025"
echo "  -6: Classic (default)"
echo "  -all: Run all themes on separate ports"
echo ""
echo "Make sure you have Flask installed: pip install -r requirements.txt"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the Flask app as a module so Python can find the web_agent_site package
python3 -m web_agent_site.app $THEME_ARG

