#!/usr/bin/env python3
"""Test script to run ExaPlay API and test timeline 'test1'."""

import asyncio
import os
import sys
import time
from typing import Dict, Any

import httpx
import uvicorn

# Set environment variables for our ExaPlay setup
os.environ.update({
    "API_KEY": "bscatIi9lN86_cJ_waF_kBz6UubjzU0O0onWOEH1kWWUEIBLJrRaPxEnisb_zyCF",
    "EXAPLAY_HOST": "localhost",  # Your ExaPlay is running locally
    "EXAPLAY_TCP_PORT": "7000",   # Default ExaPlay TCP port
    "EXAPLAY_OSC_ENABLE": "false",
    "LOG_LEVEL": "DEBUG",
    "CORS_ALLOW_ORIGINS": "http://localhost:3000,http://localhost:5173,http://localhost:8123",
})

print("🚀 ExaPlay API Test with Timeline 'test1'")
print("=" * 50)

async def test_exaplay_connection():
    """Test connection to ExaPlay server."""
    print("1. Testing ExaPlay TCP connection...")
    
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', 7000))
        sock.close()
        
        if result == 0:
            print("   ✅ ExaPlay TCP port 7000 is accessible")
            return True
        else:
            print("   ❌ Cannot connect to ExaPlay TCP port 7000")
            print("   💡 Make sure ExaPlay is running and TCP control is enabled")
            return False
    except Exception as e:
        print(f"   ❌ Connection test failed: {e}")
        return False

async def test_timeline_control():
    """Test controlling the timeline 'test1'."""
    print("\n2. Testing timeline 'test1' control...")
    
    # Give API server a moment to start
    await asyncio.sleep(2)
    
    try:
        async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=10.0) as client:
            headers = {"Authorization": "Bearer bscatIi9lN86_cJ_waF_kBz6UubjzU0O0onWOEH1kWWUEIBLJrRaPxEnisb_zyCF"}
            
            print("   Testing health endpoint...")
            response = await client.get("/healthz")
            if response.status_code != 200:
                print(f"   ❌ Health check failed: {response.status_code}")
                return False
            print("   ✅ API health check passed")
            
            print("   Testing ExaPlay version...")
            response = await client.get("/version", headers=headers)
            if response.status_code == 200:
                version_data = response.json()
                print(f"   ✅ ExaPlay version: {version_data.get('exaplayVersion', 'Unknown')}")
            else:
                print(f"   ⚠️  Version check failed: {response.status_code} - {response.text}")
            
            print("   Getting initial status of 'test1'...")
            response = await client.get("/compositions/test1/status", headers=headers)
            if response.status_code == 200:
                status_data = response.json()
                print(f"   📊 Initial status: {status_data['state']} at {status_data['time']}s")
            else:
                print(f"   ⚠️  Status check failed: {response.status_code} - {response.text}")
            
            print("   🎬 Starting timeline 'test1'...")
            response = await client.post("/compositions/test1/play", headers=headers)
            if response.status_code == 200:
                play_data = response.json()
                print(f"   ✅ Play command successful: {play_data.get('reply', 'OK')}")
                
                # Check status after playing
                await asyncio.sleep(1)
                response = await client.get("/compositions/test1/status", headers=headers)
                if response.status_code == 200:
                    status_data = response.json()
                    print(f"   📊 After play: {status_data['state']} at {status_data['time']}s")
                    if status_data['state'] == 'playing':
                        print("   🎉 Timeline 'test1' is now playing!")
                    else:
                        print(f"   ⚠️  Timeline state is '{status_data['state']}' instead of 'playing'")
                
            else:
                print(f"   ❌ Play command failed: {response.status_code} - {response.text}")
                return False
            
            # Test pause
            print("   ⏸️  Testing pause...")
            response = await client.post("/compositions/test1/pause", headers=headers)
            if response.status_code == 200:
                print("   ✅ Pause command successful")
            
            # Test stop
            print("   ⏹️  Testing stop...")
            response = await client.post("/compositions/test1/stop", headers=headers)
            if response.status_code == 200:
                print("   ✅ Stop command successful")
                
                # Final status check
                response = await client.get("/compositions/test1/status", headers=headers)
                if response.status_code == 200:
                    status_data = response.json()
                    print(f"   📊 Final status: {status_data['state']} at {status_data['time']}s")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Timeline test failed: {e}")
        return False

def run_api_server():
    """Run the ExaPlay API server."""
    print("\n3. Starting ExaPlay API server...")
    print("   🌐 Server running at http://localhost:8000")
    print("   📖 API docs at http://localhost:8000/docs")
    print("   🛑 Press Ctrl+C to stop\n")
    
    from app.main import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

async def main():
    """Main function to run all tests."""
    
    # Test ExaPlay connection first
    if not await test_exaplay_connection():
        print("\n❌ ExaPlay connection failed. Please check:")
        print("   1. ExaPlay is running on localhost")
        print("   2. TCP control is enabled in ExaPlay settings")
        print("   3. Port 7000 is not blocked by firewall")
        print("   4. Timeline 'test1' exists in ExaPlay")
        sys.exit(1)
    
    print("\n✅ ExaPlay connection successful!")
    print("\nStarting API server to test timeline control...")
    print("The API will start and automatically test the 'test1' timeline.\n")
    
    # Run API server (this will block)
    run_api_server()

if __name__ == "__main__":
    try:
        # First test connection without starting server
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if "--test-only" in sys.argv:
            # Just run the timeline test
            loop.run_until_complete(test_timeline_control())
        else:
            # Run full setup
            loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
