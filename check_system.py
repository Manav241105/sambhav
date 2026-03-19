#!/usr/bin/env python3
"""
System Health Check Script
Verifies all components are running correctly
"""

import sys
import requests
from typing import Tuple

def check_component(name: str, check_func) -> Tuple[bool, str]:
    """Check a component and return status"""
    try:
        success, message = check_func()
        status = "✅" if success else "❌"
        print(f"{status} {name}: {message}")
        return success, message
    except Exception as e:
        print(f"❌ {name}: ERROR - {e}")
        return False, str(e)

def check_ollama() -> Tuple[bool, str]:
    """Check if Ollama is running"""
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            if "llama3:8b" in models:
                return True, "Running with llama3:8b model"
            else:
                return False, f"Running but llama3:8b not found. Available: {', '.join(models)}"
        return False, f"Unexpected status code: {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Not running (connection refused)"
    except requests.exceptions.Timeout:
        return False, "Timeout (server not responding)"

def check_api_server() -> Tuple[bool, str]:
    """Check if API server is running"""
    try:
        resp = requests.get("http://localhost:8000/health", timeout=5)
        if resp.status_code == 200:
            return True, "Running and healthy"
        return False, f"Unexpected status code: {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Not running (connection refused)"
    except requests.exceptions.Timeout:
        return False, "Timeout (server not responding)"

def check_chat_endpoint() -> Tuple[bool, str]:
    """Check if chat endpoint works"""
    try:
        resp = requests.post(
            "http://localhost:8000/api/chat",
            json={"message": "test", "vehicle_id": "VEH001"},
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            reply = data.get("reply", "")
            if "[AI offline" in reply:
                return False, "API server running but can't connect to Ollama"
            return True, f"Working (response: {reply[:50]}...)"
        return False, f"Unexpected status code: {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "API server not running"
    except requests.exceptions.Timeout:
        return False, "Timeout (Ollama may be slow or not responding)"

def main():
    print("\n" + "="*60)
    print("🔍 AutoPredict System Health Check")
    print("="*60 + "\n")
    
    results = []
    
    # Check Ollama
    results.append(check_component("Ollama Server", check_ollama))
    
    # Check API Server
    results.append(check_component("API Server", check_api_server))
    
    # Check Chat Endpoint (only if API server is running)
    if results[1][0]:
        results.append(check_component("Chat Endpoint", check_chat_endpoint))
    
    print("\n" + "="*60)
    
    # Summary
    all_passed = all(r[0] for r in results)
    
    if all_passed:
        print("✅ All systems operational!")
        print("\nYour mobile app should now work correctly.")
    else:
        print("❌ Some components are not working properly.")
        print("\nRecommended actions:")
        
        if not results[0][0]:
            print("\n1. Start Ollama:")
            print("   ollama serve")
            print("\n2. Verify llama3:8b model is installed:")
            print("   ollama pull llama3:8b")
        
        if not results[1][0]:
            print("\n3. Start the API server:")
            print("   cd backend")
            print("   python webhook_server.py")
        
        if len(results) > 2 and not results[2][0]:
            print("\n4. Check Ollama connection:")
            print("   curl http://localhost:11434/api/tags")
    
    print("\n" + "="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
