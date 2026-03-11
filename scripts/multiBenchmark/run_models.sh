#!/bin/bash
# Iterates over multiple models, running all benchmark scripts across all
# specified TimeWarp versions for each model.
#
# Usage: ./run_models.sh --models MODELS --scripts SCRIPTS [OPTIONS]
#   --models:     Comma-separated list of model paths (required)
#   --scripts:    Comma-separated list of benchmark Python scripts (required)
#   --vlm-script: Path to VLM start script (forwarded to run_with_vlm.sh)
#   --port:       Port for VLM server (forwarded to run_with_vlm.sh)
#   --versions:   Comma-separated versions to run (forwarded to run_with_vlm.sh)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SERVER_TIMEOUT=60

MODELS=""
BENCHMARK_SCRIPTS=""
VLM_SCRIPT_PATH=""
PORT=""
VERSIONS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --models)
            MODELS="$2"
            shift 2
            ;;
        --scripts)
            BENCHMARK_SCRIPTS="$2"
            shift 2
            ;;
        --vlm-script)
            VLM_SCRIPT_PATH="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --versions)
            VERSIONS="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 --models MODELS --scripts SCRIPTS [OPTIONS]"
            echo "  --models:     Comma-separated list of model paths (required)"
            echo "  --scripts:    Comma-separated list of benchmark Python scripts (required)"
            echo "  --vlm-script: Path to VLM start script (default: startVLMmodel.sh)"
            echo "  --port:       Port for VLM server (default: auto-detect)"
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

if [ -z "$MODELS" ]; then
    echo "Error: --models parameter is required"
    exit 1
fi
if [ -z "$BENCHMARK_SCRIPTS" ]; then
    echo "Error: --scripts parameter is required"
    exit 1
fi

IFS=',' read -ra MODEL_LIST <<< "$MODELS"
TOTAL=${#MODEL_LIST[@]}
CURRENT=0

echo "=========================================="
echo "Starting benchmarks for $TOTAL model(s)"
echo "  Scripts:  $BENCHMARK_SCRIPTS"
echo "  Versions: ${VERSIONS:-1,2,3,4,5,6}"
echo "=========================================="
echo ""

for MODEL_PATH in "${MODEL_LIST[@]}"; do
    CURRENT=$((CURRENT + 1))
    MODEL_NAME=$(basename "$MODEL_PATH")

    echo "=========================================="
    echo "[$CURRENT/$TOTAL] Model: $MODEL_NAME"
    echo "Full path: $MODEL_PATH"
    echo "=========================================="

    CMD_ARGS=(--model "$MODEL_PATH" --scripts "$BENCHMARK_SCRIPTS")
    [ -n "$VLM_SCRIPT_PATH" ] && CMD_ARGS+=(--vlm-script "$VLM_SCRIPT_PATH")
    [ -n "$PORT" ]            && CMD_ARGS+=(--port "$PORT")
    [ -n "$VERSIONS" ]        && CMD_ARGS+=(--versions "$VERSIONS")

    bash "$SCRIPT_DIR/run_with_vlm.sh" "${CMD_ARGS[@]}"
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo "Benchmark complete: $MODEL_NAME"
    else
        echo ""
        echo "Benchmark failed for: $MODEL_NAME (exit code: $EXIT_CODE)"
    fi

    if [ $CURRENT -lt $TOTAL ]; then
        echo "Waiting ${SERVER_TIMEOUT}s before starting next model..."
        sleep $SERVER_TIMEOUT
        echo ""
    fi
done

echo ""
echo "=========================================="
echo "All model benchmarks completed!"
echo "=========================================="
