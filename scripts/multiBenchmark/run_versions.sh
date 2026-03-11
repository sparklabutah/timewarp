#!/bin/bash
# Runs experiments sequentially across TimeWarp versions for a single model.
# Each experiment waits for the previous one to complete before starting.
#
# Usage: ./run_versions.sh --port PORT --model MODEL_PATH --script SCRIPT_PATH [--versions VERSIONS]
#   --port:     Port number for vLLM API (required)
#   --model:    Path to model directory (required)
#   --script:   Path to benchmark Python script (required)
#   --versions: Comma-separated list of versions to run (default: 1,2,3,4,5,6)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PORT=""
MODEL=""
SCRIPT=""
VERSIONS="1,2,3,4,5,6"

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
        --script)
            SCRIPT="$2"
            shift 2
            ;;
        --versions)
            VERSIONS="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 --port PORT --model MODEL_PATH --script SCRIPT_PATH [--versions VERSIONS]"
            echo "  --port:     Port number for vLLM API (required)"
            echo "  --model:    Path to model directory (required)"
            echo "  --script:   Path to benchmark Python script (required)"
            echo "  --versions: Comma-separated list of versions, e.g. '1,2,3' (default: 1,2,3,4,5,6)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

if [ -z "$PORT" ]; then
    echo "Error: --port parameter is required"
    exit 1
fi
if [ -z "$MODEL" ]; then
    echo "Error: --model parameter is required"
    exit 1
fi
if [ -z "$SCRIPT" ]; then
    echo "Error: --script parameter is required"
    exit 1
fi
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "Error: Port must be a number, got: '$PORT'"
    exit 1
fi

IFS=',' read -ra VERSION_LIST <<< "$VERSIONS"
for v in "${VERSION_LIST[@]}"; do
    if ! [[ "$v" =~ ^[1-6]$ ]]; then
        echo "Error: Invalid version '$v'. Must be between 1 and 6."
        exit 1
    fi
done

source ~/.bashrc

TW_PIDS=()

safe_kill_timewarp_pid() {
    local pid="$1"

    if [ ! -d "/proc/$pid" ]; then
        return 0
    fi

    local cmdline
    cmdline="$(tr '\0' ' ' < /proc/"$pid"/cmdline 2>/dev/null || echo "")"

    if echo "$cmdline" | grep -Eq 'wiki_app\.py|news_app\.py|web_agent_site\.app'; then
        kill "$pid" 2>/dev/null || true
    else
        echo "Skipping PID $pid (does not look like a TimeWarp env process): $cmdline"
    fi
}

stop_timewarp() {
    if [ ${#TW_PIDS[@]} -gt 0 ]; then
        echo "Stopping TimeWarp environments for this experiment (PIDs: ${TW_PIDS[@]})..."
        for pid in "${TW_PIDS[@]}"; do
            safe_kill_timewarp_pid "$pid"
        done
        sleep 2
        for pid in "${TW_PIDS[@]}"; do
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

run_experiment() {
    local version=$1
    local port=$2
    local model=$3
    local script=$4

    if [ -z "$version" ] || [ -z "$port" ] || [ -z "$model" ] || [ -z "$script" ]; then
        echo "Error: run_experiment requires version, port, model, and script arguments"
        return 1
    fi
    if ! [[ "$port" =~ ^[0-9]+$ ]]; then
        echo "Error: Port must be a number, got: '$port'"
        return 1
    fi

    echo "=========================================="
    echo "Starting experiment version $version"
    echo "=========================================="

    echo "Stopping all TimeWarp environments..."
    if [ -f "/scratch/general/nfs1/u1592009/TimeWarp/stop_all_ports.sh" ]; then
        bash "/scratch/general/nfs1/u1592009/TimeWarp/stop_all_ports.sh" || true
    else
        echo "Warning: /scratch/general/nfs1/u1592009/TimeWarp/stop_all_ports.sh not found, skipping..."
    fi

    echo "Starting TimeWarp environments (version $version)..."
    if ! conda activate timewarp; then
        echo "Error: Failed to activate conda environment 'timewarp'"
        return 1
    fi

    local LOG_FILE="/tmp/timewarp_startup_v${version}_$$.log"
    echo "Using TimeWarp startup log: $LOG_FILE"

    bash "${SCRIPT_DIR}/TimeWarp/run_all_env.sh" "$version" > "$LOG_FILE" 2>&1 &
    STARTUP_PID=$!

    echo "Waiting for TimeWarp v${version} servers to start..."
    sleep 10

    TW_PIDS=($(grep -oP 'PID: \K\d+' "$LOG_FILE"))
    echo "Started TimeWarp servers with PIDs: ${TW_PIDS[@]}"

    export TW_WIKI=$(grep "TW_WIKI=" "$LOG_FILE" | cut -d'=' -f2)
    export TW_NEWS=$(grep "TW_NEWS=" "$LOG_FILE" | cut -d'=' -f2)
    export TW_WEBSHOP=$(grep "TW_WEBSHOP=" "$LOG_FILE" | cut -d'=' -f2)
    export TW_HOME=$(grep "TW_HOME=" "$LOG_FILE" | cut -d'=' -f2)

    echo "TimeWarp environments ready!"
    echo "  TW_WIKI=$TW_WIKI"
    echo "  TW_NEWS=$TW_NEWS"
    echo "  TW_WEBSHOP=$TW_WEBSHOP"
    echo "  TW_HOME=$TW_HOME"

    if [ -n "$TW_WIKI" ]; then
        MAX_WAIT=30
        WAIT_COUNT=0
        echo "Checking if TimeWarp servers are responding..."
        while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
            if curl -s "${TW_WIKI}" > /dev/null 2>&1; then
                echo "TimeWarp servers are responding"
                break
            fi
            sleep 1
            WAIT_COUNT=$((WAIT_COUNT + 1))
        done
        if [ $WAIT_COUNT -eq $MAX_WAIT ]; then
            echo "WARNING: TimeWarp servers may not be ready, proceeding anyway..."
        fi
    fi
    echo ""

    echo "Running benchmark (version $version, port $port, model $model)..."
    if ! conda activate agentlab; then
        echo "Error: Failed to activate conda environment 'agentlab'"
        rm -f "$LOG_FILE"
        return 1
    fi

    TW_WIKI=$TW_WIKI TW_NEWS=$TW_NEWS TW_WEBSHOP=$TW_WEBSHOP TW_HOME=$TW_HOME \
        python "$script" --port $port --version $version --model "$model"
    BENCHMARK_EXIT_CODE=$?

    if [ $BENCHMARK_EXIT_CODE -eq 0 ]; then
        echo "Experiment version $version completed successfully"
    else
        echo "Experiment version $version failed with exit code $BENCHMARK_EXIT_CODE"
    fi

    stop_timewarp
    rm -f "$LOG_FILE"

    echo "=========================================="
    echo ""
}

echo "Running versions: ${VERSION_LIST[*]}"
for v in "${VERSION_LIST[@]}"; do
    run_experiment "$v" "$PORT" "$MODEL" "$SCRIPT"
done

echo "All experiments completed!"
