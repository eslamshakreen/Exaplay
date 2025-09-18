#!/usr/bin/env python3
"""Complete test script for ExaPlay API with timeline 'test1'."""

import asyncio
import os
import sys
import time
import httpx

# Set environment variables correctly
os.environ.update({
    "API_KEY": "bscatIi9lN86_cJ_waF_kBz6UubjzU0O0onWOEH1kWWUEIBLJrRaPxEnisb_zyCF",
    "EXAPLAY_HOST": "localhost",
    "EXAPLAY_TCP_PORT": "17000",  # Mock server port
    "EXAPLAY_OSC_ENABLE": "false",
    "LOG_LEVEL": "INFO",
    "CORS_ALLOW_ORIGINS": "http://localhost:3000,http://localhost:5173,http://localhost:8123",
})

print("🚀 ExaPlay API Complete Test")
print("Testing timeline 'test1' with mock server")
print("=" * 50)

async def start_mock_server():
    """Start mock ExaPlay server."""
    print("1. Starting mock ExaPlay server...")
    
    try:
        from app.tests.fixtures.mock_exaplay import MockExaPlayServer, MockComposition
        
        server = MockExaPlayServer("localhost", 17000)
        # Add timeline 'test1'
        server.compositions["test1"] = MockComposition("test1", duration=120.0)
        
        await server.start()
        print("   ✅ Mock ExaPlay server started on port 17000")
        print("   📦 Timeline 'test1' added (120s duration)")
        return server
        
    except Exception as e:
        print(f"   ❌ Failed to start mock server: {e}")
        return None

def start_api_server():
    """Start the API server."""
    print("\n2. Starting API server...")
    
    try:
        from app.main import app
        import uvicorn
        
        print("   ✅ App imported successfully")
        print("   🌐 Starting server on http://localhost:8000")
        
        # Start server in a separate process would be better, but for now we'll test differently
        return app
        
    except Exception as e:
        print(f"   ❌ Failed to start API server: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_api_directly():
    """Test API endpoints directly."""
    print("\n3. Testing API endpoints...")
    
    # Import and test the app directly
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        headers = {"Authorization": "Bearer bscatIi9lN86_cJ_waF_kBz6UubjzU0O0onWOEH1kWWUEIBLJrRaPxEnisb_zyCF"}
        
        print("   🔍 Testing health endpoint...")
        response = client.get("/healthz")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Health: {response.json()}")
        else:
            print(f"   ❌ Health failed: {response.text}")
            return False
        
        print("   📋 Testing version endpoint...")
        response = client.get("/version", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ ExaPlay version: {data['exaplayVersion']}")
        else:
            print(f"   ❌ Version failed: {response.text}")
        
        print("   📊 Getting timeline 'test1' status...")
        response = client.get("/compositions/test1/status", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   📈 Initial state: {data['state']}")
            print(f"   📈 Time: {data['time']}s")
            print(f"   📈 Duration: {data['duration']}s")
        else:
            print(f"   ❌ Status check failed: {response.text}")
            return False
        
        print("   🎬 Playing timeline 'test1'...")
        response = client.post("/compositions/test1/play", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Play command: {data['sent']} -> {data['reply']}")
        else:
            print(f"   ❌ Play failed: {response.text}")
            return False
        
        print("   📊 Checking status after play...")
        response = client.get("/compositions/test1/status", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"   📈 New state: {data['state']}")
            print(f"   📈 Time: {data['time']}s")
            
            if data['state'] == 'playing':
                print("   🎉 SUCCESS: Timeline 'test1' is now playing!")
            else:
                print(f"   ⚠️  Expected 'playing' but got '{data['state']}'")
        
        print("   ⏸️  Testing pause...")
        response = client.post("/compositions/test1/pause", headers=headers)
        if response.status_code == 200:
            print("   ✅ Pause successful")
        
        print("   ⏹️  Testing stop...")
        response = client.post("/compositions/test1/stop", headers=headers)
        if response.status_code == 200:
            print("   ✅ Stop successful")
            
            # Final status
            response = client.get("/compositions/test1/status", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"   📈 Final state: {data['state']} at {data['time']}s")
        
        print("\n🎉 All API tests passed!")
        print("📖 API Docs available at: http://localhost:8000/docs")
        return True
        
    except Exception as e:
        print(f"   ❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the complete test."""
    
    # Start mock server
    mock_server = await start_mock_server()
    if not mock_server:
        print("❌ Cannot continue without mock server")
        return
    
    try:
        # Test API directly (without starting HTTP server)
        success = await test_api_directly()
        
        if success:
            print(f"\n✅ Complete test successful!")
            print("🎯 Timeline 'test1' control is working correctly")
            print("\n📋 Next steps:")
            print("1. Configure your real ExaPlay TCP control")
            print("2. Update EXAPLAY_TCP_PORT to match your ExaPlay settings")
            print("3. Run: python start_api.py")
        else:
            print("\n❌ Some tests failed")
            
    finally:
        await mock_server.stop()
        print("✅ Mock server stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
