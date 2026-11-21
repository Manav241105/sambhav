#!/bin/bash
# Start the AutoPredict API for local development.
set -euo pipefail
cd "$(dirname "$0")"

if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

echo "Applying database migrations..."
alembic upgrade head

echo ""
echo "Starting AutoPredict API on http://localhost:8001 (docs: /docs)"
echo "No demo data yet? Run: python -m sim.build"
echo ""
python webhook_server.py
