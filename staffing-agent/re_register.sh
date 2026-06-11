#!/bin/bash
# Run the re-registration utility using the root venv

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Path to root venv python
PYTHON_PATH="$DIR/../.venv/bin/python"

if [ ! -f "$PYTHON_PATH" ]; then
    echo "Error: Python not found at $PYTHON_PATH"
    exit 1
fi

$PYTHON_PATH "$DIR/deployment/deploy.py" "$@"
