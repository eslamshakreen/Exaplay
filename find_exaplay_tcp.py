#!/usr/bin/env python3
"""Find ExaPlay TCP port."""

import socket
import asyncio

def test_port(port):
    """Test if a port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    except:
        return False

async def test_exaplay_protocol(port):
    """Test if port responds to ExaPlay commands."""
    try:
        reader, writer = await asyncio.open_connection('localhost', port)
        
        # Send version command
        command = "get:ver\r"
        writer.write(command.encode('utf-8'))
        await writer.drain()
        
        response = await asyncio.wait_for(reader.readuntil(b"\r\n"), timeout=3.0)
        reply = response.decode('utf-8').strip()
        
        writer.close()
        await writer.wait_closed()
        
        # Check if it looks like ExaPlay
        if reply and not reply.startswith("HTTP") and len(reply) > 0:
            return reply
        return None
        
    except:
        return None

async def main():
    print("🔍 Scanning for ExaPlay TCP ports...")
    print("=" * 40)
    
    # Common ExaPlay ports
    ports_to_test = [7000, 7001, 7002, 8000, 8001, 8123, 9000, 9001, 10000, 10001]
    
    open_ports = []
    
    for port in ports_to_test:
        print(f"Testing port {port}...", end=" ", flush=True)
        if test_port(port):
            print("OPEN")
            open_ports.append(port)
        else:
            print("closed")
    
    if not open_ports:
        print("\n❌ No open ports found")
        print("ExaPlay TCP control might not be enabled")
        return
    
    print(f"\n📍 Found {len(open_ports)} open ports: {open_ports}")
    print("\n🧪 Testing for ExaPlay protocol...")
    
    for port in open_ports:
        print(f"\nTesting port {port} for ExaPlay commands...")
        response = await test_exaplay_protocol(port)
        if response:
            print(f"   ✅ Port {port} responds to ExaPlay commands!")
            print(f"   📦 Version response: {response}")
            print(f"\n🎯 FOUND EXAPLAY TCP ON PORT {port}!")
            print(f"\nUpdate your configuration:")
            print(f"EXAPLAY_TCP_PORT={port}")
            return port
        else:
            print(f"   ❌ Port {port} doesn't respond to ExaPlay commands")
    
    print("\n❌ No ExaPlay TCP ports found")
    print("Check ExaPlay TCP configuration in Settings → Comm")

if __name__ == "__main__":
    asyncio.run(main())
