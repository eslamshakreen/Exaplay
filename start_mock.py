#!/usr/bin/env python3
"""Start mock ExaPlay server for testing."""

import asyncio
import sys

async def main():
    """Start the mock ExaPlay server."""
    print("🎭 Starting Mock ExaPlay Server")
    print("=" * 40)
    print("📍 Listening on: localhost:17000")
    print("🎬 Timeline 'test1' will be available")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 40)
    
    try:
        from app.tests.fixtures.mock_exaplay import MockExaPlayServer, MockComposition
        
        server = MockExaPlayServer("localhost", 17000)
        
        # Add test1 timeline
        server.compositions["test1"] = MockComposition("test1", duration=120.0)
        
        await server.start()
        print("✅ Mock server started successfully")
        print("📦 Added timeline 'test1' (120s duration)")
        print("\nReady for API connections!")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Shutting down mock server...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        try:
            await server.stop()
        except:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Mock server stopped")
