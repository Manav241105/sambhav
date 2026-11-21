import sys
# Windows consoles default to cp1252 and crash on emoji prints; force UTF-8.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

#!/usr/bin/env python3
"""
System Health Check Script
Verifies all components are running correctly
"""

import sys
import requests
from typing import Tuple

from core.settings import get_settings

_settings = get_settings()
_API = f"http://localhost:{_settings.api_port}"

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
        resp = requests.get(f"{_settings.ollama_base_url.rstrip('/')}/api/tags", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            if _settings.ollama_model in models:
                return True, f"Running with {_settings.ollama_model}"
            else:
                return False, f"Running but {_settings.ollama_model} not found. Available: {', '.join(models)}"
        return False, f"Unexpected status code: {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Not running (connection refused)"
    except requests.exceptions.Timeout:
        return False, "Timeout (server not responding)"

def check_api_server() -> Tuple[bool, str]:
    """Check if API server is running"""
    try:
        resp = requests.get(f"{_API}/health", timeout=5)
        if resp.status_code == 200:
            if not resp.json().get("database"):
                return False, "Running, but the database is unreachable"
            return True, "Running and healthy (database OK)"
        return False, f"Unexpected status code: {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Not running (connection refused)"
    except requests.exceptions.Timeout:
        return False, "Timeout (server not responding)"

def check_staff_login() -> Tuple[bool, str]:
    """Check authentication with the demo staff account (needs DEMO_STAFF_PASSWORD and demo data)."""
    if not _settings.demo_staff_password:
        return False, "DEMO_STAFF_PASSWORD not set in .env"
    resp = requests.post(f"{_API}/api/auth/login", timeout=10,
                         json={"email": "ops@autopredict.local", "password": _settings.demo_staff_password})
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        vehicles = requests.get(f"{_API}/api/vehicles", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        n = len(vehicles.json()) if vehicles.status_code == 200 else 0
        if n == 0:
            return False, "Login works but there is no data. Run: python -m sim.build"
        return True, f"Login works; {n} vehicles in the database"
    if resp.status_code == 401:
        return False, "Login rejected. Was demo data built with this DEMO_STAFF_PASSWORD? (python -m sim.build)"
    return False, f"Unexpected status code: {resp.status_code}"

def main():
    print("\n" + "="*60)
    print("🔍 AutoPredict System Health Check")
    print("="*60 + "\n")
    
    results = []
    
    # Check Ollama
    results.append(check_component("Ollama Server", check_ollama))
    
    # Check API Server
    results.append(check_component("API Server", check_api_server))
    
    # Check login + data (only if API server is running)
    if results[1][0]:
        results.append(check_component("Staff Login & Data", check_staff_login))
    
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
