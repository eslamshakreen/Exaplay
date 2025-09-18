#!/usr/bin/env python3
"""Quick test script to verify the ExaPlay API is working correctly.

This script starts a mock ExaPlay server and tests basic API functionality.
Run this to verify your installation is working.
"""

import asyncio
import os
import sys
import time
from typing import Dict, Any

import httpx
import uvicorn

# Set environment variables for testing
os.environ.update({
    "API_KEY": "test_api_key_12345678901234567890123456789012",
    "EXAPLAY_HOST": "127.0.0.1",
    "EXAPLAY_TCP_PORT": "17000",
    "EXAPLAY_OSC_ENABLE": "false",
    "LOG_LEVEL": "INFO",
})

from app.tests.fixtures.mock_exaplay import MockExaPlayServer


async def test_api_functionality():
    """Test basic API functionality against mock server."""
    
    print("🚀 Starting ExaPlay API Test Suite")
    print("=" * 50)
    
    # Start mock ExaPlay server
    print("1. Starting mock ExaPlay server...")
    mock_server = MockExaPlayServer("127.0.0.1", 17000)
    await mock_server.start()
    
    # Give server a moment to start
    await asyncio.sleep(1)
    
    try:
        # Test API endpoints
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            headers = {"Authorization": "Bearer test_api_key_12345678901234567890123456789012"}
            
            print("2. Testing health endpoint...")
            response = await client.get("/healthz")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"
            print("   ✅ Health check passed")
            
            print("3. Testing version endpoint...")
            response = await client.get("/version", headers=headers)
            assert response.status_code == 200
            version_data = response.json()
            assert "exaplayVersion" in version_data
            print(f"   ✅ Version: {version_data['exaplayVersion']}")
            
            print("4. Testing composition control...")
            
            # Play composition
            response = await client.post("/compositions/test_comp/play", headers=headers)
            assert response.status_code == 200
            play_data = response.json()
            assert play_data["reply"] == "OK"
            print("   ✅ Play command successful")
            
            # Get status
            response = await client.get("/compositions/test_comp/status", headers=headers)
            assert response.status_code == 200
            status_data = response.json()
            assert status_data["state"] == "playing"
            print(f"   ✅ Status: {status_data['state']} at {status_data['time']}s")
            
            # Set volume
            response = await client.post(
                "/compositions/test_comp/volume",
                json={"value": 80},
                headers=headers
            )
            assert response.status_code == 200
            print("   ✅ Volume set successfully")
            
            # Get volume
            response = await client.get("/compositions/test_comp/volume", headers=headers)
            assert response.status_code == 200
            volume_data = response.json()
            assert volume_data["value"] == 80
            print(f"   ✅ Volume confirmed: {volume_data['value']}")
            
            # Pause composition
            response = await client.post("/compositions/test_comp/pause", headers=headers)
            assert response.status_code == 200
            print("   ✅ Pause command successful")
            
            # Stop composition
            response = await client.post("/compositions/test_comp/stop", headers=headers)
            assert response.status_code == 200
            print("   ✅ Stop command successful")
            
            print("5. Testing admin endpoint...")
            response = await client.post(
                "/exaplay/command",
                json={"raw": "get:ver"},
                headers=headers
            )
            assert response.status_code == 200
            cmd_data = response.json()
            assert "2.21.0.0" in cmd_data["reply"]
            print("   ✅ Raw command successful")
            
    finally:
        # Clean up
        await mock_server.stop()
    
    print("\n🎉 All tests passed! ExaPlay API is working correctly.")
    print("📚 Visit http://localhost:8000/docs for interactive API documentation")


def run_api_server():
    """Run the API server for testing."""
    print("6. Starting ExaPlay API server...")
    print("   🌐 Server will be available at http://localhost:8000")
    print("   📖 API docs at http://localhost:8000/docs")
    print("   🛑 Press Ctrl+C to stop")
    
    # Import here to avoid circular imports
    from app.main import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


async def main():
    """Main test function."""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--server-only":
        # Just run the server
        run_api_server()
        return
    
    try:
        # Run tests first
        await test_api_functionality()
        
        print("\n" + "=" * 50)
        print("🎯 Quick API Test Complete!")
        print("")
        print("Next steps:")
        print("1. Run with real ExaPlay: Update EXAPLAY_HOST in your .env")
        print("2. Start development server: uvicorn app.main:app --reload")
        print("3. Run full test suite: pytest")
        print("4. Deploy with Docker: docker-compose up")
        print("")
        print("For production deployment, see README.md")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Check that all dependencies are installed and try again.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--server-only":
            run_api_server()
        else:
            asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
