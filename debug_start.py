#!/usr/bin/env python3
"""Debug script to start API server and see any errors."""

import os
import sys

# Set environment variables
os.environ.update({
    "API_KEY": "bscatIi9lN86_cJ_waF_kBz6UubjzU0O0onWOEH1kWWUEIBLJrRaPxEnisb_zyCF",
    "EXAPLAY_HOST": "localhost",
    "EXAPLAY_TCP_PORT": "17000",
    "EXAPLAY_OSC_ENABLE": "false", 
    "LOG_LEVEL": "DEBUG",
    "CORS_ALLOW_ORIGINS": "http://localhost:3000,http://localhost:5173,http://localhost:8123",
})

print("🔍 Debug: Starting ExaPlay API")
print("=" * 40)

try:
    print("1. Checking Python path...")
    print(f"   Python executable: {sys.executable}")
    print(f"   Working directory: {os.getcwd()}")
    print(f"   Python path: {sys.path[:3]}...")  # First 3 entries
    
    print("\n2. Checking environment variables...")
    for key in ["API_KEY", "EXAPLAY_HOST", "EXAPLAY_TCP_PORT"]:
        value = os.environ.get(key, "NOT SET")
        if key == "API_KEY":
            value = value[:16] + "..." if len(value) > 16 else value
        print(f"   {key}: {value}")
    
    print("\n3. Testing imports...")
    try:
        import fastapi
        print(f"   ✅ FastAPI version: {fastapi.__version__}")
    except ImportError as e:
        print(f"   ❌ FastAPI import failed: {e}")
        sys.exit(1)
    
    try:
        import uvicorn
        print(f"   ✅ Uvicorn imported successfully")
    except ImportError as e:
        print(f"   ❌ Uvicorn import failed: {e}")
        sys.exit(1)
    
    print("\n4. Testing app import...")
    try:
        from app.main import app
        print("   ✅ App imported successfully")
    except ImportError as e:
        print(f"   ❌ App import failed: {e}")
        print(f"   Make sure you're in the correct directory with 'app' folder")
        sys.exit(1)
    except Exception as e:
        print(f"   ❌ App import error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n5. Testing app configuration...")
    try:
        # Test that settings are loaded
        from app.settings import settings
        print(f"   ✅ Settings loaded")
        print(f"   ExaPlay Host: {settings.exaplay_host}")
        print(f"   ExaPlay Port: {settings.exaplay_tcp_port}")
        print(f"   API Key: {settings.api_key[:16]}...")
    except Exception as e:
        print(f"   ❌ Settings error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n6. Starting server...")
    print("   Server will start on http://localhost:8000")
    print("   Press Ctrl+C to stop")
    print("=" * 40)
    
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=8000,
        log_level="debug"
    )
    
except KeyboardInterrupt:
    print("\n👋 Stopped by user")
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
