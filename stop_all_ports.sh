#!/bin/bash

################################################################################
# stop_all_ports.sh - Stop All Port Forwarding and Tunnels
################################################################################
# This script stops all cloudflared tunnels, ngrok tunnels, and optionally
# the wiki/news/webshop servers running on local ports.
#
# Usage:
#   ./stop_all_ports.sh              # Stop tunnels AND all servers (default)
#   ./stop_all_ports.sh --tunnels-only # Stop only tunnels (keep servers running)
#   ./stop_all_ports.sh --servers     # Stop only servers (keep tunnels running)
#   ./stop_all_ports.sh --help        # Show this help message
################################################################################

STOP_SERVERS=true
STOP_TUNNELS=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all|--kill-all)
            STOP_SERVERS=true
            STOP_TUNNELS=true
            shift
            ;;
        --servers|--kill-servers)
            STOP_SERVERS=true
            STOP_TUNNELS=false
            shift
            ;;
        --tunnels-only|--tunnels)
            STOP_SERVERS=false
            STOP_TUNNELS=true
            shift
            ;;
        --help|-h)
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

echo "============================================================"
if [ "$STOP_TUNNELS" = true ] && [ "$STOP_SERVERS" = true ]; then
    echo "Stopping All Port Forwarding, Tunnels, and Servers"
elif [ "$STOP_TUNNELS" = true ]; then
    echo "Stopping All Port Forwarding and Tunnels"
elif [ "$STOP_SERVERS" = true ]; then
    echo "Stopping All Servers"
fi
echo "============================================================"
echo ""

# Function to check if a process is running
check_process() {
    pgrep -f "$1" > /dev/null 2>&1
    return $?
}

# Stop tunnels if requested
if [ "$STOP_TUNNELS" = true ]; then
    # Stop cloudflared tunnels
    echo "1. Stopping cloudflared tunnels..."
    CLOUDFLARED_COUNT=$(pgrep -f "cloudflared tunnel" | wc -l)
    if [ "$CLOUDFLARED_COUNT" -gt 0 ]; then
        pkill -f "cloudflared tunnel" 2>/dev/null
        sleep 1
        # Force kill if still running
        pkill -9 -f "cloudflared tunnel" 2>/dev/null || true
        echo "   ✓ Stopped $CLOUDFLARED_COUNT cloudflared tunnel(s)"
    else
        echo "   ✓ No cloudflared tunnels running"
    fi

    # Stop ngrok tunnels
    echo "2. Stopping ngrok tunnels..."
    NGROK_COUNT=$(pgrep -f "ngrok http" | wc -l)
    if [ "$NGROK_COUNT" -gt 0 ]; then
        pkill -f "ngrok http" 2>/dev/null
        sleep 1
        # Force kill if still running
        pkill -9 -f "ngrok http" 2>/dev/null || true
        echo "   ✓ Stopped $NGROK_COUNT ngrok tunnel(s)"
    else
        echo "   ✓ No ngrok tunnels running"
    fi

    # Stop any remaining cloudflared processes
    echo "3. Stopping any remaining cloudflared processes..."
    REMAINING_CLOUDFLARED=$(pgrep cloudflared | wc -l)
    if [ "$REMAINING_CLOUDFLARED" -gt 0 ]; then
        pkill cloudflared 2>/dev/null
        sleep 1
        pkill -9 cloudflared 2>/dev/null || true
        echo "   ✓ Stopped $REMAINING_CLOUDFLARED remaining cloudflared process(es)"
    else
        echo "   ✓ No remaining cloudflared processes"
    fi

    # Stop any remaining ngrok processes
    echo "4. Stopping any remaining ngrok processes..."
    REMAINING_NGROK=$(pgrep ngrok | wc -l)
    if [ "$REMAINING_NGROK" -gt 0 ]; then
        pkill ngrok 2>/dev/null
        sleep 1
        pkill -9 ngrok 2>/dev/null || true
        echo "   ✓ Stopped $REMAINING_NGROK remaining ngrok process(es)"
    else
        echo "   ✓ No remaining ngrok processes"
    fi
fi

