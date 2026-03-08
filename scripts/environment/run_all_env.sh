#!/bin/bash

# Script to start all three environments (Wiki, News, Webshop) with a specified version
# Usage: ./run_all_env.sh [version] [--wait]
#   version: 1-6 (default: 1)
#   --wait: Wait for processes (blocks terminal, default: returns immediately)
# Example: ./run_all_env.sh 1
# Example: ./run_all_env.sh 3
# Example: ./run_all_env.sh 1 --wait  # Blocks until Ctrl+C

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to check if a port is free
is_port_free() {
    local port=$1
    ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1
}

# Function to find the next available port starting from a given port
find_free_port() {
    local start_port=$1
    local port=$start_port
    while ! is_port_free $port; do
        port=$((port + 1))
        # Safety check to avoid infinite loop
        if [ $port -gt 65535 ]; then
            echo "Error: Could not find a free port starting from $start_port" >&2
            exit 1
        fi
    done
    echo $port
}

# Parse arguments
WAIT_FOR_PROCESSES=false
VERSION=1

# Parse arguments
for arg in "$@"; do
    if [[ "$arg" == "--wait" ]]; then
        WAIT_FOR_PROCESSES=true
    elif [[ "$arg" =~ ^[1-6]$ ]]; then
        VERSION="$arg"
    fi
done

# Validate version parameter
if ! [[ "$VERSION" =~ ^[1-6]$ ]]; then
    echo "Error: Version must be between 1 and 6"
    echo "Usage: ./run_all_env.sh [version]"
    echo "  version: 1-6 (default: 1)"
    echo ""
    echo "Examples:"
    echo "  ./run_all_env.sh 1    # Start all with version 1"
    echo "  ./run_all_env.sh 3    # Start all with version 3"
    exit 1
fi

echo "=========================================="
echo "Starting all environments (version $VERSION)"
echo "=========================================="
echo ""

# Find free ports starting from 5000
WIKI_PORT=$(find_free_port 5000)
NEWS_PORT=$(find_free_port $((WIKI_PORT + 1)))
WEBSHOP_PORT=$(find_free_port $((NEWS_PORT + 1)))

echo "Found free ports: Wiki=$WIKI_PORT, News=$NEWS_PORT, Webshop=$WEBSHOP_PORT"
echo ""

# Start Wiki (uses -1, -2, etc. format)
echo "Starting Wiki environment (theme -$VERSION) on port $WIKI_PORT..."
cd "$SCRIPT_DIR/env/wiki"
python3 wiki_app.py -$VERSION --port=$WIKI_PORT &
WIKI_PID=$!
echo "Wiki started (PID: $WIKI_PID) on http://localhost:$WIKI_PORT"
echo ""

# Start News (uses -1, -2, etc. format, supports 1-6)
echo "Starting News environment (theme -$VERSION) on port $NEWS_PORT..."
cd "$SCRIPT_DIR/env/news"
python3 news_app.py -$VERSION --port=$NEWS_PORT &
NEWS_PID=$!
echo "News started (PID: $NEWS_PID) on http://localhost:$NEWS_PORT"
echo ""

# Start Webshop (uses 1, 2, etc. format)
echo "Starting Webshop environment (theme $VERSION) on port $WEBSHOP_PORT..."
cd "$SCRIPT_DIR/env/webshop"
python -m web_agent_site.app $VERSION --port=$WEBSHOP_PORT --log --attrs &
WEBSHOP_PID=$!
echo "Webshop started (PID: $WEBSHOP_PID) on http://localhost:$WEBSHOP_PORT"
echo ""

echo "=========================================="
echo "All environments started!"
echo "=========================================="
echo "Wiki:   http://localhost:$WIKI_PORT (PID: $WIKI_PID)"
echo "News:   http://localhost:$NEWS_PORT (PID: $NEWS_PID)"
echo "Webshop: http://localhost:$WEBSHOP_PORT (PID: $WEBSHOP_PID)"
echo ""

# Export environment variables
export TW_WIKI="http://localhost:$WIKI_PORT"
export TW_NEWS="http://localhost:$NEWS_PORT"
export TW_WEBSHOP="http://localhost:$WEBSHOP_PORT/abc"
export TW_HOME="http://localhost:5100"

echo "Environment variables exported:"
echo "  TW_WIKI=$TW_WIKI"
echo "  TW_NEWS=$TW_NEWS"
echo "  TW_WEBSHOP=$TW_WEBSHOP"
echo "  TW_HOME=$TW_HOME"
echo ""

if [ "$WAIT_FOR_PROCESSES" = true ]; then
    echo "Press Ctrl+C to stop all environments"
    echo ""
    # Wait for all processes
    wait
else
    echo "All environments running in background."
    echo "To stop them, run: ./stop_all_ports.sh"
    echo ""
fi