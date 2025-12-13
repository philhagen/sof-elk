#!/bin/bash
# Wrapper script to execute sof-elk commands within the hatch environment.
# Automatically bootstraps hatch if it is missing.

# Ensure we are in the script's directory (the project python root)
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"

# Determine python command
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

if ! command -v "$PYTHON_CMD" &> /dev/null; then
    echo "Error: neither python3 nor python found in PATH."
    exit 1
fi

# Function to check for hatch availability via module
check_hatch_module() {
    "$PYTHON_CMD" -m hatch --version &> /dev/null
}

# 1. Check if hatch is available
if ! check_hatch_module; then
    echo "hatch module not found."
    echo "Attempting to bootstrap hatch..."
    
    if [ -f "bootstrap_hatch.py" ]; then
        "$PYTHON_CMD" bootstrap_hatch.py
        
        if ! check_hatch_module; then
             echo "Error: hatch installed but 'python -m hatch' still failed."
             exit 1
        fi
    else
        echo "Error: bootstrap_hatch.py not found in $SCRIPT_DIR"
        exit 1
    fi
fi

# Execute the command
# Use local 'hatch' alias if available, otherwise fallback to python -m hatch
if [ -f "./hatch" ]; then
    HATCH_CMD="./hatch"
else
    HATCH_CMD="$PYTHON_CMD -m hatch"
fi

echo "Executing: $HATCH_CMD run sof-elk $@"
$HATCH_CMD run sof-elk "$@"
