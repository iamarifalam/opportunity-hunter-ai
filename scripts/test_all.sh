#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "🧪 Running full test suite for Opportunity Hunter AI..."
"$DIR/.venv/bin/pytest" -v --tb=short
