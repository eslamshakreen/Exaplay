#!/usr/bin/env python3
"""Debug which ExaPlay commands work."""

import asyncio

async def test_command(reader, writer, command, timeout=5.0):
    """Test a single ExaPlay command."""
    try:
        print(f"   Testing: {command}")
        writer.write(f"{command}\r".encode('utf-8'))
        await writer.drain()
        
        response = await asyncio.wait_for(reader.readuntil(b"\r\n"), timeout=timeout)
        result = response.decode('utf-8').strip()
        print(f"   ✅ Response: {result}")
        return result
    except asyncio.TimeoutError:
        print(f"   ❌ TIMEOUT after {timeout}s")
        return None
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return None

async def debug_exaplay():
    """Debug ExaPlay commands to find what works."""
    print("🔍 Debugging ExaPlay Commands")
    print("=" * 40)
    
    host = "10.5.0.2"
    port = 7000
    
    try:
        reader, writer = await asyncio.open_connection(host, port)
        print(f"✅ Connected to {host}:{port}")
        print()
        
        # Test basic commands that should work
        print("1. Testing basic commands:")
        await test_command(reader, writer, "hello")
        await test_command(reader, writer, "get:ver")
        
        print("\n2. Testing status commands (might fail):")
        # Try different composition names
        compositions = ["test1", "comp1", "timeline1", "Timeline1", "Test1"]
        
        for comp in compositions:
            result = await test_command(reader, writer, f"get:status,{comp}", timeout=3.0)
            if result and not result.startswith("ERR") and result != "":
                print(f"   🎉 FOUND WORKING COMPOSITION: {comp}")
                break
        
        print("\n3. Testing play commands (might fail):")
        for comp in compositions:
            result = await test_command(reader, writer, f"play,{comp}", timeout=3.0)
            if result == "OK":
                print(f"   🎉 PLAY WORKS FOR: {comp}")
                # Test status after play
                status = await test_command(reader, writer, f"get:status,{comp}", timeout=3.0)
                if status:
                    print(f"   📊 Status after play: {status}")
                break
            elif result and result.startswith("ERR"):
                print(f"   ⚠️  Composition '{comp}' exists but can't play: {result}")
        
        writer.close()
        await writer.wait_closed()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

async def list_compositions():
    """Try to find what compositions exist."""
    print("\n🔍 Trying to discover compositions...")
    print("=" * 40)
    
    # Try common composition discovery commands
    # Note: ExaPlay might not have a list command, but we can try
    host = "10.5.0.2"
    port = 7000
    
    try:
        reader, writer = await asyncio.open_connection(host, port)
        
        # Try some discovery commands
        discovery_commands = [
            "list",
            "get:list", 
            "compositions",
            "get:compositions",
            "help",
            "get:help"
        ]
        
        for cmd in discovery_commands:
            result = await test_command(reader, writer, cmd, timeout=2.0)
            if result and not result.startswith("ERR") and result.strip() != "":
                print(f"   📋 Discovery command '{cmd}' returned: {result}")
        
        writer.close()
        await writer.wait_closed()
        
    except Exception as e:
        print(f"❌ Discovery failed: {e}")

if __name__ == "__main__":
    print("This will help find which compositions exist in ExaPlay...")
    print("and debug why the play command times out.\n")
    
    try:
        asyncio.run(debug_exaplay())
        asyncio.run(list_compositions())
        
        print(f"\n💡 Recommendations:")
        print("1. Check ExaPlay UI - what compositions/timelines are actually loaded?")
        print("2. Try creating a simple timeline named 'test1' in ExaPlay")
        print("3. Make sure the timeline has some content")
        print("4. Save the ExaPlay project")
        print("5. If you find working composition names, update the API calls")
        
    except Exception as e:
        print(f"\n❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
