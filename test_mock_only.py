#!/usr/bin/env python3
"""Test only the mock server connection."""

import asyncio
import socket

async def test_mock_connection():
    """Test direct connection to mock ExaPlay server."""
    print("🧪 Testing Mock ExaPlay Server Connection")
    print("=" * 50)
    
    print("1. Starting mock server...")
    try:
        from app.tests.fixtures.mock_exaplay import MockExaPlayServer, MockComposition
        
        server = MockExaPlayServer("localhost", 17000)
        server.compositions["test1"] = MockComposition("test1", duration=120.0)
        
        await server.start()
        print("   ✅ Mock server started on port 17000")
        
        # Wait a moment for server to be ready
        await asyncio.sleep(1)
        
        print("\n2. Testing socket connection...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 17000))
            sock.close()
            
            if result == 0:
                print("   ✅ Socket connection successful")
            else:
                print(f"   ❌ Socket connection failed: {result}")
                return False
        except Exception as e:
            print(f"   ❌ Socket test error: {e}")
            return False
        
        print("\n3. Testing ExaPlay TCP protocol...")
        try:
            # Open connection
            reader, writer = await asyncio.open_connection('localhost', 17000)
            
            # Send version command
            command = "get:ver\r"
            writer.write(command.encode('utf-8'))
            await writer.drain()
            
            # Read response
            response = await asyncio.wait_for(reader.readuntil(b"\r\n"), timeout=2.0)
            response_str = response.decode('utf-8').strip()
            
            print(f"   ✅ ExaPlay protocol test successful")
            print(f"   📦 Version response: {response_str}")
            
            # Test status command for test1
            command = "get:status,test1\r"
            writer.write(command.encode('utf-8'))
            await writer.drain()
            
            response = await asyncio.wait_for(reader.readuntil(b"\r\n"), timeout=2.0)
            response_str = response.decode('utf-8').strip()
            
            print(f"   📊 Status response: {response_str}")
            
            # Test play command
            command = "play,test1\r"
            writer.write(command.encode('utf-8'))
            await writer.drain()
            
            response = await asyncio.wait_for(reader.readuntil(b"\r\n"), timeout=2.0)
            response_str = response.decode('utf-8').strip()
            
            print(f"   🎬 Play response: {response_str}")
            
            writer.close()
            await writer.wait_closed()
            
            print("\n🎉 Mock server is working correctly!")
            return True
            
        except Exception as e:
            print(f"   ❌ Protocol test failed: {e}")
            return False
        
    except Exception as e:
        print(f"   ❌ Failed to start mock server: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            await server.stop()
            print("\n✅ Mock server stopped")
        except:
            pass

if __name__ == "__main__":
    try:
        result = asyncio.run(test_mock_connection())
        if result:
            print("\n✅ Mock server test successful!")
            print("The mock server is working correctly.")
        else:
            print("\n❌ Mock server test failed!")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
