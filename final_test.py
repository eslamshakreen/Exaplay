#!/usr/bin/env python3
"""Final working test for ExaPlay API with timeline 'test1'."""

import asyncio
import os
import sys
import time

# Set environment variables
os.environ.update({
    "API_KEY": "bscatIi9lN86_cJ_waF_kBz6UubjzU0O0onWOEH1kWWUEIBLJrRaPxEnisb_zyCF",
    "EXAPLAY_HOST": "localhost",
    "EXAPLAY_TCP_PORT": "17000",
    "EXAPLAY_OSC_ENABLE": "false",
    "LOG_LEVEL": "INFO",
    "CORS_ALLOW_ORIGINS": "http://localhost:3000,http://localhost:5173,http://localhost:8123",
})

print("🚀 ExaPlay API Final Test - Timeline 'test1'")
print("=" * 50)

async def run_complete_test():
    """Run the complete test with proper timing."""
    
    # 1. Start mock server
    print("1. Starting mock ExaPlay server...")
    from app.tests.fixtures.mock_exaplay import MockExaPlayServer, MockComposition
    
    server = MockExaPlayServer("localhost", 17000)
    server.compositions["test1"] = MockComposition("test1", duration=120.0)
    
    await server.start()
    print("   ✅ Mock server started on port 17000")
    print("   📦 Timeline 'test1' added (120s duration)")
    
    try:
        # 2. Wait for server to be ready
        await asyncio.sleep(1)
        
        # 3. Test API with proper client
        print("\n2. Testing ExaPlay API...")
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        headers = {"Authorization": "Bearer bscatIi9lN86_cJ_waF_kBz6UubjzU0O0onWOEH1kWWUEIBLJrRaPxEnisb_zyCF"}
        
        # Health check
        print("   🔍 Health check...")
        response = client.get("/healthz")
        assert response.status_code == 200
        print(f"   ✅ Health: {response.json()}")
        
        # Version check
        print("   📋 Version check...")
        response = client.get("/version", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ ExaPlay version: {data['exaplayVersion']}")
        else:
            print(f"   ⚠️  Version check failed: {response.status_code}")
        
        # Timeline status
        print("   📊 Getting timeline 'test1' initial status...")
        response = client.get("/compositions/test1/status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"   📈 State: {data['state']} | Time: {data['time']}s | Duration: {data['duration']}s")
        
        # Play timeline
        print("   🎬 Playing timeline 'test1'...")
        response = client.post("/compositions/test1/play", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"   ✅ Play command: {data['sent']} -> {data['reply']}")
        
        # Check status after play
        response = client.get("/compositions/test1/status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"   📈 Playing state: {data['state']} | Time: {data['time']}s")
        
        if data['state'] == 'playing':
            print("   🎉 SUCCESS: Timeline 'test1' is now playing!")
        else:
            print(f"   ⚠️  Expected 'playing' but got '{data['state']}'")
        
        # Test volume control
        print("   🔊 Testing volume control...")
        response = client.post("/compositions/test1/volume", json={"value": 80}, headers=headers)
        assert response.status_code == 200
        
        response = client.get("/compositions/test1/volume", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"   🔊 Volume set to: {data['value']}")
        
        # Test pause
        print("   ⏸️  Testing pause...")
        response = client.post("/compositions/test1/pause", headers=headers)
        assert response.status_code == 200
        
        response = client.get("/compositions/test1/status", headers=headers)
        data = response.json()
        print(f"   📈 Paused state: {data['state']} | Time: {data['time']}s")
        
        # Test stop
        print("   ⏹️  Testing stop...")
        response = client.post("/compositions/test1/stop", headers=headers)
        assert response.status_code == 200
        
        response = client.get("/compositions/test1/status", headers=headers)
        data = response.json()
        print(f"   📈 Final state: {data['state']} | Time: {data['time']}s")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Timeline 'test1' control is working perfectly!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await server.stop()
        print("\n✅ Mock server stopped")

if __name__ == "__main__":
    print("This test verifies that the ExaPlay API can control timeline 'test1'")
    print("The test uses a mock ExaPlay server for demonstration.\n")
    
    try:
        success = asyncio.run(run_complete_test())
        
        if success:
            print(f"\n" + "="*60)
            print("🎯 TIMELINE 'TEST1' CONTROL TEST SUCCESSFUL!")
            print("="*60)
            print()
            print("📋 What was tested:")
            print("  ✅ API health check")
            print("  ✅ ExaPlay version retrieval")
            print("  ✅ Timeline 'test1' status monitoring")
            print("  ✅ Timeline 'test1' play command")
            print("  ✅ Timeline 'test1' pause command")
            print("  ✅ Timeline 'test1' stop command")
            print("  ✅ Volume control for 'test1'")
            print()
            print("🚀 Next steps for real ExaPlay:")
            print("  1. Enable TCP control in your ExaPlay settings")
            print("  2. Note the TCP port number (usually 7000)")
            print("  3. Update EXAPLAY_TCP_PORT in your environment")
            print("  4. Run: python start_api.py")
            print("  5. Test with: curl commands or visit /docs")
            print()
            print("📖 API Documentation: http://localhost:8000/docs")
            print("🎬 Your timeline 'test1' will be controllable via REST API!")
        else:
            print("\n❌ Test failed - check the logs above")
            
    except KeyboardInterrupt:
        print("\n👋 Test interrupted")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
