#!/usr/bin/env python3
"""Script to find ExaPlay TCP control port and test connection."""

import socket
import time

def test_port(host, port):
    """Test if a port is open and responsive."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def scan_common_ports():
    """Scan common ExaPlay TCP ports."""
    print("🔍 Scanning for ExaPlay TCP control ports...")
    print("=" * 50)
    
    host = "localhost"
    common_ports = [7000, 7001, 7002, 8000, 8001, 8123, 9000, 9001, 9999, 10000]
    
    open_ports = []
    
    for port in common_ports:
        print(f"Testing port {port}...", end=" ")
        if test_port(host, port):
            print("✅ OPEN")
            open_ports.append(port)
        else:
            print("❌ CLOSED")
    
    if open_ports:
        print(f"\n📍 Found {len(open_ports)} open ports: {open_ports}")
        
        # Test if any port responds like ExaPlay TCP
        for port in open_ports:
            print(f"\n🧪 Testing port {port} for ExaPlay TCP protocol...")
            if test_exaplay_protocol(host, port):
                print(f"✅ Port {port} appears to be ExaPlay TCP!")
                return port
            else:
                print(f"❌ Port {port} is not ExaPlay TCP")
    else:
        print("\n❌ No open ports found on common ExaPlay ports")
    
    return None

def test_exaplay_protocol(host, port):
    """Test if a port responds to ExaPlay commands."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        
        # Send ExaPlay version command
        command = "get:ver\r"
        sock.send(command.encode('utf-8'))
        
        # Try to read response
        response = sock.recv(1024).decode('utf-8')
        sock.close()
        
        print(f"   📦 Response: {response.strip()}")
        
        # Check if response looks like ExaPlay version
        if response and (
            any(char.isdigit() for char in response) and 
            ('.' in response or 'ExaPlay' in response or 'OK' in response)
        ):
            return True
        
    except Exception as e:
        print(f"   ⚠️  Protocol test error: {e}")
    
    return False

if __name__ == "__main__":
    print("🚀 ExaPlay TCP Port Scanner")
    print("=" * 50)
    print("This script will help you find the correct ExaPlay TCP control port.")
    print("Make sure ExaPlay is running with TCP control enabled.\n")
    
    # Check if ExaPlay web interface is accessible
    if test_port("localhost", 8123):
        print("✅ ExaPlay web interface is accessible on port 8123")
    else:
        print("❌ ExaPlay web interface not accessible on port 8123")
        print("   Make sure ExaPlay is running first")
    
    print()
    
    # Scan for TCP control port
    tcp_port = scan_common_ports()
    
    if tcp_port:
        print(f"\n🎉 Found ExaPlay TCP control on port {tcp_port}!")
        print(f"\nTo use this port, update your environment:")
        print(f"EXAPLAY_TCP_PORT={tcp_port}")
        print(f"\nOr run the test with:")
        print(f"python run_test_with_port.py {tcp_port}")
    else:
        print("\n❌ Could not find ExaPlay TCP control port.")
        print("\n📋 Steps to enable TCP control in ExaPlay:")
        print("1. Open ExaPlay interface at http://localhost:8123/")
        print("2. Go to Settings/Preferences")
        print("3. Look for 'TCP Control' or 'Network' settings")
        print("4. Enable TCP control and note the port number")
        print("5. Common default ports are 7000, 7001, or 9000")
        print("6. Restart ExaPlay if needed")
        
    print("\n" + "=" * 50)
    print("Once TCP control is enabled, run: python run_test.py")
