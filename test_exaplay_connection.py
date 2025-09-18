#!/usr/bin/env python3
"""Test direct connection to your ExaPlay server."""

import asyncio
import socket

async def test_exaplay_tcp():
    """Test connection to real ExaPlay server."""
    print("🧪 Testing ExaPlay TCP Connection")
    print("=" * 40)
    
    host = "localhost"
    port = 7000
    
    print(f"1. Testing socket connection to {host}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print("   ✅ Socket connection successful")
        else:
            print(f"   ❌ Socket connection failed: {result}")
            print("   💡 Make sure ExaPlay is running and TCP is enabled on *:7000")
            return False
    except Exception as e:
        print(f"   ❌ Socket test error: {e}")
        return False
    
    print("\n2. Testing ExaPlay protocol...")
    try:
        # Open connection
        reader, writer = await asyncio.open_connection(host, port)
        
        # Test version command
        print("   📋 Testing version command...")
        command = "get:ver\r"
        writer.write(command.encode('utf-8'))
        await writer.drain()
        
        response = await asyncio.wait_for(reader.readuntil(b"\r\n"), timeout=5.0)
        version = response.decode('utf-8').strip()
        print(f"   ✅ ExaPlay version: {version}")
        
        # Test hello command
        print("   👋 Testing hello command...")
        command = "hello\r"
        writer.write(command.encode('utf-8'))
        await writer.drain()
        
        response = await asyncio.wait_for(reader.readuntil(b"\r\n"), timeout=5.0)
        hello_response = response.decode('utf-8').strip()
        print(f"   ✅ Hello response: {hello_response}")
        
        # Test timeline 'test1' status
        print("   📊 Testing status for timeline 'test1'...")
        command = "get:status,test1\r"
        writer.write(command.encode('utf-8'))
        await writer.drain()
        
        response = await asyncio.wait_for(reader.readuntil(b"\r\n"), timeout=5.0)
        status = response.decode('utf-8').strip()
        print(f"   📈 Timeline 'test1' status: {status}")
        
        if status.startswith("ERR"):
            print("   ⚠️  Timeline 'test1' might not exist in ExaPlay")
            print("   💡 Make sure timeline 'test1' is created in your ExaPlay project")
        else:
            print("   ✅ Timeline 'test1' found!")
            
            # Try to play timeline 'test1'
            print("   🎬 Testing play command for 'test1'...")
            command = "play,test1\r"
            writer.write(command.encode('utf-8'))
            await writer.drain()
            
            response = await asyncio.wait_for(reader.readuntil(b"\r\n"), timeout=5.0)
            play_response = response.decode('utf-8').strip()
            print(f"   🎮 Play response: {play_response}")
            
            if play_response == "OK":
                print("   🎉 SUCCESS: Timeline 'test1' can be controlled!")
            elif play_response.startswith("ERR"):
                print("   ⚠️  Play command failed - timeline might not be ready")
        
        writer.close()
        await writer.wait_closed()
        
        return True
        
    except asyncio.TimeoutError:
        print("   ❌ Protocol test timeout - ExaPlay not responding")
        return False
    except Exception as e:
        print(f"   ❌ Protocol test failed: {e}")
        return False

if __name__ == "__main__":
    print("This will test direct connection to your ExaPlay server.")
    print("Make sure ExaPlay is running with TCP enabled on *:7000\n")
    
    try:
        success = asyncio.run(test_exaplay_tcp())
        
        if success:
            print(f"\n✅ ExaPlay connection test successful!")
            print("Your ExaPlay server is ready for API control.")
            print("\nNow restart the API server:")
            print("python start_api.py")
        else:
            print(f"\n❌ ExaPlay connection test failed!")
            print("\n🔧 Troubleshooting steps:")
            print("1. Ensure ExaPlay is running on http://localhost:8123/")
            print("2. Go to ExaPlay Settings → Comm tab")
            print("3. Set TCP Listen to: *:7000")
            print("4. Make sure timeline 'test1' exists in your project")
            print("5. Restart ExaPlay if needed")
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
