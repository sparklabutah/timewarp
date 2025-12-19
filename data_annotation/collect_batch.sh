#!/bin/bash

# Batch data collection script for TimeWarp environments
# Usage: ./collect_batch.sh <env> <variant>
# Example: ./collect_batch.sh wiki 1

set -e  # Exit on error

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Error: .env file not found"
    echo "Please create a .env file with environment URLs (WIKI1, NEWS1, etc.)"
    exit 1
fi

# Check arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <env> <variant>"
    echo "  env: Environment type (wiki, homepage, news, webshop)"
    echo "  variant: Theme/variant number (1-6) or 'all'"
    echo ""
    echo "Example: $0 wiki 1"
    echo "Example: $0 wiki all  # Collects across all themes sequentially"
    echo ""
    echo "URLs are loaded from .env file:"
    echo "  wiki 1 → WIKI1"
    echo "  news 3 → NEWS3"
    echo "  webshop 2 → SHOP2"
    echo "  homepage 4 → HOME4"
    echo ""
    echo "When using 'all':"
    echo "  Trace 1: theme1, theme2, theme3, theme4, theme5, theme6"
    echo "  Trace 2: theme1, theme2, theme3, theme4, theme5, theme6"
    echo "  ... and so on"
    exit 1
fi

ENV="$1"
VARIANT="$2"

# Determine number of iterations and environment variable name based on environment
case "$ENV" in
    wiki)
        NUM_ITERATIONS=39
        ENV_VAR_PREFIX="WIKI"
        ;;
    news)
        NUM_ITERATIONS=32
        ENV_VAR_PREFIX="NEWS"
        ;;
    webshop)
        NUM_ITERATIONS=45
        ENV_VAR_PREFIX="SHOP"
        ;;
    homepage)
        NUM_ITERATIONS=5
        ENV_VAR_PREFIX="HOME"
        ;;
    *)
        echo "Error: Invalid environment '$ENV'"
        echo "Valid environments: wiki, homepage, news, webshop"
        exit 1
        ;;
esac

# Check if collecting across all themes
if [ "$VARIANT" == "all" ]; then
    echo "=========================================="
    echo "Batch Data Collection - ALL THEMES"
    echo "=========================================="
    echo "Environment: $ENV"
    echo "Mode: Sequential across all themes (1-6)"
    echo "Number of iterations per theme: $NUM_ITERATIONS"
    echo "Total traces to collect: $((NUM_ITERATIONS * 6))"
    echo "=========================================="
    echo ""
    
    # Loop through each iteration
    for i in $(seq 1 $NUM_ITERATIONS); do
        echo ""
        echo "=========================================="
        echo "Trace ID: $i"
        echo "=========================================="
        
        # Loop through each theme (1-6)
        for theme in {1..6}; do
            echo ""
            echo "--- Theme $theme (Trace $i) ---"
            
            # Construct environment variable name and get URL
            ENV_VAR_NAME="${ENV_VAR_PREFIX}${theme}"
            URL="${!ENV_VAR_NAME}"
            
            # Check if URL is set
            if [ -z "$URL" ] || [ "$URL" == "INSERT_URL_HERE" ]; then
                echo "⚠️  Warning: $ENV_VAR_NAME is not set or is a placeholder. Skipping theme $theme."
                continue
            fi
            
            # Create output directory
            OUTPUT_DIR="trajectories/${ENV}/theme_${theme}"
            mkdir -p "$OUTPUT_DIR"
            
            TRACE_FILE="${OUTPUT_DIR}/${i}_trace.zip"
            EXIT_MSG_FILE="${OUTPUT_DIR}/${i}_exit_message.txt"
            
            # Check if files already exist
            if [ -f "$TRACE_FILE" ] && [ -f "$EXIT_MSG_FILE" ]; then
                echo "⚠️  Files already exist. Skipping..."
                echo "   Trace: $TRACE_FILE"
                continue
            fi
            
            echo "Environment Variable: $ENV_VAR_NAME"
            echo "URL: $URL"
            echo "Output: $TRACE_FILE"
            echo ""
            echo "Instructions:"
            echo "  1. Browser will open - perform your task"
            echo "  2. Close the Inspector window when done"
            echo ""
            
            # Run playwright codegen with trace saving
            playwright codegen --target python --save-trace="$TRACE_FILE" "$URL"
            
            # Verify trace file was created
            if [ ! -f "$TRACE_FILE" ]; then
                echo "❌ Error: Trace file was not created"
                echo "Did you close the Inspector window?"
                exit 1
            fi
            
            # Prompt for exit message
            echo ""
            echo "Trace saved successfully!"
            echo "Now enter the exit message (your final answer for this task):"
            read -p "> " exit_message
            
            # Save exit message to file
            echo "$exit_message" > "$EXIT_MSG_FILE"
            
            echo "✓ Theme $theme completed (Trace $i)"
            echo "  Trace: $TRACE_FILE"
            echo "  Exit message: $EXIT_MSG_FILE"
        done
        
        echo ""
        echo "✓ Completed Trace ID $i across all themes"
    done
    
    echo ""
    echo "=========================================="
    echo "ALL THEMES Collection Complete!"
    echo "=========================================="
    echo "Environment: $ENV"
    echo "Total traces collected: $((NUM_ITERATIONS * 6))"
    echo ""
    echo "Next steps:"
    echo "  1. Review the collected traces in trajectories/${ENV}/"
    echo "  2. Run process_traces.py for each theme"
    echo "=========================================="
    exit 0
