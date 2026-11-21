import sys
# Windows consoles default to cp1252 and crash on emoji prints; force UTF-8.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import asyncio
import uvicorn
import sys
import os
import time
from multiprocessing import Process
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

def run_server():
    """Run the FastAPI server"""
    print("\n🚀 Starting Voice AI Server...")
    print("👉 API Docs available at: http://127.0.0.1:8001/docs")
    sys.path.append(os.getcwd())  # Ensure path is correct
    uvicorn.run("voice_api:app", host="0.0.0.0", port=8001, log_level="info")

def run_main_simulation():
    """Run the main system simulation"""
    # Wait for server to start
    time.sleep(5)
    print("\n🎬 Starting Main Simulation...")
    # Using os.system to run in same console, or import main
    # Better to run as subprocess to keep output clean
    os.system("python main.py")

if __name__ == "__main__":
    print("==================================================")
    print("🤖 STARTING FULL SYSTEM (Server + Simulation)")
    print("==================================================")
    
    # Check for keys
    if not os.getenv("TWILIO_SID"):
        print("⚠️  Warning: TWILIO_SID not found in .env")
        print("   Voice AI features will be in SIMULATION MODE")
    
    # Start Server Process
    server_process = Process(target=run_server)
    server_process.start()
    
    try:
        # Run Main Simulation in this process
        run_main_simulation()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down system...")
    finally:
        server_process.terminate()
        server_process.join()
        print("✅ System Shutdown Complete")