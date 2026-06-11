#!/usr/bin/env bash
# Re-registers the ADK Agent locally.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$DIR/.env" ]; then
  source "$DIR/.env"
fi

PYTHON_PATH=${PYTHON_PATH:-"python3"}

$PYTHON_PATH "$DIR/deployment/deploy.py" "$@"