# Stop servers if requested
if [ "$STOP_SERVERS" = true ]; then
    echo ""
    if [ "$STOP_TUNNELS" = true ]; then
        echo "5. Stopping wiki/news/webshop servers..."
    else
        echo "1. Stopping wiki/news/webshop servers..."
    fi
    
    # Stop wiki servers (typically on ports 5000-5005)
    # Match python3 wiki_app.py or python wiki_app.py with any arguments
    WIKI_COUNT=$(pgrep -f "wiki_app\.py" | wc -l)
    if [ "$WIKI_COUNT" -gt 0 ]; then
        pkill -f "wiki_app\.py" 2>/dev/null || true
        sleep 1
        pkill -9 -f "wiki_app\.py" 2>/dev/null || true
        echo "   ✓ Stopped $WIKI_COUNT wiki server process(es)"
    else
        echo "   ✓ No wiki servers running"
    fi
    
    # Stop news servers
    # Match python3 news_app.py or python news_app.py with any arguments
    NEWS_COUNT=$(pgrep -f "news_app\.py" | wc -l)
    if [ "$NEWS_COUNT" -gt 0 ]; then
        pkill -f "news_app\.py" 2>/dev/null || true
        sleep 1
        pkill -9 -f "news_app\.py" 2>/dev/null || true
        echo "   ✓ Stopped $NEWS_COUNT news server process(es)"
    else
        echo "   ✓ No news servers running"
    fi
    
    # Stop webshop servers (match web_agent_site.app, web_agent_site/app.py, run_dev.sh, run_prod.sh)
    # Count processes matching any webshop pattern (count each separately and combine)
    WEBSHOP_COUNT_1=$(pgrep -f "web_agent_site\.app" 2>/dev/null | wc -l)
    WEBSHOP_COUNT_2=$(pgrep -f "web_agent_site/app\.py" 2>/dev/null | wc -l)
    WEBSHOP_COUNT_3=$(pgrep -f "run_dev\.sh" 2>/dev/null | wc -l)
    WEBSHOP_COUNT_4=$(pgrep -f "run_prod\.sh" 2>/dev/null | wc -l)
    WEBSHOP_COUNT=$((WEBSHOP_COUNT_1 + WEBSHOP_COUNT_2 + WEBSHOP_COUNT_3 + WEBSHOP_COUNT_4))
    if [ "$WEBSHOP_COUNT" -gt 0 ]; then
        # Kill processes matching web_agent_site.app (python -m web_agent_site.app)
        pkill -f "web_agent_site\.app" 2>/dev/null || true
        # Kill processes matching web_agent_site/app.py (direct python execution)
        pkill -f "web_agent_site/app\.py" 2>/dev/null || true
        # Kill processes matching run_dev.sh
        pkill -f "run_dev\.sh" 2>/dev/null || true
        # Kill processes matching run_prod.sh
        pkill -f "run_prod\.sh" 2>/dev/null || true
        sleep 1
        # Force kill any remaining
        pkill -9 -f "web_agent_site\.app" 2>/dev/null || true
        pkill -9 -f "web_agent_site/app\.py" 2>/dev/null || true
        pkill -9 -f "run_dev\.sh" 2>/dev/null || true
        pkill -9 -f "run_prod\.sh" 2>/dev/null || true
        echo "   ✓ Stopped $WEBSHOP_COUNT webshop server process(es)"
    else
        echo "   ✓ No webshop servers running"
    fi
    
    # Stop homepage servers
    HOMEPAGE_COUNT=$(pgrep -f "homepage_app\.py" | wc -l)
    if [ "$HOMEPAGE_COUNT" -gt 0 ]; then
        pkill -f "homepage_app\.py" 2>/dev/null || true
        sleep 1
        pkill -9 -f "homepage_app\.py" 2>/dev/null || true
        echo "   ✓ Stopped $HOMEPAGE_COUNT homepage server process(es)"
    else
        echo "   ✓ No homepage servers running"
    fi
fi

echo ""
echo "============================================================"
echo "✓ Cleanup Complete!"
echo "============================================================"
echo ""

# Show what's still running on common ports
echo "Force-stopping any process on ports 5000-5100..."
for port in {5000..5100}; do
    if command -v lsof > /dev/null 2>&1; then
        PIDS=$(lsof -ti:$port 2>/dev/null | tr '\n' ' ')
        if [ -n "$PIDS" ]; then
            echo "   Killing port $port (PIDs: $PIDS)"
            kill $PIDS 2>/dev/null || true
            sleep 0.2
            kill -9 $PIDS 2>/dev/null || true
        fi
    elif command -v fuser > /dev/null 2>&1; then
        if fuser $port/tcp > /dev/null 2>&1; then
            echo "   Killing port $port (fuser)"
            fuser -k $port/tcp 2>/dev/null || true
        fi
    fi
done

echo "Checking ports 5000-5100..."
for port in {5000..5100}; do
    if command -v lsof > /dev/null 2>&1; then
        PID=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$PID" ]; then
            PROCESS=$(ps -p $PID -o comm= 2>/dev/null | head -1)
            echo "   ⚠️  Port $port: Process $PID ($PROCESS)"
        fi
    elif command -v netstat > /dev/null 2>&1; then
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            echo "   ⚠️  Port $port: In use (run 'netstat -tuln | grep $port' for details)"
        fi
    fi
done

echo ""
echo "Done!"

