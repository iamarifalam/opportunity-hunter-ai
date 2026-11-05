#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "🚀 Starting Opportunity Hunter AI on http://127.0.0.1:8000 ..."
"$DIR/.venv/bin/uvicorn" hunter_ai.api.app:app --host 127.0.0.1 --port 8000 --reload
