########## Work in progress ########


#!/bin/bash

# Homepage UI Launcher Script
# Usage: ./start_homepage.sh [theme_number|theme_name|all]
#
# Theme options:
#   1 or fshape      - F-Shape Layout
#   2 or 2column     - Two Column Layout
#   3 or interactive - Interactive Slides Layout
#   4 or magazine    - Magazine Layout
#   5 or classic     - Classic Grid Layout
#   all              - Run all themes on successive ports
#
# Examples:
#   ./start_homepage.sh              # Run classic theme (default)
#   ./start_homepage.sh 1            # Run F-shape layout
#   ./start_homepage.sh interactive  # Run interactive slides layout
#   ./start_homepage.sh all          # Run all themes

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "=========================================="
echo "Homepage UI Launcher"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if Flask is installed
if ! python3 -c "import flask" &> /dev/null
then
    echo "Flask is not installed. Installing dependencies..."
    pip3 install -r "$SCRIPT_DIR/requirements.txt"
fi

# Run the app
cd "$SCRIPT_DIR"
python3 homepage_app.py "$@"
