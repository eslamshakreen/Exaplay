#!/usr/bin/env python3
"""Test direct connection to ExaPlay at 10.5.0.2:7000."""

import asyncio
import time

async def test_exaplay_direct():
    """Test connection to ExaPlay at 10.5.0.2:7000."""
    print("🧪 Testing ExaPlay at 10.5.0.2:7000")
    print("=" * 40)
    
    host = "10.5.0.2"
    port = 7000
    
    try:
        print(f"1. Connecting to {host}:{port}...")
        start_time = time.time()
        
        reader, writer = await asyncio.open_connection(host, port)
        connect_time = time.time() - start_time
        print(f"   ✅ Connected in {connect_time:.2f}s")
        
        # Test version command (this works)
        print("2. Testing version command...")
        start_time = time.time()
        
        command = "get:ver\r"
        writer.write(command.encode('utf-8'))
        await writer.drain()
        
        response = await asyncio.wait_for(reader.readuntil(b"\r\n"), timeout=10.0)
        version_time = time.time() - start_time
        version = response.decode('utf-8').strip()
        print(f"   ✅ Version: {version} (took {version_time:.2f}s)")
        
        # Test status command for test1
        print("3. Testing status command for 'test1'...")
        start_time = time.time()
        
        command = "get:status,test1\r"
        writer.write(command.encode('utf-8'))
        await writer.drain()
        
        response = await asyncio.wait_for(reader.readuntil(b"\r\n"), timeout=10.0)
        status_time = time.time() - start_time
        status = response.decode('utf-8').strip()
        print(f"   📊 Status: {status} (took {status_time:.2f}s)")
        
        if status.startswith("ERR"):
            print("   ⚠️  Timeline 'test1' not found or not accessible")
            print("   💡 Make sure timeline 'test1' exists in ExaPlay")
        else:
            print("   ✅ Timeline 'test1' found!")
            
            # Test play command
            print("4. Testing play command for 'test1'...")
            start_time = time.time()
            
            command = "play,test1\r"
            writer.write(command.encode('utf-8'))
            await writer.drain()
            
            response = await asyncio.wait_for(reader.readuntil(b"\r\n"), timeout=10.0)
            play_time = time.time() - start_time
            play_response = response.decode('utf-8').strip()
            print(f"   🎮 Play: {play_response} (took {play_time:.2f}s)")
            
            if play_response == "OK":
                print("   🎉 SUCCESS: Play command works!")
                
                # Check status after play
                print("5. Checking status after play...")
                command = "get:status,test1\r"
                writer.write(command.encode('utf-8'))
                await writer.drain()
                
                response = await asyncio.wait_for(reader.readuntil(b"\r\n"), timeout=10.0)
                new_status = response.decode('utf-8').strip()
                print(f"   📈 New status: {new_status}")
                
            elif play_response.startswith("ERR"):
                print(f"   ❌ Play failed: {play_response}")
            
        writer.close()
        await writer.wait_closed()
        
        return True
        
    except asyncio.TimeoutError:
        print("   ❌ TCP timeout - ExaPlay taking too long to respond")
        return False
    except ConnectionRefusedError:
        print("   ❌ Connection refused - ExaPlay TCP not listening")
        return False
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing direct connection to your ExaPlay server...")
    print("This will help debug the TCP timeout issue.\n")
    
    try:
        success = asyncio.run(test_exaplay_direct())
        
        if success:
            print(f"\n✅ Direct TCP connection works!")
            print("The issue might be in the API server configuration.")
            print("\nTry restarting the API server:")
            print("python start_api.py")
        else:
            print(f"\n❌ Direct TCP connection failed!")
            print("This explains the 504 timeout in the API.")
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
