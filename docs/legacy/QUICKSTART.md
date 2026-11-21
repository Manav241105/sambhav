# AutoPredict API Server - Quick Start Guide

## Problem: "[AI offline — ensure Ollama is running]"

This error means the backend API server is not running. Follow these steps to fix it:

## Prerequisites

1. **Ollama must be running** with the `llama3:8b` model
2. **Python 3.8+** installed
3. **Dependencies installed** (see Installation below)

## Quick Fix (3 Steps)

### Step 1: Verify Ollama is Running

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start Ollama
ollama serve

# Verify llama3:8b model is available
ollama list

# If model is missing, pull it
ollama pull llama3:8b
```

### Step 2: Install Python Dependencies

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Start the API Server

**Option A: Using the startup script (Windows)**
```bash
start_server.bat
```

**Option B: Using the startup script (Linux/Mac)**
```bash
chmod +x start_server.sh
./start_server.sh
```

**Option C: Direct Python command**
```bash
python webhook_server.py
```

## Verify Server is Running

Once started, you should see:
```
🌐 STARTING WEBHOOK SERVER
================================================================================

Endpoints:
  - WhatsApp: http://localhost:8001/webhook/whatsapp
  - SMS:      http://localhost:8001/webhook/sms
  - Email:    http://localhost:8001/webhook/email
  - Test:     http://localhost:8001/test/simulate-response
  - Health:   http://localhost:8001/health

Starting server...
```

Test the server:
```bash
# Test health endpoint
curl http://localhost:8001/health

# Test chat endpoint
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hi","vehicle_id":"VEH001"}'
```

## Mobile App Configuration

The mobile app should connect to:
- **API Base URL**: `http://localhost:8001/api`
- **Chat Endpoint**: `http://localhost:8001/api/chat`
- **WebSocket**: `ws://localhost:8001/ws/dashboard`

If testing on a physical device, replace `localhost` with your computer's IP address:
- Find your IP: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
- Example: `http://192.168.1.100:8001/api`

## Troubleshooting

### Error: "Connection refused"
- The API server is not running
- Run `python webhook_server.py` in the backend directory

### Error: "[AI offline — ensure Ollama is running]"
- Ollama is not running or not accessible
- Start Ollama: `ollama serve`
- Verify: `curl http://localhost:11434/api/tags`

### Error: "Model not found"
- The llama3:8b model is not installed
- Install it: `ollama pull llama3:8b`

### Error: "Module not found"
- Python dependencies are not installed
- Run: `pip install -r requirements.txt`

### Port 8000 already in use
- Another process is using port 8000
- Find and kill the process, or change the port in `webhook_server.py`

## Architecture Overview

```
Mobile App (Android/iOS)
    ↓ HTTP/WebSocket
API Server (FastAPI) - Port 8000
    ↓ HTTP
Ollama (LLM Server) - Port 11434
    ↓
Llama3:8b Model
```

## Development Workflow

1. Start Ollama: `ollama serve`
2. Start API Server: `python webhook_server.py`
3. Start Frontend (optional): `cd autopredict-web && npm run dev`
4. Test mobile app or use the web dashboard

## Production Deployment

For production deployment:
1. Use environment variables for configuration
2. Set up proper CORS origins
3. Use a reverse proxy (nginx/Apache)
4. Enable HTTPS
5. Use a process manager (systemd/PM2)
6. Consider using a production ASGI server (gunicorn with uvicorn workers)

## Support

If you continue to have issues:
1. Check the server logs for detailed error messages
2. Verify all prerequisites are met
3. Ensure firewall/antivirus is not blocking ports 8000 or 11434
4. Try restarting both Ollama and the API server
