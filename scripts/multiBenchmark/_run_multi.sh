#!/bin/bash
# ==========================================================================
# _run_multi.sh  –  Single entry-point for multi-model, multi-version
#                   TimeWarp benchmarks.
#
# This script validates the environment, then delegates to the three
# lower-level scripts in this directory:
#
#   _run_multi.sh  →  run_models.sh  →  run_with_vlm.sh  →  run_versions.sh
#
# ==========================================================================
#
# USAGE
#   bash _run_multi.sh --models MODELS --scripts SCRIPTS [OPTIONS]
#
# REQUIRED ARGUMENTS
#   --models   MODELS    Comma-separated list of model paths to benchmark.
#                        Example: "path/to/model1,path/to/model2"
#
#   --scripts  SCRIPTS   Comma-separated list of benchmark Python scripts.
#                        Example: "singleBenchmark/benchmarkGeneralWiki.py,singleBenchmark/benchmarkGeneralMulti.py"
#
# OPTIONAL ARGUMENTS
#   --versions  VERSIONS  Comma-separated subset of versions 1-6 to run.
#                         Default: "1,2,3,4,5,6"
#                         Example: "1,2" runs only versions 1 and 2.
#
#   --vlm-script SCRIPT   Path to the script that starts the VLM server.
#                          Default: "startVLMmodel.sh"
#
#   --port PORT            Port for the VLM server.  If omitted, a free port
#                          is auto-detected.
#
# ENVIRONMENT
#   OPENAI_API_KEY         Must be set before running (used by the judge model).
#
# EXAMPLES
#   # Minimal – two models, one benchmark, all versions:
#   export OPENAI_API_KEY="sk-..."
#   bash _run_multi.sh \
#       --models  "saves/qwen3-4b,saves/llama3-8b" \
#       --scripts "singleBenchmark/benchmarkGeneralWiki.py"
#
#   # Two models, two benchmarks, only versions 1 and 3, custom VLM script:
#   bash _run_multi.sh \
#       --models     "saves/qwen3-4b,saves/llama3-8b" \
#       --scripts    "singleBenchmark/benchmarkGeneralWiki.py,singleBenchmark/benchmarkGeneralMulti.py" \
#       --versions   "1,3" \
#       --vlm-script "custom_vlm_launcher.sh" \
#       --port       9001
#
# ==========================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODELS=""
SCRIPTS=""
VERSIONS="1,2,3,4,5,6"
VLM_SCRIPT=""
PORT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --models)
            MODELS="$2"
            shift 2
            ;;
        --scripts)
            SCRIPTS="$2"
            shift 2
            ;;
        --versions)
            VERSIONS="$2"
            shift 2
            ;;
        --vlm-script)
            VLM_SCRIPT="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        -h|--help)
            # Print the header block from this file as usage text
            sed -n '2,/^# ====.*===$/p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1"
            echo "Run '$0 --help' for usage information."
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Validate environment
# ---------------------------------------------------------------------------
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set."
    echo ""
    echo "The judge model requires an OpenAI API key. Set it with:"
    echo "  export OPENAI_API_KEY=\"sk-...\""
    exit 1
fi

# ---------------------------------------------------------------------------
# Validate required arguments
# ---------------------------------------------------------------------------
if [ -z "$MODELS" ]; then
    echo "Error: --models is required (comma-separated list of model paths)."
    echo "Run '$0 --help' for usage information."
    exit 1
fi
if [ -z "$SCRIPTS" ]; then
    echo "Error: --scripts is required (comma-separated list of benchmark Python scripts)."
    echo "Run '$0 --help' for usage information."
    exit 1
fi

# Validate versions
IFS=',' read -ra VERSION_CHECK <<< "$VERSIONS"
for v in "${VERSION_CHECK[@]}"; do
    if ! [[ "$v" =~ ^[1-6]$ ]]; then
        echo "Error: Invalid version '$v'. Must be between 1 and 6."
        exit 1
    fi
done

# Validate port if provided
if [ -n "$PORT" ] && ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "Error: Port must be a number, got: '$PORT'"
    exit 1
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo "=========================================="
echo " TimeWarp Multi-Benchmark"
echo "=========================================="
echo "Models:     $MODELS"
echo "Scripts:    $SCRIPTS"
echo "Versions:   $VERSIONS"
echo "VLM Script: ${VLM_SCRIPT:-startVLMmodel.sh (default)}"
echo "Port:       ${PORT:-auto-detect}"
echo "=========================================="
echo ""

# ---------------------------------------------------------------------------
# Build arguments and delegate to run_models.sh
# ---------------------------------------------------------------------------
CMD_ARGS=(--models "$MODELS" --scripts "$SCRIPTS" --versions "$VERSIONS")
[ -n "$VLM_SCRIPT" ] && CMD_ARGS+=(--vlm-script "$VLM_SCRIPT")
[ -n "$PORT" ]       && CMD_ARGS+=(--port "$PORT")

bash "$SCRIPT_DIR/run_models.sh" "${CMD_ARGS[@]}"
