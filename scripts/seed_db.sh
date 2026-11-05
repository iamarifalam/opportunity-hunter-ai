#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "🌱 Seeding Opportunity Hunter AI database..."
"$DIR/.venv/bin/python" hunter_ai/seed_data.py
