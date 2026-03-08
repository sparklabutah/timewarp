#!/bin/bash
# Script to run experiments sequentially with different TimeWarp versions
# Each experiment waits for the previous one to complete before starting
#
# Usage: ./run_experiments.sh --port PORT --model MODEL_PATH --script SCRIPT_PATH
#   --port: Port number for vLLM API (required)
#   --model: Path to model directory (required)
#   --script: Path to benchmark Python script (required)

# Get the directory where this script is located (for resolving relative paths)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export OPENAI_API_KEY="ENTER YOUR OPENAI API KEY HERE"
# Parse command-line arguments
PORT=""
MODEL=""
SCRIPT=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 --port PORT --model MODEL_PATH --script SCRIPT_PATH"
            echo "  --port: Port number for vLLM API (required)"
            echo "  --model: Path to model directory (required)"
            echo "  --script: Path to benchmark Python script (required)"
            exit 0
            ;;
        --script)
            SCRIPT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$PORT" ]; then
    echo "Error: --port parameter is required"
    echo "Usage: $0 --port PORT --model MODEL_PATH --script SCRIPT_PATH"
    exit 1
fi

if [ -z "$MODEL" ]; then
    echo "Error: --model parameter is required"
    echo "Usage: $0 --port PORT --model MODEL_PATH --script SCRIPT_PATH"
    exit 1
fi

if [ -z "$SCRIPT" ]; then
    echo "Error: --script parameter is required"
    echo "Usage: $0 --port PORT --model MODEL_PATH --script SCRIPT_PATH"
    exit 1
fi

# Validate port is a number
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "Error: Port must be a number, got: '$PORT'"
    echo "Usage: $0 --port PORT --model MODEL_PATH"
    exit 1
fi

# Source .bashrc to initialize conda
source ~/.bashrc

# Track PIDs of TimeWarp servers we start
TW_PIDS=()

# Safely kill only PIDs that still look like TimeWarp env processes
safe_kill_timewarp_pid() {
    local pid="$1"

    # PID no longer exists
    if [ ! -d "/proc/$pid" ]; then
        return 0
    fi

    # Read command line; if unreadable, skip
    local cmdline
    cmdline="$(tr '\0' ' ' < /proc/"$pid"/cmdline 2>/dev/null || echo "")"

    # Extra safety: only kill if the command line looks like one of our TimeWarp envs
    # (python wiki_app.py / news_app.py / web_agent_site.app)
    if echo "$cmdline" | grep -Eq 'wiki_app\.py|news_app\.py|web_agent_site\.app'; then
        kill "$pid" 2>/dev/null || true
    else
        echo "Skipping PID $pid (does not look like a TimeWarp env process): $cmdline"
    fi
}

