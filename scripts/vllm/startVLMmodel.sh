#!/bin/bash
# Working vLLM server script that calculates GPU memory automatically
# Usage: ./startQwen.sh [--port PORT] [--model MODEL_PATH]
#   --port: Port number for vLLM server (default: 8001)
#   --model: Path to model directory (default: /scratch/general/nfs1/u1592009/LLaMA-Factory/saves/qwen3-4b-8k-full-epoch3)
# Example: ./startQwen.sh --port 8001
# Example: ./startQwen.sh --port 8002 --model /path/to/model

# Parse command-line arguments
PORT=8001  # Default port
MODEL_PATH="/scratch/general/nfs1/u1592009/LLaMA-Factory/saves/qwen3-4b-8k-full-epoch3"  # Default model path
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --model)
            MODEL_PATH="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--port PORT] [--model MODEL_PATH]"
            echo "  --port: Port number for vLLM server (default: 8001)"
            echo "  --model: Path to model directory (default: /scratch/general/nfs1/u1592009/LLaMA-Factory/saves/qwen3-4b-8k-full-epoch3)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "Starting vLLM Server (Auto Memory Config)"
echo "=========================================="

# Get available GPU memory in MiB
FREE_MEM=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)
TOTAL_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)

echo "GPU Memory:"
echo "  Total: ${TOTAL_MEM} MiB"
echo "  Free: ${FREE_MEM} MiB"
echo ""

# Calculate safe utilization (use 80% of free memory, converted to fraction of total)
# Formula: (free_mem * 0.8) / total_mem
SAFE_UTIL=$(python3 -c "print(min(0.9, ($FREE_MEM * 0.8) / $TOTAL_MEM))")

echo "Calculated GPU utilization: $SAFE_UTIL"
echo ""

# Get number of available GPUs
# Check if we're on a MIG instance
if nvidia-smi --list-gpus | grep -q "MIG"; then
    NUM_GPUS=1  # MIG instances don't support tensor parallelism
    # Disable NCCL for MIG instances to prevent distributed processing issues
    export NCCL_DEBUG=INFO
    export NCCL_P2P_DISABLE=1
    export NCCL_IB_DISABLE=1
    # Disable vLLM v1 engine for MIG compatibility
    export VLLM_USE_V1=0
    # Reduce GPU memory utilization for MIG instances (they have limited memory)
    # Use 60% of free memory instead of 80%, capped at 70% total
    SAFE_UTIL=$(python3 -c "print(min(0.7, ($FREE_MEM * 0.6) / $TOTAL_MEM))")
    # Enable PyTorch memory management to reduce fragmentation
    export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
    echo "MIG instance detected - reducing GPU memory utilization to ${SAFE_UTIL} and disabling distributed processing"
else
    NUM_GPUS=$(nvidia-smi --list-gpus | grep "^GPU" | wc -l)
fi
echo "GPUs detected: $NUM_GPUS"
if [ $NUM_GPUS -gt 1 ]; then
    echo "Multi-GPU mode: Tensor parallelism will be enabled"
fi
echo ""

# Get server IP - prefer public IP over private IP
# Method 1: Use SERVER_IP environment variable if set
if [ -n "$SERVER_IP" ]; then
    echo "Using SERVER_IP from environment: $SERVER_IP"
else
    # Method 2: Try to get public IP (non-private)
    # Get all IPs and filter out private ranges (10.x, 172.16-31.x, 192.168.x, 127.x)
    SERVER_IP=$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -vE '^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|127\.)' | head -1)
    
    # If no public IP found, try getting IP from specific interface (eth0.25 for public)
    if [ -z "$SERVER_IP" ]; then
        SERVER_IP=$(ip addr show eth0.25 2>/dev/null | grep -oP 'inet \K[\d.]+' | head -1)
    fi
    
    # Fallback: use first IP from hostname -I
    if [ -z "$SERVER_IP" ]; then
        SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi
fi

echo "Starting server..."
echo "Model: ${MODEL_PATH}"
echo "Port: ${PORT}"
echo "Server IP: ${SERVER_IP}"
if [ $NUM_GPUS -gt 1 ]; then
    echo "Tensor Parallel Size: $NUM_GPUS"
fi
echo ""

# Disable PyTorch dynamo/compile to avoid UnboundLocalError issues
# This prevents the "cannot access local variable 'tracer_output'" error
export TORCH_COMPILE_DISABLE=1
export PYTORCH_DISABLE_COMPILE=1
export TORCHDYNAMO_DISABLE=1
# Disable dynamo at Python level
export PYTHONOPTIMIZE=0

# Start the server
# vllm serve meta-llama/Meta-Llama-3.1-8B-Instruct \


VLLM_CMD="vllm serve ${MODEL_PATH} \
    --port ${PORT} \
    --host 0.0.0.0 \
    --trust-remote-code \
    --gpu-memory-utilization $SAFE_UTIL \
    --max-model-len 65536 \
    --enforce-eager"

# Only add tensor-parallel-size if we have multiple GPUs
if [ $NUM_GPUS -gt 1 ]; then
    VLLM_CMD="$VLLM_CMD --tensor-parallel-size $NUM_GPUS"
else
    # For single GPU (including MIG), add flags to prevent distributed processing issues
    VLLM_CMD="$VLLM_CMD --disable-custom-all-reduce"
fi

# Execute the command
eval $VLLM_CMD 2>&1 | tee vllm_server.log &

SERVER_PID=$!
echo "Server PID: $SERVER_PID"
echo ""
echo "Waiting for server to start (this may take several minutes)..."

# Wait for server to be ready (600 iterations × 5s = 50 minutes)
for i in {1..600}; do
    sleep 5
    if curl -s http://localhost:${PORT}/health > /dev/null 2>&1; then
        echo ""
        echo "=========================================="
        echo "Server is READY!"
        echo "=========================================="
        echo "Local: http://localhost:${PORT}"
        echo "Network: http://${SERVER_IP}:${PORT}"
        echo "API Docs: http://${SERVER_IP}:${PORT}/docs"
        if [ $NUM_GPUS -gt 1 ]; then
            echo "Multi-GPU: Using $NUM_GPUS GPUs with tensor parallelism"
        fi
        echo ""
        echo "Test it:"
        echo "  curl http://localhost:${PORT}/health"
        echo "  curl http://localhost:${PORT}/v1/models"
        echo ""
        echo "To stop: kill $SERVER_PID"
        echo "=========================================="
        exit 0
    fi
    
    if ! ps -p $SERVER_PID > /dev/null 2>&1; then
        echo ""
        echo "✗ Server crashed. Check logs above for errors."
        exit 1
    fi
    echo -n "."
done

echo ""
echo "✗ Server timed out after 50 minutes. Check status with:"
echo "  curl http://localhost:${PORT}/health"
echo "  tail -f vllm_server.log"
exit 1