fi

# Single theme mode (original behavior)
# Validate variant
if ! [[ "$VARIANT" =~ ^[1-6]$ ]]; then
    echo "Error: Variant must be between 1 and 6 or 'all'"
    exit 1
fi

# Construct environment variable name and get URL
ENV_VAR_NAME="${ENV_VAR_PREFIX}${VARIANT}"
URL="${!ENV_VAR_NAME}"

# Check if URL is set
if [ -z "$URL" ] || [ "$URL" == "INSERT_URL_HERE" ]; then
    echo "Error: Environment variable $ENV_VAR_NAME is not set or is a placeholder"
    echo "Please update your .env file with the actual URL for $ENV_VAR_NAME"
    exit 1
fi

# Create output directory
OUTPUT_DIR="trajectories/${ENV}/theme_${VARIANT}"
mkdir -p "$OUTPUT_DIR"

echo "=========================================="
echo "Batch Data Collection"
echo "=========================================="
echo "Environment: $ENV"
echo "Variant/Theme: $VARIANT"
echo "Environment Variable: $ENV_VAR_NAME"
echo "URL: $URL"
echo "Number of iterations: $NUM_ITERATIONS"
echo "Output directory: $OUTPUT_DIR"
echo "=========================================="
echo ""

# Loop through iterations
for i in $(seq 1 $NUM_ITERATIONS); do
    echo ""
    echo "=========================================="
    echo "Iteration $i of $NUM_ITERATIONS"
    echo "=========================================="
    
    TRACE_FILE="${OUTPUT_DIR}/${i}_trace.zip"
    EXIT_MSG_FILE="${OUTPUT_DIR}/${i}_exit_message.txt"
    
    # Check if files already exist
    if [ -f "$TRACE_FILE" ] && [ -f "$EXIT_MSG_FILE" ]; then
        echo "⚠️  Files already exist for iteration $i. Skipping..."
        echo "   Trace: $TRACE_FILE"
        echo "   Exit message: $EXIT_MSG_FILE"
        continue
    fi
    
    echo "Running Playwright codegen for iteration $i..."
    echo "Trace will be saved to: $TRACE_FILE"
    echo ""
    echo "Instructions:"
    echo "  1. Browser will open - perform your task"
    echo "  2. Close the Inspector window when done (trace saves automatically)"
    echo ""
    
    # Run playwright codegen with trace saving
    playwright codegen --target python --save-trace="$TRACE_FILE" "$URL"
    
    # Verify trace file was created
    if [ ! -f "$TRACE_FILE" ]; then
        echo "❌ Error: Trace file was not created for iteration $i"
        echo "Did you close the Inspector window?"
        exit 1
    fi
    
    # Prompt for exit message
    echo ""
    echo "Trace saved successfully!"
    echo "Now enter the exit message (your final answer for this task):"
    read -p "> " exit_message
    
    # Save exit message to file
    echo "$exit_message" > "$EXIT_MSG_FILE"
    
    if [ ! -f "$EXIT_MSG_FILE" ]; then
        echo "❌ Error: Exit message file was not created for iteration $i"
        exit 1
    fi
    
    echo "✓ Iteration $i completed successfully"
    echo "  Trace: $TRACE_FILE"
    echo "  Exit message: $EXIT_MSG_FILE"
done

echo ""
echo "=========================================="
echo "Batch Collection Complete!"
echo "=========================================="
echo "Environment: $ENV"
echo "Variant: $VARIANT"
echo "Total iterations: $NUM_ITERATIONS"
echo "Output directory: $OUTPUT_DIR"
echo ""
echo "Files created:"
ls -lh "$OUTPUT_DIR" | tail -n +2 | wc -l
echo ""
echo "Next steps:"
echo "  1. Review the collected traces"
echo "  2. Run process_traces.py to generate training data"
echo "=========================================="

