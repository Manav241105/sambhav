#!/bin/bash

echo "========================================"
echo "Starting AutoPredict API Server"
echo "========================================"
echo ""
echo "Checking Python environment..."

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -f venv/bin/activate ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

echo ""
echo "Starting FastAPI server on http://localhost:8001"
echo ""
echo "Available endpoints:"
echo "  - API: http://localhost:8001/api"
echo "  - Chat: http://localhost:8001/api/chat"
echo "  - Health: http://localhost:8001/health"
echo "  - WebSocket: ws://localhost:8001/ws/dashboard"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python webhook_server.py
