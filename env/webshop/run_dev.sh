#!/bin/bash
# Usage: ./run_dev.sh [theme_number|theme_name|all] [--port=PORT]
# Theme numbers: 1=webshop2000, 2=webshop2005, 3=webshop2010, 4=webshop2015, 5=webshop2025, 6=classic
# Or use theme names directly: webshop2000, webshop2005, webshop2010, webshop2015, webshop2025, classic
# Use "all" to run all 6 servers on successive ports (starting from --port if provided, or auto-detected)
# Example: ./run_dev.sh 6 --port=3000
# Example: ./run_dev.sh classic
# Example: ./run_dev.sh all --port=3000

export FLASK_ENV=development
cd "$(dirname "$0")"
THEME_ARG=${1:-6}  # Default to classic (theme 6)
shift  # Remove theme arg from $@
python -m web_agent_site.app $THEME_ARG --log --attrs "$@"
