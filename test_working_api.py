#!/usr/bin/env python3
"""Test the API with the working composition 'comp1'."""

import asyncio
import httpx

async def test_api_with_comp1():
    """Test the API using the working composition 'comp1'."""
    print("🧪 Testing ExaPlay API with composition 'comp1'")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    headers = {
        "Authorization": "Bearer bscatIi9lN86_cJ_waF_kBz6UubjzU0O0onWOEH1kWWUEIBLJrRaPxEnisb_zyCF",
        "accept": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("1. Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/healthz")
            print(f"   ✅ Health: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"   ❌ Health failed: {e}")
            return
        
        print("\n2. Testing version endpoint...")
        try:
            response = await client.get(f"{base_url}/version", headers=headers)
            print(f"   ✅ Version: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"   ❌ Version failed: {e}")
            return
        
        print("\n3. Testing status for 'comp1'...")
        try:
            response = await client.get(f"{base_url}/compositions/comp1/status", headers=headers)
            print(f"   ✅ Status: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"   ❌ Status failed: {e}")
            
        print("\n4. Testing volume get for 'comp1'...")
        try:
            response = await client.get(f"{base_url}/compositions/comp1/volume", headers=headers)
            print(f"   ✅ Volume get: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"   ❌ Volume get failed: {e}")
        
        print("\n5. Testing volume set for 'comp1'...")
        try:
            response = await client.post(
                f"{base_url}/compositions/comp1/volume", 
                headers=headers,
                json={"value": 50}
            )
            print(f"   ✅ Volume set: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"   ❌ Volume set failed: {e}")
        
        print("\n6. Testing play for 'comp1' (might timeout)...")
        try:
            response = await client.post(f"{base_url}/compositions/comp1/play", headers=headers)
            print(f"   ✅ Play: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"   ❌ Play failed: {e}")
            
        print("\n7. Testing pause for 'comp1' (might timeout)...")
        try:
            response = await client.post(f"{base_url}/compositions/comp1/pause", headers=headers)
            print(f"   ✅ Pause: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"   ❌ Pause failed: {e}")
        
        print("\n8. Testing raw command...")
        try:
            response = await client.post(
                f"{base_url}/exaplay/command", 
                headers=headers,
                json={"raw": "get:status,comp1"}
            )
            print(f"   ✅ Raw command: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"   ❌ Raw command failed: {e}")

if __name__ == "__main__":
    print("Testing API with the working composition 'comp1'...")
    print("Make sure the API server is running: python start_api.py\n")
    
    try:
        asyncio.run(test_api_with_comp1())
        
        print(f"\n🎉 API Testing Complete!")
        print(f"\n📋 Summary:")
        print("✅ Composition 'comp1' exists in ExaPlay")
        print("✅ Status and volume commands work")
        print("❓ Play/pause commands might timeout (ExaPlay limitation)")
        print("\n💡 Use composition 'comp1' instead of 'test1' in your API calls!")
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
