#!/usr/bin/env python3
"""Simple client to test ExaPlay API."""

import asyncio
import httpx
import time

async def test_api():
    """Test the ExaPlay API endpoints."""
    
    print("🧪 Testing ExaPlay API")
    print("=" * 30)
    
    # Wait for server to start
    print("Waiting for API server to start...")
    await asyncio.sleep(5)
    
    headers = {"Authorization": "Bearer bscatIi9lN86_cJ_waF_kBz6UubjzU0O0onWOEH1kWWUEIBLJrRaPxEnisb_zyCF"}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Test health
            print("\n1. Health check...")
            response = await client.get("http://localhost:8000/healthz")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.json()}")
            
            # Test version
            print("\n2. Version check...")
            response = await client.get("http://localhost:8000/version", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Version: {response.json()}")
            
            # Test timeline 'test1' status
            print("\n3. Timeline 'test1' status...")
            response = await client.get("http://localhost:8000/compositions/test1/status", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   State: {data['state']}")
                print(f"   Time: {data['time']}s")
                print(f"   Duration: {data['duration']}s")
            
            # Test play timeline 'test1'
            print("\n4. Playing timeline 'test1'...")
            response = await client.post("http://localhost:8000/compositions/test1/play", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Command: {data['sent']}")
                print(f"   Reply: {data['reply']}")
            
            # Check status after play
            await asyncio.sleep(1)
            response = await client.get("http://localhost:8000/compositions/test1/status", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Timeline is now: {data['state']}")
                print(f"   📊 Playing at: {data['time']}s")
            
            print("\n🎉 API test completed successfully!")
            print("📖 Visit http://localhost:8000/docs for full API documentation")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
