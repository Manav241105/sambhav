# 🚀 START HERE - Fix "[AI offline]" Error

## The Problem
Your mobile app shows: **"[AI offline — ensure Ollama is running]"**

## The Solution (2 Simple Steps)

### ✅ Step 1: Ollama is Already Running
Good news! Ollama is running correctly with the llama3:8b model.

### ⚠️ Step 2: Start the API Server (THIS IS WHAT'S MISSING!)

The mobile app needs the API server to be running. Here's how to start it:

#### Windows Users:
```bash
cd backend
start_server.bat
```

#### Linux/Mac Users:
```bash
cd backend
chmod +x start_server.sh
./start_server.sh
```

#### Alternative (Any OS):
```bash
cd backend
python webhook_server.py
```

## What You Should See

When the server starts successfully, you'll see:
```
🌐 STARTING WEBHOOK SERVER
================================================================================

Endpoints:
  - API: http://localhost:8000/api
  - Chat: http://localhost:8000/api/chat
  - Health: http://localhost:8000/health
  - WebSocket: ws://localhost:8000/ws/dashboard

Starting server...

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Test It Works

Open a new terminal and run:
```bash
cd backend
python check_system.py
```

You should see all green checkmarks (✅).

## Now Test Your Mobile App

1. Make sure the API server is still running (don't close the terminal)
2. Open your mobile app
3. Try sending a message like "hi" or "How are my brakes?"
4. You should now get AI responses instead of the offline error!

## Mobile App Configuration

If you're testing on a physical device (not emulator), you need to:

1. Find your computer's IP address:
   - Windows: `ipconfig` (look for IPv4 Address)
   - Mac/Linux: `ifconfig` or `ip addr`

2. Update your mobile app's API URL from:
   - `http://localhost:8000/api` 
   - TO: `http://YOUR_IP_ADDRESS:8000/api`
   - Example: `http://192.168.1.100:8000/api`

3. Make sure your phone and computer are on the same WiFi network

## Troubleshooting

### "Port 8000 already in use"
Another process is using port 8000. Find and kill it:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### "Module not found" errors
Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### Still not working?
Run the diagnostic:
```bash
cd backend
python check_system.py
```

This will tell you exactly what's wrong.

## Keep the Server Running

Important: The API server must stay running while you use the mobile app!

- Don't close the terminal window
- If you close it, just run `python webhook_server.py` again
- For production, you'd use a process manager to keep it running automatically

## Next Steps

Once everything is working:
1. ✅ Ollama is running (already done)
2. ✅ API server is running (you just started it)
3. ✅ Mobile app can connect (test it now!)
4. 🎉 Enjoy your AI-powered vehicle assistant!
