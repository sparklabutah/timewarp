#!/bin/bash
# Script to run experiments for multiple models sequentially
# Each experiment waits for the previous one to complete before starting
# Usage: ./trainMultipleModels.sh --script BENCHMARK_SCRIPT
#   --script: Path to benchmark Python script passed through to run_experiments_with_model.sh

# Array of model paths
MODELS=(
    # "/scratch/general/nfs1/u1592009/LLaMA-Factory/saves/qwen3-vl-8b-SS/qwenSS-TW-checkpoint-864"
    # "/scratch/general/nfs1/u1592009/LLaMA-Factory/saves/qwen3-vl-8b-Thinking-SoM"
    "/scratch/general/nfs1/u1592009/LLaMA-Factory/saves/qwen3-vl-8b-SoM/Qwen3-SoM-TW-ep1-checkpoint-288"

)
# Server timeout (seconds to wait between models)
SERVER_TIMEOUT=60
# Get the directory of this script to ensure we can find run_experiments_with_model.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Benchmark script to pass down
BENCHMARK_SCRIPT=""

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --script)
            BENCHMARK_SCRIPT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 --script BENCHMARK_SCRIPT"
            echo "  --script: Path to benchmark Python script passed to run_experiments_with_model.sh"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate that benchmark script was provided
if [ -z "$BENCHMARK_SCRIPT" ]; then
    echo "Error: --script parameter is required"
    echo "Usage: $0 --script BENCHMARK_SCRIPT"
    exit 1
fi

# Counter for tracking progress
TOTAL=${#MODELS[@]}
CURRENT=0

echo "=========================================="
echo "Starting training for $TOTAL models"
echo "=========================================="
echo ""

# Loop through each model
for MODEL_PATH in "${MODELS[@]}"; do
    CURRENT=$((CURRENT + 1))
    
    # Extract model name from path (last component)
    MODEL_NAME=$(basename "$MODEL_PATH")
    
    echo "=========================================="
    echo "[$CURRENT/$TOTAL] Starting benchmark for model: $MODEL_NAME"
    echo "Full path: $MODEL_PATH"
    echo "=========================================="
    
    # Run the experiment script
    bash "$SCRIPT_DIR/run_experiments_with_modelAllVersions.sh" --model "$MODEL_PATH" --script "$BENCHMARK_SCRIPT"
    EXIT_CODE=$?
    
    # Check if the experiment completed successfully
    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo "✓ Benchmark complete: $MODEL_NAME"
    else
        echo ""
        echo "✗ Benchmark failed for: $MODEL_NAME (exit code: $EXIT_CODE)"
    fi
    
    # Wait before starting the next model (unless this was the last one)
    if [ $CURRENT -lt $TOTAL ]; then
        echo "Waiting ${SERVER_TIMEOUT} seconds before starting next model..."
        sleep $SERVER_TIMEOUT
        echo ""
    fi
done

echo ""
echo "=========================================="
echo "All benchmarks completed!"
echo "=========================================="
