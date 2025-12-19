#!/bin/bash

################################################################################
# expose_servers.sh - Make Wiki Servers Publicly Accessible
################################################################################
# This script exposes wiki theme servers to the internet using ngrok or cloudflared.
# 
# Prerequisites:
#   1. ngrok installed (https://ngrok.com/download) OR
#   2. cloudflared installed (https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/)
#   3. For ngrok: account + authtoken configured (ngrok config add-authtoken <TOKEN>)
#
# Usage:
#   ./expose_servers.sh [THEME] [OPTIONS]
#
# Theme Selection:
#   -1             Expose only theme 1
#   -2             Expose only theme 2
#   -3             Expose only theme 3
#   -4             Expose only theme 4
#   -5             Expose only theme 5
#   -6             Expose only theme 6
#   -all           Expose all 6 themes (default)
#
# Options:
#   --port PORT        Starting port for wiki servers (default: 5000)
#   --method METHOD    Tunneling method: ngrok, cloudflared (default: cloudflared)
#   --help             Show this help message
#
# Methods:
#   ngrok       - Uses ngrok (requires account, supports multiple tunnels)
#   cloudflared - Uses Cloudflare Tunnel (free, no account needed) [RECOMMENDED]
#
# Examples:
#   ./expose_servers.sh -1                          # Expose only theme 1
#   ./expose_servers.sh -3 --method ngrok           # Expose theme 3 with ngrok
#   ./expose_servers.sh -all                        # Expose all themes
#   ./expose_servers.sh -all --method cloudflared   # Expose all with Cloudflare
#   ./expose_servers.sh -2 --port 6000              # Expose theme 2 starting at port 6000
################################################################################

set -e  # Exit on error

# Default values
START_PORT=5000
METHOD="cloudflared"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
THEMES=()
EXPOSE_ALL=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -1|-2|-3|-4|-5|-6)
            THEME_NUM="${1:1}"  # Remove the leading dash
            THEMES+=($THEME_NUM)
            shift
            ;;
        -all|--all)
            THEMES=(1 2 3 4 5 6)
            EXPOSE_ALL=true
            shift
            ;;
        --port)
            START_PORT="$2"
            shift 2
            ;;
        --method)
            METHOD="$2"
            shift 2
            ;;
        --help)
            grep "^#" "$0" | grep -v "^#!/" | sed 's/^# //g' | sed 's/^#//g'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# If no theme specified, default to all