# Function to stop TimeWarp environments we started (only those for the current experiment)
stop_timewarp() {
    if [ ${#TW_PIDS[@]} -gt 0 ]; then
        echo "Stopping TimeWarp environments for this experiment (PIDs: ${TW_PIDS[@]})..."
        for pid in "${TW_PIDS[@]}"; do
            safe_kill_timewarp_pid "$pid"
        done
        # Give them time to shut down gracefully
        sleep 2
        # Force kill if still running
        for pid in "${TW_PIDS[@]}"; do
            # Re-check the PID and only force kill if it still looks like our process
            if [ -d "/proc/$pid" ]; then
                local cmdline
                cmdline="$(tr '\0' ' ' < /proc/"$pid"/cmdline 2>/dev/null || echo "")"
                if echo "$cmdline" | grep -Eq 'wiki_app\.py|news_app\.py|web_agent_site\.app'; then
                    kill -9 "$pid" 2>/dev/null || true
                fi
            fi
        done
        TW_PIDS=()
    fi
}

# Function to run a single experiment
run_experiment() {
    local version=$1
    local port=$2
    local model=$3
    local script=$4
    
    # Validate arguments
    if [ -z "$version" ] || [ -z "$port" ] || [ -z "$model" ] || [ -z "$script" ]; then
        echo "Error: run_experiment requires version, port, model, and script arguments"
        echo "Usage: run_experiment <version> <port> <model> <script>"
        return 1
    fi
    
    # Validate port is a number
    if ! [[ "$port" =~ ^[0-9]+$ ]]; then
        echo "Error: Port must be a number, got: '$port'"
        return 1
    fi
    
    echo "=========================================="
    echo "Starting experiment version $version"
    echo "=========================================="
    
    # Stop previous TimeWarp environments
    # stop_timewarp
    
    # Stop all TimeWarp environments using the stop_all_ports script
    echo "Stopping all TimeWarp environments..."
    if [ -f "/scratch/general/nfs1/u1592009/TimeWarp/stop_all_ports.sh" ]; then
        bash "/scratch/general/nfs1/u1592009/TimeWarp/stop_all_ports.sh" || true
    else
        echo "Warning: /scratch/general/nfs1/u1592009/TimeWarp/stop_all_ports.sh not found, skipping..."
    fi
    
    # Start TimeWarp environments for this version
    echo "Starting TimeWarp environments (version $version)..."
    if ! conda activate timewarp; then
        echo "Error: Failed to activate conda environment 'timewarp'"
        return 1
    fi
    
    # Use a unique log file per run to avoid clobbering / mixing with other runs
    local LOG_FILE="/tmp/timewarp_startup_v${version}_$$.log"
    echo "Using TimeWarp startup log: $LOG_FILE"

    # Run the script in background to start the servers (use absolute path)
    bash "${SCRIPT_DIR}/TimeWarp/run_all_env.sh" "$version" > "$LOG_FILE" 2>&1 &
    STARTUP_PID=$!
    
    # Wait a bit for servers to start and write their ports
    echo "Waiting for TimeWarp v${version} servers to start..."
    sleep 10  # Increased wait time to ensure servers are fully up
    
    # Extract PIDs from the log file (they're printed as "PID: XXXX")
    TW_PIDS=($(grep -oP 'PID: \K\d+' "$LOG_FILE"))
    echo "Started TimeWarp servers with PIDs: ${TW_PIDS[@]}"
    
    # Extract the environment variables from the log
    export TW_WIKI=$(grep "TW_WIKI=" "$LOG_FILE" | cut -d'=' -f2)
    export TW_NEWS=$(grep "TW_NEWS=" "$LOG_FILE" | cut -d'=' -f2)
    export TW_WEBSHOP=$(grep "TW_WEBSHOP=" "$LOG_FILE" | cut -d'=' -f2)
    export TW_HOME=$(grep "TW_HOME=" "$LOG_FILE" | cut -d'=' -f2)
    
    echo "TimeWarp environments ready!"
    echo "  TW_WIKI=$TW_WIKI"
    echo "  TW_NEWS=$TW_NEWS"
    echo "  TW_WEBSHOP=$TW_WEBSHOP"
    echo "  TW_HOME=$TW_HOME"
    
    # Verify servers are responding
    if [ -n "$TW_WIKI" ]; then
        MAX_WAIT=30
        WAIT_COUNT=0
        echo "Checking if TimeWarp servers are responding..."
        while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
            if curl -s "${TW_WIKI}" > /dev/null 2>&1; then
                echo "✓ TimeWarp servers are responding"
                break
            fi
            sleep 1
            WAIT_COUNT=$((WAIT_COUNT + 1))
        done
        if [ $WAIT_COUNT -eq $MAX_WAIT ]; then
            echo "✗ WARNING: TimeWarp servers may not be ready, proceeding anyway..."
        fi
    fi
    echo ""
    
    # Run benchmark (this will block until completion - ensures sequential execution)
    echo "Running benchmark (version $version, port $port, model $model)..."
    if ! conda activate agentlab; then
        echo "Error: Failed to activate conda environment 'agentlab'"
        # Clean up log file before returning
        rm -f "$LOG_FILE"
        return 1
    fi
    
    # Explicitly pass environment variables to Python process
    TW_WIKI=$TW_WIKI TW_NEWS=$TW_NEWS TW_WEBSHOP=$TW_WEBSHOP TW_HOME=$TW_HOME \
        python "$script" --port $port --version $version --model "$model"
    BENCHMARK_EXIT_CODE=$?
    
    # Check if benchmark completed successfully
    if [ $BENCHMARK_EXIT_CODE -eq 0 ]; then
        echo "✓ Experiment version $version completed successfully"
    else
        echo "✗ Experiment version $version failed with exit code $BENCHMARK_EXIT_CODE"
    fi
    
    # Stop only the TimeWarp environments used for this experiment
    stop_timewarp
    
    # Clean up the log file
    rm -f "$LOG_FILE"
    
    echo "=========================================="
    echo ""
}

# Run experiments sequentially
run_experiment 1 $PORT "$MODEL" "$SCRIPT"
run_experiment 2 $PORT "$MODEL" "$SCRIPT"
run_experiment 3 $PORT "$MODEL" "$SCRIPT"
run_experiment 4 $PORT "$MODEL" "$SCRIPT"
run_experiment 5 $PORT "$MODEL" "$SCRIPT"
run_experiment 6 $PORT "$MODEL" "$SCRIPT"


# Stop the last set of TimeWarp environments
# stop_timewarp

echo "All experiments completed!"