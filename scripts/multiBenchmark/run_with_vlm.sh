#!/bin/bash
# Starts a VLM server for a model, runs one or more benchmark scripts across
# TimeWarp versions, then stops the VLM server.
#
# Usage: ./run_with_vlm.sh --model MODEL_PATH --scripts SCRIPTS [OPTIONS]
#   --model:      Path to model directory (required)
#   --scripts:    Comma-separated benchmark Python scripts (required)
#   --script:     Single benchmark script (alias for --scripts, can repeat)
#   --vlm-script: Path to VLM start script (default: startVLMmodel.sh)
#   --port:       Port number for VLM server (default: auto-detect free port)
#   --versions:   Comma-separated versions to run (default: 1,2,3,4,5,6)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VLM_SCRIPT="startVLMmodel.sh"
VLM_PORT=""
VLM_MODEL=""
VLM_PID=""
BENCHMARK_SCRIPTS=""
VLM_OUTPUT=""
VERSIONS="1,2,3,4,5,6"

while [[ $# -gt 0 ]]; do
    case $1 in
        --vlm-script)
            VLM_SCRIPT="$2"
            shift 2
            ;;
        --port)
            VLM_PORT="$2"
            shift 2
            ;;
        --model)
            VLM_MODEL="$2"
            shift 2
            ;;
        --scripts)
            if [ -n "$BENCHMARK_SCRIPTS" ]; then
                BENCHMARK_SCRIPTS="${BENCHMARK_SCRIPTS},$2"
            else
                BENCHMARK_SCRIPTS="$2"
            fi
            shift 2
            ;;
        --script)
            if [ -n "$BENCHMARK_SCRIPTS" ]; then
                BENCHMARK_SCRIPTS="${BENCHMARK_SCRIPTS},$2"
            else
                BENCHMARK_SCRIPTS="$2"
            fi
            shift 2
            ;;
        --versions)
            VERSIONS="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 --model MODEL_PATH --scripts SCRIPTS [OPTIONS]"
            echo "  --model:      Path to model directory (required)"
            echo "  --scripts:    Comma-separated benchmark Python scripts (required)"
            echo "  --script:     Single benchmark script (alias, can repeat)"
            echo "  --vlm-script: Path to VLM start script (default: startVLMmodel.sh)"
            echo "  --port:       Port for VLM server (default: auto-detect free port)"
            echo "  --versions:   Comma-separated versions to run (default: 1,2,3,4,5,6)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

if [ -z "$VLM_MODEL" ]; then
    echo "Error: --model parameter is required"
    exit 1
fi
if [ -z "$BENCHMARK_SCRIPTS" ]; then
    echo "Error: --scripts parameter is required (comma-separated benchmark Python scripts)"
    exit 1
fi
if [ ! -f "$VLM_SCRIPT" ]; then
    echo "Error: VLM script not found: $VLM_SCRIPT"
    exit 1
fi

find_free_port() {
    local start_port=${1:-8001}
    local end_port=${2:-9000}
    local port=$start_port
    while [ "$port" -le "$end_port" ]; do
        if ! lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
            echo "$port"
            return 0
        fi
        port=$((port + 1))
    done
    return 1
}

cleanup_temp_files() {
    if [ -n "$VLM_OUTPUT" ] && [ -f "$VLM_OUTPUT" ]; then
        rm -f "$VLM_OUTPUT"
    fi
}

stop_vlm_server() {
    cleanup_temp_files
    if [ -n "$VLM_PID" ] && ps -p $VLM_PID > /dev/null 2>&1; then
        echo "Stopping VLM server (PID: $VLM_PID)..."
        kill -TERM $VLM_PID 2>/dev/null || true
        sleep 3
        if ps -p $VLM_PID > /dev/null 2>&1; then
            echo "Force killing VLM server and children..."
            pkill -9 -P $VLM_PID 2>/dev/null || true
            kill -9 $VLM_PID 2>/dev/null || true
        fi
        VLM_PID=""
        echo "VLM server stopped"
    elif [ -n "$VLM_PORT" ]; then
        echo "Stopping VLM server on port $VLM_PORT..."
        PORT_PID=$(lsof -ti:$VLM_PORT 2>/dev/null | head -1)
        if [ -n "$PORT_PID" ]; then
            kill -TERM $PORT_PID 2>/dev/null || true
            sleep 2
            kill -9 $PORT_PID 2>/dev/null || true
        fi
    else
        echo "No VLM PID or port known; nothing to stop."
    fi
}