if [ ${#THEMES[@]} -eq 0 ]; then
    THEMES=(1 2 3 4 5 6)
    EXPOSE_ALL=true
fi

# Validate method
if [[ ! "$METHOD" =~ ^(ngrok|cloudflared)$ ]]; then
    echo "Error: Invalid method '$METHOD'"
    echo "Valid methods: ngrok, cloudflared"
    exit 1
fi

# Change to the script directory
cd "$SCRIPT_DIR"

echo "============================================================"
echo "Wiki Server Public Exposure Script"
echo "============================================================"
echo "Method: $METHOD"
echo "Starting port: $START_PORT"
if [ "$EXPOSE_ALL" = true ]; then
    echo "Themes: All (1-6)"
else
    echo "Themes: ${THEMES[@]}"
fi
echo "Working directory: $SCRIPT_DIR"
echo "============================================================"
echo ""

# Check if specific servers are running
check_server_running() {
    local port=$1
    nc -z localhost $port 2>/dev/null
    return $?
}

# Start wiki servers based on theme selection
start_wiki_servers() {
    echo "Starting wiki servers..."
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        echo "Error: python3 not found"
        exit 1
    fi
    
    if [ "$EXPOSE_ALL" = true ]; then
        # Start all 6 theme servers using the -all flag
        echo "Starting all wiki themes..."
        python3 wiki_app.py -all --port=$START_PORT &
        WIKI_PID=$!
        
        echo "Wiki servers starting (PID: $WIKI_PID)..."
        echo "Waiting for servers to be ready..."
        
        # Wait for all servers to be ready
        for i in {0..5}; do
            port=$((START_PORT + i))
            echo -n "  Waiting for server on port $port... "
            
            # Wait up to 60 seconds for each server
            for attempt in {1..60}; do
                if check_server_running $port; then
                    echo "✓ Ready"
                    break
                fi
                sleep 1
                
                if [ $attempt -eq 60 ]; then
                    echo "✗ Timeout"
                    echo "Error: Server on port $port failed to start"
                    kill $WIKI_PID 2>/dev/null || true
                    exit 1
                fi
            done
        done
    else
        # Start individual theme servers
        for theme in "${THEMES[@]}"; do
            port=$((START_PORT + theme - 1))
            
            echo "Starting theme $theme on port $port..."
            python3 wiki_app.py -$theme --port=$port &
            
            echo -n "  Waiting for server to be ready... "
            for attempt in {1..60}; do
                if check_server_running $port; then
                    echo "✓ Ready"
                    break
                fi
                sleep 1
                
                if [ $attempt -eq 60 ]; then
                    echo "✗ Timeout"
                    echo "Error: Server on port $port failed to start"
                    exit 1
                fi
            done
        done
    fi
    
    echo ""
    echo "✓ Wiki servers are running"
    echo ""
}

# Expose using ngrok
expose_with_ngrok() {
    echo "============================================================"
    echo "Exposing servers with ngrok"
    echo "============================================================"
    
    # Check if ngrok is installed
    if ! command -v ngrok &> /dev/null; then
        echo "Error: ngrok not found"
        echo ""
        echo "Please install ngrok:"
        echo "  1. Visit https://ngrok.com/download"
        echo "  2. Download and install ngrok"
        echo "  3. Sign up for a free account at https://ngrok.com"
        echo "  4. Run: ngrok config add-authtoken <YOUR_TOKEN>"
        exit 1
    fi
    
    echo "Starting ngrok tunnels..."
    echo ""
    
    # Store PIDs
    declare -a NGROK_PIDS
    
    # Start ngrok for each theme
    for theme in "${THEMES[@]}"; do
        port=$((START_PORT + theme - 1))
        
        echo "Starting tunnel for Theme $theme (port $port)..."
        ngrok http $port --log=stdout > /dev/null 2>&1 &
        NGROK_PID=$!
        NGROK_PIDS+=($NGROK_PID)
        
        sleep 2
    done
    
    sleep 3
    
    # Get tunnel URLs from ngrok API
    echo ""
    echo "Public URLs for wiki servers:"
    echo "============================================================"
    
    if command -v curl &> /dev/null; then
        # Get all tunnels from API
        TUNNELS=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null)
        
        for theme in "${THEMES[@]}"; do
            port=$((START_PORT + theme - 1))
            echo -n "Theme $theme (port $port): "
            
            # Extract URL for this port
            url=$(echo "$TUNNELS" | grep -o "https://[a-zA-Z0-9-]*\.ngrok-free\.app" | head -n $theme | tail -n 1 || echo "Check ngrok dashboard")
            
            echo "$url"
        done
    else
        echo "Visit http://localhost:4040 to see all tunnel URLs"
    fi
    
    echo "============================================================"
    echo ""
    echo "ngrok Web Interface: http://localhost:4040"
    echo ""
    echo "Note: Free ngrok accounts have limitations on concurrent tunnels."
    echo "For unlimited tunnels, consider using cloudflared (--method cloudflared)"
    echo ""
    
    # Cleanup function
    cleanup() {
        echo ""
        echo "Shutting down..."
        for pid in "${NGROK_PIDS[@]}"; do
            kill $pid 2>/dev/null || true
        done
        echo "✓ Cleanup complete"
    }
    
    trap cleanup EXIT INT TERM
    
    echo "Press Ctrl+C to stop all tunnels and servers"
    
    # Wait for any tunnel to exit
    for pid in "${NGROK_PIDS[@]}"; do
        wait $pid 2>/dev/null || true
    done
}

# Expose using Cloudflare Tunnel (cloudflared)
expose_with_cloudflared() {
    echo "============================================================"
    echo "Exposing servers with Cloudflare Tunnel"
    echo "============================================================"
    
    # Check if cloudflared is installed
    if ! command -v cloudflared &> /dev/null; then
        echo "Error: cloudflared not found"
        echo ""
        echo "Please install cloudflared:"
        echo "  Windows (WSL): wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        echo "                 chmod +x cloudflared-linux-amd64"
        echo "                 sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared"
        echo ""
        echo "  macOS:   brew install cloudflared"
        echo "  Linux:   https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
        exit 1
    fi
    
    echo "Starting Cloudflare Tunnels..."
    echo ""
    
    # Store PIDs and URLs
    declare -a TUNNEL_PIDS
    declare -a TUNNEL_URLS
    
    for theme in "${THEMES[@]}"; do
        port=$((START_PORT + theme - 1))
        
        echo "Starting tunnel for Theme $theme (port $port)..."
        
        # Start cloudflared tunnel in background and capture output
        TUNNEL_OUTPUT=$(mktemp)
        cloudflared tunnel --url http://localhost:$port > "$TUNNEL_OUTPUT" 2>&1 &
        TUNNEL_PID=$!
        TUNNEL_PIDS+=($TUNNEL_PID)
        
        # Wait for tunnel URL to appear in output
        echo -n "  Waiting for tunnel URL... "
        TUNNEL_URL=""
        for attempt in {1..30}; do
            if [ -f "$TUNNEL_OUTPUT" ]; then
                # Try multiple patterns for cloudflared URL
                TUNNEL_URL=$(grep -oE "https://[a-zA-Z0-9-]+\.trycloudflare\.com" "$TUNNEL_OUTPUT" 2>/dev/null | head -1)
                
                # If still empty, try alternative pattern
                if [ -z "$TUNNEL_URL" ]; then
                    TUNNEL_URL=$(grep -oE "https://[^[:space:]]+" "$TUNNEL_OUTPUT" 2>/dev/null | grep "trycloudflare" | head -1)
                fi
                
                # Check if we got a URL
                if [ -n "$TUNNEL_URL" ]; then
                    TUNNEL_URLS+=("$TUNNEL_URL")
                    echo "✓"
                    echo "  → $TUNNEL_URL"
                    break
                fi
            fi
            sleep 1
            
            if [ $attempt -eq 30 ]; then
                echo "✗ Timeout"
                echo "  Debug: Cloudflared output:"
                cat "$TUNNEL_OUTPUT" 2>/dev/null || echo "  (output file not found)"
                rm -f "$TUNNEL_OUTPUT"
                # Kill all started tunnels
                for pid in "${TUNNEL_PIDS[@]}"; do
                    kill $pid 2>/dev/null || true
                done
                exit 1
            fi
        done
        
        rm -f "$TUNNEL_OUTPUT"
    done
    
    echo ""
    echo "Public URLs for wiki servers:"
    echo "============================================================"
    for i in "${!THEMES[@]}"; do
        theme="${THEMES[$i]}"
        port=$((START_PORT + theme - 1))
        url="${TUNNEL_URLS[$i]}"
        if [ -z "$url" ]; then
            echo "Theme $theme (port $port): ⚠️  URL not captured (but tunnel may be running)"
        else
            echo "Theme $theme (port $port): ${url}"
        fi
    done
    echo "============================================================"
    echo ""
    
    # Check if we have URLs before creating .env
    if [ ${#TUNNEL_URLS[@]} -eq 0 ]; then
        echo "⚠️  Warning: No URLs were captured. Check cloudflared output above."
        echo "The tunnels may still be running. You can check manually by visiting:"
        echo "  http://localhost:$START_PORT"
    else
        # Create .env file with URLs
        create_env_file "${THEMES[@]}" "${TUNNEL_URLS[@]}"
    fi
    
    # Cleanup function
    cleanup() {
        echo ""
        echo "Shutting down tunnels..."
        for pid in "${TUNNEL_PIDS[@]}"; do
            kill $pid 2>/dev/null || true
        done
        echo "✓ Cleanup complete"
    }
    
    trap cleanup EXIT INT TERM
    
    echo "✓ All tunnels are running!"
    echo ""
    echo "Press Ctrl+C to stop all tunnels and servers"
    
    # Wait for any tunnel to exit
    for pid in "${TUNNEL_PIDS[@]}"; do
        wait $pid 2>/dev/null || true
    done
}

# Create .env file with tunnel URLs
create_env_file() {
    local themes=("$@")
    local num_themes=${#THEMES[@]}
    local urls=("${@:$((num_themes + 1))}")
    
    ENV_FILE="../../data_annotation/.env"
    ENV_BACKUP_FILE="../../data_annotation/.env.backup"
    
    echo ""
    echo "Creating/updating .env file..."
    
    # Backup existing .env if it exists
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$ENV_BACKUP_FILE"
        echo "  ✓ Backed up existing .env to .env.backup"
    fi
    
    # Read existing .env or create new
    if [ -f "$ENV_FILE" ]; then
        # Preserve non-WIKI variables
        grep -v "^WIKI[1-6]=" "$ENV_FILE" > "${ENV_FILE}.tmp" 2>/dev/null || touch "${ENV_FILE}.tmp"
    else
        touch "${ENV_FILE}.tmp"
    fi
    
    # Add header if file is new
    if [ ! -s "${ENV_FILE}.tmp" ]; then
        {
            echo "# Environment URLs - Generated by expose_servers.sh"
            echo "# Method: $METHOD"
            echo "# Generated: $(date)"
            echo ""
        } > "${ENV_FILE}.tmp"
    fi
    
    # Add/update WIKI URLs
    {
        echo ""
        echo "# Wiki URLs - Updated: $(date)"
        for i in "${!THEMES[@]}"; do
            theme="${THEMES[$i]}"
            url="${urls[$i]}"
            echo "WIKI${theme}=${url}"
        done
    } >> "${ENV_FILE}.tmp"
    
    # Move temp file to final location
    mv "${ENV_FILE}.tmp" "$ENV_FILE"
    
    echo "  ✓ Updated $ENV_FILE"
    echo ""
    echo "You can now use these URLs in your data collection scripts!"
    echo "Example: ./collect_batch.sh wiki 1"
    echo ""
}

# Main execution
echo "Checking if wiki servers are already running..."

# Check if servers need to be started
NEED_TO_START=false
for theme in "${THEMES[@]}"; do
    port=$((START_PORT + theme - 1))
    if ! check_server_running $port; then
        NEED_TO_START=true
        break
    fi
done

if [ "$NEED_TO_START" = true ]; then
    echo "Some servers are not running"
    start_wiki_servers
else
    echo "✓ All required servers are already running"
    echo ""
fi

# Expose servers based on method
case $METHOD in
    ngrok)
        expose_with_ngrok
        ;;
    cloudflared)
        expose_with_cloudflared
        ;;
    *)
        echo "Error: Unknown method '$METHOD'"
        exit 1
        ;;
esac
