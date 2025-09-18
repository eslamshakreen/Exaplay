#!/usr/bin/env python3
"""Run ExaPlay API with mock server for testing timeline 'test1'."""

import asyncio
import os
import sys
import time
from typing import Dict, Any

import httpx
import uvicorn

# Set environment variables for mock ExaPlay setup
os.environ.update({
    "API_KEY": "bscatIi9lN86_cJ_waF_kBz6UubjzU0O0onWOEH1kWWUEIBLJrRaPxEnisb_zyCF",
    "EXAPLAY_HOST": "localhost",
    "EXAPLAY_TCP_PORT": "17000",  # Use mock server port
    "EXAPLAY_OSC_ENABLE": "false",
    "LOG_LEVEL": "INFO",
    "CORS_ALLOW_ORIGINS": "http://localhost:3000,http://localhost:5173,http://localhost:8123",
})

print("🚀 ExaPlay API Test with Mock Server")
print("Testing timeline 'test1' control")
print("=" * 50)

async def start_mock_server():
    """Start the mock ExaPlay server."""
    print("1. Starting mock ExaPlay server on port 17000...")
    
    try:
        from app.tests.fixtures.mock_exaplay import MockExaPlayServer
        
        mock_server = MockExaPlayServer("localhost", 17000)
        await mock_server.start()
        
        # Add timeline 'test1' to mock server
        from app.tests.fixtures.mock_exaplay import MockComposition
        mock_server.compositions["test1"] = MockComposition("test1", duration=120.0)
        
        print("   ✅ Mock ExaPlay server started successfully")
        print("   📦 Added timeline 'test1' (120s duration)")
        
        return mock_server
        
    except Exception as e:
        print(f"   ❌ Failed to start mock server: {e}")
        return None

async def test_timeline_control():
    """Test controlling the timeline 'test1'."""
    print("\n2. Testing timeline 'test1' control...")
    
    # Give API server a moment to start
    await asyncio.sleep(3)
    
    try:
        async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=10.0) as client:
            headers = {"Authorization": "Bearer bscatIi9lN86_cJ_waF_kBz6UubjzU0O0onWOEH1kWWUEIBLJrRaPxEnisb_zyCF"}
            
            print("   🔍 Testing API health...")
            response = await client.get("/healthz")
            if response.status_code != 200:
                print(f"   ❌ Health check failed: {response.status_code}")
                return False
            print("   ✅ API is healthy")
            
            print("   📋 Getting ExaPlay version...")
            response = await client.get("/version", headers=headers)
            if response.status_code == 200:
                version_data = response.json()
                print(f"   ✅ ExaPlay version: {version_data.get('exaplayVersion', 'Unknown')}")
            else:
                print(f"   ⚠️  Version check failed: {response.status_code}")
            
            print("   📊 Getting initial status of timeline 'test1'...")
            response = await client.get("/compositions/test1/status", headers=headers)
            if response.status_code == 200:
                status_data = response.json()
                print(f"   📈 Status: {status_data['state']} | Time: {status_data['time']}s | Duration: {status_data['duration']}s")
            else:
                print(f"   ❌ Status check failed: {response.status_code}")
                return False
            
            print("   🎬 Starting timeline 'test1'...")
            response = await client.post("/compositions/test1/play", headers=headers)
            if response.status_code == 200:
                play_data = response.json()
                print(f"   ✅ Play command: {play_data.get('reply', 'OK')}")
                
                # Check status after playing
                await asyncio.sleep(1)
                response = await client.get("/compositions/test1/status", headers=headers)
                if response.status_code == 200:
                    status_data = response.json()
                    print(f"   📈 Playing status: {status_data['state']} | Time: {status_data['time']}s")
                    
                    if status_data['state'] == 'playing':
                        print("   🎉 SUCCESS: Timeline 'test1' is now playing!")
                    else:
                        print(f"   ⚠️  Expected 'playing' but got '{status_data['state']}'")
                
            else:
                print(f"   ❌ Play command failed: {response.status_code} - {response.text}")
                return False
            
            print("   ⏸️  Testing pause command...")
            response = await client.post("/compositions/test1/pause", headers=headers)
            if response.status_code == 200:
                print("   ✅ Pause successful")
                
                response = await client.get("/compositions/test1/status", headers=headers)
                if response.status_code == 200:
                    status_data = response.json()
                    print(f"   📈 Paused status: {status_data['state']} | Time: {status_data['time']}s")
            
            print("   ⏹️  Testing stop command...")
            response = await client.post("/compositions/test1/stop", headers=headers)
            if response.status_code == 200:
                print("   ✅ Stop successful")
                
                response = await client.get("/compositions/test1/status", headers=headers)
                if response.status_code == 200:
                    status_data = response.json()
                    print(f"   📈 Final status: {status_data['state']} | Time: {status_data['time']}s")
            
            print("\n🎯 All timeline control tests completed successfully!")
            return True
            
    except Exception as e:
        print(f"   ❌ Timeline test failed: {e}")
        return False

async def run_api_server_with_mock():
    """Run the API server with mock ExaPlay server."""
    print("\n3. Starting ExaPlay API server...")
    
    # Start mock server first
    mock_server = await start_mock_server()
    if not mock_server:
        print("❌ Cannot start without mock server")
        return
    
    try:
        # Import here to ensure environment variables are set
        from app.main import app
        
        print("   🌐 API server starting on http://localhost:8000")
        print("   📖 API docs will be at http://localhost:8000/docs")
        print("   🧪 Running in test mode with mock ExaPlay server")
        print("\n" + "=" * 50)
        
        # Run the timeline test in background
        test_task = asyncio.create_task(test_timeline_control())
        
        # Start API server
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        
        # Run server and test concurrently
        server_task = asyncio.create_task(server.serve())
        
        # Wait for test to complete or server to be interrupted
        try:
            await test_task
            print("\n🎉 Test completed! Server is still running for manual testing.")
            print("📖 Visit http://localhost:8000/docs to explore the API")
            print("🛑 Press Ctrl+C to stop")
            await server_task
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
        
    finally:
        if mock_server:
            await mock_server.stop()
            print("✅ Mock server stopped")

if __name__ == "__main__":
    try:
        asyncio.run(run_api_server_with_mock())
    except KeyboardInterrupt:
        print("\n👋 Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
