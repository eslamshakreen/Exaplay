"""Mock ExaPlay TCP server for testing.

Provides a simple asyncio TCP server that mimics ExaPlay's protocol
for testing purposes. Supports scripted responses and state simulation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple

# Simplified composition state for mock server
class MockComposition:
    """Represents a mock composition with basic state tracking."""
    
    def __init__(self, name: str, duration: float = 300.0) -> None:
        self.name = name
        self.state = 0  # 0=stopped, 1=playing, 2=paused
        self.time = 0.0
        self.frame = 0
        self.clip_index = -1
        self.duration = duration
        self.volume = 75  # Default volume
        
        # For cuelist compositions, simulate clips
        self.is_cuelist = "cuelist" in name.lower()
        if self.is_cuelist:
            self.clip_index = 1  # Cuelist clips are 1-based
    
    def get_status_csv(self) -> str:
        """Get status as CSV string matching ExaPlay format."""
        return f"{self.state},{self.time},{self.frame},{self.clip_index},{self.duration}"
    
    def play(self) -> str:
        """Start playback."""
        if self.state != 1:  # Not already playing
            self.state = 1
        return "OK"
    
    def pause(self) -> str:
        """Pause playback."""
        if self.state == 1:  # Currently playing
            self.state = 2
        return "OK"
    
    def stop(self) -> str:
        """Stop playback and reset position."""
        self.state = 0
        self.time = 0.0
        self.frame = 0
        return "OK"
    
    def set_cuetime(self, seconds: float) -> str:
        """Set playback time position."""
        if 0 <= seconds <= self.duration:
            self.time = seconds
            self.frame = int(seconds * 30)  # Assume 30fps
            return "OK"
        return "ERR"
    
    def set_cue(self, index: int) -> str:
        """Set cue/clip index."""
        if self.is_cuelist:
            # For cuelists, index is 1-based clip number
            if index >= 1:
                self.clip_index = index
                # Simulate jumping to clip start
                self.time = (index - 1) * 30.0  # Assume 30s clips
                self.frame = int(self.time * 30)
                return "OK"
            return "ERR"
        else:
            # For timelines, index is cue number (0-based)
            if index >= 0:
                self.clip_index = index
                # Simulate jumping to cue time
                self.time = index * 15.0  # Assume 15s cues
                self.frame = int(self.time * 30)
                return "OK"
            return "ERR"
    
    def set_volume(self, volume: int) -> str:
        """Set volume level."""
        if 0 <= volume <= 100:
            self.volume = volume
            return "OK"
        return "ERR"
    
    def get_volume(self) -> str:
        """Get current volume."""
        return str(self.volume)


class MockExaPlayServer:
    """Mock ExaPlay TCP server for testing.
    
    Simulates the ExaPlay TCP protocol with basic command handling
    and state management for testing the API client.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 17000) -> None:
        """Initialize mock server.
        
        Args:
            host: Server bind address
            port: Server bind port (default 17000 to avoid conflicts)
        """
        self.host = host
        self.port = port
        self.server: Optional[asyncio.Server] = None
        self.compositions: Dict[str, MockComposition] = {}
        self.version = "2.21.0.0"
        
        # Create some default compositions for testing
        self._create_default_compositions()
        
        # Configure logging for mock server
        self.logger = logging.getLogger("mock_exaplay")
        self.logger.setLevel(logging.DEBUG)
    
    def _create_default_compositions(self) -> None:
        """Create default test compositions."""
        self.compositions = {
            "comp1": MockComposition("comp1", duration=300.0),
            "timeline1": MockComposition("timeline1", duration=180.0),
            "cuelist1": MockComposition("cuelist1", duration=240.0),
            "showA": MockComposition("showA", duration=600.0),
        }
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle a client connection.
        
        Args:
            reader: Client stream reader
            writer: Client stream writer
        """
        client_addr = writer.get_extra_info('peername')
        self.logger.debug(f"Client connected: {client_addr}")
        
        try:
            while True:
                # Read command until CR
                data = await reader.readuntil(b"\r")
                if not data:
                    break
                
                command = data.decode("utf-8").rstrip("\r")
                self.logger.debug(f"Received command: {command}")
                
                # Process command and get response
                response = self._process_command(command)
                
                # Send response with CRLF
                response_bytes = f"{response}\r\n".encode("utf-8")
                writer.write(response_bytes)
                await writer.drain()
                
                self.logger.debug(f"Sent response: {response}")
                
        except asyncio.IncompleteReadError:
            self.logger.debug("Client disconnected")
        except Exception as e:
            self.logger.error(f"Error handling client: {e}")
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
    
    def _process_command(self, command: str) -> str:
        """Process a command and return the response.
        
        Args:
            command: Command string from client
            
        Returns:
            str: Response string to send back
        """
        parts = command.split(",")
        cmd = parts[0].strip().lower()
        
        try:
            if cmd == "get:ver":
                return self.version
            
            elif cmd == "play" and len(parts) >= 2:
                comp_name = parts[1].strip()
                comp = self._get_or_create_composition(comp_name)
                return comp.play()
            
            elif cmd == "pause" and len(parts) >= 2:
                comp_name = parts[1].strip()
                comp = self._get_or_create_composition(comp_name)
                return comp.pause()
            
            elif cmd == "stop" and len(parts) >= 2:
                comp_name = parts[1].strip()
                comp = self._get_or_create_composition(comp_name)
                return comp.stop()
            
            elif cmd == "get:status" and len(parts) >= 2:
                comp_name = parts[1].strip()
                comp = self._get_or_create_composition(comp_name)
                return comp.get_status_csv()
            
            elif cmd == "set:cuetime" and len(parts) >= 3:
                comp_name = parts[1].strip()
                try:
                    seconds = float(parts[2].strip())
                    comp = self._get_or_create_composition(comp_name)
                    return comp.set_cuetime(seconds)
                except ValueError:
                    return "ERR"
            
            elif cmd == "set:cue" and len(parts) >= 3:
                comp_name = parts[1].strip()
                try:
                    index = int(parts[2].strip())
                    comp = self._get_or_create_composition(comp_name)
                    return comp.set_cue(index)
                except ValueError:
                    return "ERR"
            
            elif cmd == "set:vol" and len(parts) >= 3:
                comp_name = parts[1].strip()
                try:
                    volume = int(parts[2].strip())
                    comp = self._get_or_create_composition(comp_name)
                    return comp.set_volume(volume)
                except ValueError:
                    return "ERR"
            
            elif cmd == "get:vol" and len(parts) >= 2:
                comp_name = parts[1].strip()
                comp = self._get_or_create_composition(comp_name)
                return comp.get_volume()
            
            else:
                self.logger.warning(f"Unknown command: {command}")
                return "ERR"
                
        except Exception as e:
            self.logger.error(f"Error processing command '{command}': {e}")
            return "ERR"
    
    def _get_or_create_composition(self, name: str) -> MockComposition:
        """Get existing composition or create a new one.
        
        Args:
            name: Composition name
            
        Returns:
            MockComposition: The composition object
        """
        if name not in self.compositions:
            self.compositions[name] = MockComposition(name)
            self.logger.info(f"Created new composition: {name}")
        return self.compositions[name]
    
    async def start(self) -> None:
        """Start the mock server."""
        if self.server is not None:
            self.logger.warning("Server already running")
            return
        
        self.logger.info(f"Starting mock ExaPlay server on {self.host}:{self.port}")
        
        self.server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        self.logger.info(f"Mock ExaPlay server started on {self.host}:{self.port}")
    
    async def stop(self) -> None:
        """Stop the mock server."""
        if self.server is None:
            return
        
        self.logger.info("Stopping mock ExaPlay server")
        
        self.server.close()
        await self.server.wait_closed()
        self.server = None
        
        self.logger.info("Mock ExaPlay server stopped")
    
    async def __aenter__(self) -> "MockExaPlayServer":
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()


# Utility functions for tests
async def run_mock_server_for_duration(duration: float, port: int = 17000) -> None:
    """Run mock server for a specific duration (useful for manual testing).
    
    Args:
        duration: How long to run the server in seconds
        port: Port to bind to
    """
    async with MockExaPlayServer("127.0.0.1", port) as server:
        print(f"Mock ExaPlay server running on port {port} for {duration}s")
        await asyncio.sleep(duration)
        print("Mock server shutting down")


if __name__ == "__main__":
    # Allow running the mock server standalone for manual testing
    import sys
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 17000
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else 300.0
    
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] %(levelname)s [%(name)s] %(message)s"
    )
    
    asyncio.run(run_mock_server_for_duration(duration, port))