trap stop_vlm_server EXIT

source ~/.bashrc

echo "=========================================="
echo "Starting VLM Server"
echo "=========================================="
echo "VLM Script:        $VLM_SCRIPT"
echo "Model:             $VLM_MODEL"
echo "Benchmark Scripts: $BENCHMARK_SCRIPTS"
echo "Versions:          $VERSIONS"

if [ -z "$VLM_PORT" ]; then
    echo "No port specified, searching for a free port..."
    VLM_PORT=$(find_free_port 8001 9000)
    if [ -z "$VLM_PORT" ]; then
        echo "Error: Could not find a free port in range 8001-9000"
        exit 1
    fi
fi

echo "Using VLM server port: $VLM_PORT"
echo ""

echo "Activating conda environment: vlm"
if ! conda activate vlm; then
    echo "Error: Failed to activate conda environment 'vlm'"
    exit 1
fi

VLM_OUTPUT=$(mktemp)

echo "Running VLM server script (this may take 1-2 minutes)..."
echo "Logging to: $VLM_OUTPUT"
bash "$VLM_SCRIPT" --model "$VLM_MODEL" --port "$VLM_PORT" > "$VLM_OUTPUT" 2>&1
VLM_SCRIPT_EXIT_CODE=$?

if [ $VLM_SCRIPT_EXIT_CODE -ne 0 ]; then
    echo "Error: VLM server script failed with exit code $VLM_SCRIPT_EXIT_CODE"
    echo "VLM script output:"
    cat "$VLM_OUTPUT"
    exit 1
fi

VLM_PID=$(lsof -ti:$VLM_PORT 2>/dev/null | head -1)
if [ -z "$VLM_PID" ]; then
    echo "Error: Could not find VLM server process on port $VLM_PORT"
    echo "VLM script output:"
    cat "$VLM_OUTPUT"
    exit 1
fi

echo ""
echo "VLM Server started successfully!"
echo "  Port: $VLM_PORT"
echo "  Server PID: $VLM_PID"
echo ""

rm -f "$VLM_OUTPUT"
VLM_OUTPUT=""

echo "Waiting 60 seconds for model to fully initialize before starting experiments..."
sleep 60
echo ""

echo "Verifying VLM server is responding..."
if curl -s http://localhost:${VLM_PORT}/health > /dev/null 2>&1; then
    echo "VLM server is responding"
else
    echo "WARNING: VLM server health check failed, but process is running. Proceeding..."
fi
echo ""

if ! curl -s http://localhost:${VLM_PORT}/health > /dev/null 2>&1; then
    echo "ERROR: VLM server on port $VLM_PORT is not responding!"
    echo "Cannot proceed with experiments."
    exit 1
fi

echo "=========================================="
echo "Running Experiments"
echo "=========================================="

IFS=',' read -ra SCRIPT_LIST <<< "$BENCHMARK_SCRIPTS"
TOTAL_SCRIPTS=${#SCRIPT_LIST[@]}
SCRIPT_IDX=0

for BM_SCRIPT in "${SCRIPT_LIST[@]}"; do
    SCRIPT_IDX=$((SCRIPT_IDX + 1))
    echo ""
    echo "------------------------------------------"
    echo "Benchmark script [$SCRIPT_IDX/$TOTAL_SCRIPTS]: $BM_SCRIPT"
    echo "------------------------------------------"

    bash "${SCRIPT_DIR}/run_versions.sh" \
        --port "$VLM_PORT" \
        --model "$VLM_MODEL" \
        --script "$BM_SCRIPT" \
        --versions "$VERSIONS"
    EXPERIMENTS_EXIT_CODE=$?

    if [ $EXPERIMENTS_EXIT_CODE -eq 0 ]; then
        echo "Benchmark script $BM_SCRIPT completed successfully"
    else
        echo "Benchmark script $BM_SCRIPT failed with exit code $EXPERIMENTS_EXIT_CODE"
    fi
done

echo ""
echo "=========================================="
echo "All benchmark scripts completed"
echo "=========================================="

stop_vlm_server

echo ""
echo "VLM session completed!"
