#!/bin/bash
# Script to run training with VLM server
# 1. Activates conda environment vlm
# 2. Runs a VLM server script
# 3. Runs run_experiments.sh with the VLM server port
# 4. Stops the VLM server when done
#
# Usage: ./run_training.sh --model MODEL_PATH [--vlm-script SCRIPT] [--port PORT] [--script BENCHMARK_SCRIPT]
#   --model: Path to model directory (required, will be passed to VLM script as --model)
#   --vlm-script: Path to VLM start script (optional, default: vlm/startVLMmodel.sh)
#   --port: Port number for VLM server (optional, script default will be used if not provided)
#   --script: Path to benchmark Python script for run_experiments.sh (required)

# Get the directory where this script is located (for resolving relative paths)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
VLM_SCRIPT="/scratch/general/nfs1/u1592009/vlm/startVLMmodel.sh"
VLM_PORT=""
VLM_MODEL=""
VLM_PID=""
BENCHMARK_SCRIPT=""
VLM_OUTPUT=""

# Parse command-line arguments
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
        --script)
            BENCHMARK_SCRIPT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 --model MODEL_PATH [--vlm-script SCRIPT] [--port PORT] [--script BENCHMARK_SCRIPT]"
            echo "  --model: Path to model directory (required, will be passed to VLM script)"
            echo "  --vlm-script: Path to VLM start script (optional, default: vlm/startVLMmodel.sh)"
            echo "  --port: Port number for VLM server (optional)"
            echo "  --script: Path to benchmark Python script for run_experiments.sh (required)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate model path is provided
if [ -z "$VLM_MODEL" ]; then
    echo "Error: --model parameter is required"
    echo "Usage: $0 --model MODEL_PATH [--vlm-script SCRIPT] [--port PORT] [--script BENCHMARK_SCRIPT]"
    exit 1
fi

# Validate benchmark script is provided
if [ -z "$BENCHMARK_SCRIPT" ]; then
    echo "Error: --script parameter is required (benchmark Python script for run_experiments.sh)"
    echo "Usage: $0 --model MODEL_PATH [--vlm-script SCRIPT] [--port PORT] [--script BENCHMARK_SCRIPT]"
    exit 1
fi

# Validate VLM script exists
if [ ! -f "$VLM_SCRIPT" ]; then
    echo "Error: VLM script not found: $VLM_SCRIPT"
    exit 1
fi

# Function to find a free TCP port
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

# Function to clean up temp files
cleanup_temp_files() {
    if [ -n "$VLM_OUTPUT" ] && [ -f "$VLM_OUTPUT" ]; then
        rm -f "$VLM_OUTPUT"
    fi
}

# Function to stop VLM server
stop_vlm_server() {
    # Clean up temp files first
    cleanup_temp_files
    
    if [ -n "$VLM_PID" ] && ps -p $VLM_PID > /dev/null 2>&1; then
        echo "Stopping VLM server (PID: $VLM_PID)..."
        # Kill the process and its children
        kill -TERM $VLM_PID 2>/dev/null || true
        # Give it time to shut down gracefully
        sleep 3
        # Force kill if still running (including children)
        if ps -p $VLM_PID > /dev/null 2>&1; then
            echo "Force killing VLM server and children..."
            pkill -9 -P $VLM_PID 2>/dev/null || true
            kill -9 $VLM_PID 2>/dev/null || true
        fi
        VLM_PID=""
        echo "VLM server stopped"
    elif [ -n "$VLM_PORT" ]; then
        # Try to find and kill process by port
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

# Trap to ensure VLM server is stopped and temp files cleaned on script exit
trap stop_vlm_server EXIT

# Source .bashrc to initialize conda
source ~/.bashrc

echo "=========================================="
echo "Starting VLM Server"
echo "=========================================="
echo "VLM Script: $VLM_SCRIPT"
echo "Model: $VLM_MODEL"
echo "Benchmark Script: $BENCHMARK_SCRIPT"

# If no port specified, find a free one
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

# Activate vlm conda environment
echo "Activating conda environment: vlm"
if ! conda activate vlm; then
    echo "Error: Failed to activate conda environment 'vlm'"
    echo "Make sure the 'vlm' conda environment exists"
    exit 1
fi

# Create temp file for VLM output (will be cleaned up by trap)
VLM_OUTPUT=$(mktemp)

# Run VLM script in foreground - it has built-in waiting logic that waits
# up to 5 minutes for the server to become healthy before exiting
echo "Running VLM server script (this may take 1-2 minutes)..."
echo "Logging to: $VLM_OUTPUT"
bash "$VLM_SCRIPT" --model "$VLM_MODEL" --port "$VLM_PORT" > "$VLM_OUTPUT" 2>&1
VLM_SCRIPT_EXIT_CODE=$?

# Check if the startup script succeeded
if [ $VLM_SCRIPT_EXIT_CODE -ne 0 ]; then
    echo "Error: VLM server script failed with exit code $VLM_SCRIPT_EXIT_CODE"
    echo "VLM script output:"
    cat "$VLM_OUTPUT"
    exit 1
fi

# Find the vLLM server process by port (server should be running and healthy now)
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

# Clean up temp file now that server is running
rm -f "$VLM_OUTPUT"
VLM_OUTPUT=""

# Wait additional time for model to fully initialize before testing
echo "Waiting 60 seconds for model to fully initialize before starting experiments..."
sleep 60
echo ""

# Verify server is responding (should already be healthy, but double-check)
echo "Verifying VLM server is responding..."
if curl -s http://localhost:${VLM_PORT}/health > /dev/null 2>&1; then
    echo "✓ VLM server is responding"
else
    echo "✗ WARNING: VLM server health check failed, but process is running. Proceeding..."
fi
echo ""

# Run experiments
echo "=========================================="
echo "Running Experiments"
echo "=========================================="
echo "Calling run_experiments.sh with:"
echo "  --port $VLM_PORT"
echo "  --model \"$VLM_MODEL\""
echo "  --script \"$BENCHMARK_SCRIPT\""
echo ""

# Verify VLM server is still running before starting experiments
if ! curl -s http://localhost:${VLM_PORT}/health > /dev/null 2>&1; then
    echo "ERROR: VLM server on port $VLM_PORT is not responding!"
    echo "Cannot proceed with experiments."
    exit 1
fi

# Run the experiments script (use absolute path based on script location)
bash "${SCRIPT_DIR}/run_experimentsAllVersions.sh" --port $VLM_PORT --model "$VLM_MODEL" --script "$BENCHMARK_SCRIPT"
EXPERIMENTS_EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXPERIMENTS_EXIT_CODE -eq 0 ]; then
    echo "✓ All experiments completed successfully"
else
    echo "✗ Experiments failed with exit code $EXPERIMENTS_EXIT_CODE"
fi
echo "=========================================="

# Stop VLM server (trap will also handle this, but explicit is good)
stop_vlm_server
 
echo ""
echo "Training script completed!"
