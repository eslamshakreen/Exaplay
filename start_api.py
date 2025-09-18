#!/usr/bin/env python3
"""Simple script to start the ExaPlay API server."""

import os
import uvicorn

# Set environment variables
os.environ.update({
    "API_KEY": "bscatIi9lN86_cJ_waF_kBz6UubjzU0O0onWOEH1kWWUEIBLJrRaPxEnisb_zyCF",
    "EXAPLAY_HOST": "10.5.0.2",
    "EXAPLAY_TCP_PORT": "7000",  # Real ExaPlay TCP port
    "EXAPLAY_OSC_ENABLE": "false",
    "LOG_LEVEL": "INFO",
    "CORS_ALLOW_ORIGINS": "http://localhost:3000,http://localhost:5173,http://localhost:8123",
})

print("🚀 Starting ExaPlay Control API")
print("=" * 40)
print("📋 Configuration:")
print(f"   API Key: {os.environ['API_KEY'][:16]}...")
print(f"   ExaPlay Host: {os.environ['EXAPLAY_HOST']}")
print(f"   ExaPlay TCP Port: {os.environ['EXAPLAY_TCP_PORT']}")
print(f"   OSC Enabled: {os.environ['EXAPLAY_OSC_ENABLE']}")
print(f"   Log Level: {os.environ['LOG_LEVEL']}")
print()
print("🌐 Server will start at: http://localhost:8000")
print("📖 API Docs at: http://localhost:8000/docs")
print("🛑 Press Ctrl+C to stop")
print("=" * 40)

if __name__ == "__main__":
    try:
        from app.main import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False
        )
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're in the correct directory and virtual environment is active")
    except Exception as e:
        print(f"❌ Error: {e}")
