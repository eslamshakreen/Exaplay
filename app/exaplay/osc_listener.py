"""OSC listener for ExaPlay real-time status updates.

Provides optional functionality to listen for OSC messages from ExaPlay
and broadcast them to connected clients via Server-Sent Events (SSE).
This enables real-time status updates without polling.

Feature is controlled by EXAPLAY_OSC_ENABLE setting.
"""

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional, Set

try:
    from pythonosc import dispatcher
    from pythonosc import osc_server
    OSC_AVAILABLE = True
except ImportError:
    # OSC not available, create dummy classes
    OSC_AVAILABLE = False
    
    class dispatcher:
        class Dispatcher:
            def map(self, *args, **kwargs): pass
    
    class osc_server:
        class BlockingOSCUDPServer:
            def __init__(self, *args, **kwargs): pass
            def serve_forever(self): pass
            def shutdown(self): pass

from app.exaplay.models import SSEStatusEvent
from app.logging import get_logger
from app.settings import settings

logger = get_logger(__name__)


class OSCEventBroadcaster:
    """Manages OSC message reception and broadcasting to SSE clients.
    
    Listens for ExaPlay OSC messages matching the configured prefix
    and converts them to JSON events for streaming to web clients.
    """
    
    def __init__(self) -> None:
        """Initialize the OSC event broadcaster."""
        self._server: Optional[BlockingOSCUDPServer] = None
        self._server_task: Optional[asyncio.Task] = None
        self._clients: Set[asyncio.Queue] = set()
        self._running = False
        
        # OSC message dispatcher
        self._dispatcher = dispatcher.Dispatcher()
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Set up OSC message handlers for ExaPlay events."""
        if not OSC_AVAILABLE:
            return
            
        # Map OSC addresses to handler functions
        osc_prefix = f"/{settings.exaplay_osc_prefix}"
        
        # Handle status updates: /exaplay/status/[composition]
        self._dispatcher.map(f"{osc_prefix}/status/*", self._handle_status_update)
        
        # Handle cuetime updates: /exaplay/cuetime/[composition] 
        self._dispatcher.map(f"{osc_prefix}/cuetime/*", self._handle_cuetime_update)
        
        # Handle cueframe updates: /exaplay/cueframe/[composition]
        self._dispatcher.map(f"{osc_prefix}/cueframe/*", self._handle_cueframe_update)
        
        # Catch-all handler for debugging
        self._dispatcher.map("/*", self._handle_debug_message)
        
        logger.info(
            "OSC handlers configured",
            prefix=osc_prefix,
            handlers=["status", "cuetime", "cueframe"]
        )
    
    def _handle_status_update(self, address: str, *args: Any) -> None:
        """Handle OSC status update messages.
        
        Args:
            address: OSC address (e.g., /exaplay/status/comp1)
            *args: OSC arguments (typically status value)
        """
        try:
            # Extract composition name from address
            parts = address.split("/")
            if len(parts) < 4:
                logger.warning("Invalid status address format", address=address)
                return
            
            composition = parts[3]  # /exaplay/status/[composition]
            
            if not args:
                logger.warning("Status update missing arguments", address=address)
                return
            
            status_value = args[0]
            
            logger.debug(
                "Received status update",
                composition=composition,
                status=status_value,
                address=address
            )
            
            # Create status event (simplified format for now)
            event_data = {
                "composition": composition,
                "status": int(status_value),
                "cuetime": 0.0,  # Will be updated by separate cuetime messages
                "cueframe": 0    # Will be updated by separate cueframe messages
            }
            
            # Broadcast to all connected clients
            self._broadcast_event("status", event_data)
            
        except Exception as e:
            logger.error(
                "Error handling status update",
                address=address,
                args=args,
                error=str(e)
            )
    
    def _handle_cuetime_update(self, address: str, *args: Any) -> None:
        """Handle OSC cuetime update messages.
        
        Args:
            address: OSC address (e.g., /exaplay/cuetime/comp1)
            *args: OSC arguments (typically time value)
        """
        try:
            parts = address.split("/")
            if len(parts) < 4:
                logger.warning("Invalid cuetime address format", address=address)
                return
            
            composition = parts[3]
            
            if not args:
                logger.warning("Cuetime update missing arguments", address=address)
                return
            
            cuetime_value = float(args[0])
            
            logger.debug(
                "Received cuetime update",
                composition=composition,
                cuetime=cuetime_value,
                address=address
            )
            
            # For cuetime updates, we might want to combine with current status
            # For now, send a simplified event
            event_data = {
                "composition": composition,
                "status": 1,  # Assume playing when time updates
                "cuetime": cuetime_value,
                "cueframe": 0
            }
            
            self._broadcast_event("cuetime", event_data)
            
        except Exception as e:
            logger.error(
                "Error handling cuetime update",
                address=address,
                args=args,
                error=str(e)
            )
    
    def _handle_cueframe_update(self, address: str, *args: Any) -> None:
        """Handle OSC cueframe update messages.
        
        Args:
            address: OSC address (e.g., /exaplay/cueframe/comp1)
            *args: OSC arguments (typically frame value)
        """
        try:
            parts = address.split("/")
            if len(parts) < 4:
                logger.warning("Invalid cueframe address format", address=address)
                return
            
            composition = parts[3]
            
            if not args:
                logger.warning("Cueframe update missing arguments", address=address)
                return
            
            cueframe_value = int(args[0])
            
            logger.debug(
                "Received cueframe update",
                composition=composition,
                cueframe=cueframe_value,
                address=address
            )
            
            event_data = {
                "composition": composition,
                "status": 1,  # Assume playing when frame updates
                "cuetime": 0.0,
                "cueframe": cueframe_value
            }
            
            self._broadcast_event("cueframe", event_data)
            
        except Exception as e:
            logger.error(
                "Error handling cueframe update",
                address=address,
                args=args,
                error=str(e)
            )
    
    def _handle_debug_message(self, address: str, *args: Any) -> None:
        """Debug handler for all OSC messages.
        
        Args:
            address: OSC address
            *args: OSC arguments
        """
        # Only log if it matches our prefix (to avoid spam)
        if address.startswith(f"/{settings.exaplay_osc_prefix}"):
            logger.debug(
                "OSC message received",
                address=address,
                args=args,
                arg_count=len(args)
            )
    
    def _broadcast_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast event to all connected SSE clients.
        
        Args:
            event_type: Type of event (status, cuetime, cueframe)
            data: Event data dictionary
        """
        if not self._clients:
            logger.debug("No SSE clients connected, skipping broadcast")
            return
        
        # Create SSE-formatted message
        sse_data = json.dumps(data, ensure_ascii=False)
        sse_message = f"event: {event_type}\ndata: {sse_data}\n\n"
        
        # Send to all connected clients
        disconnected_clients = set()
        
        for client_queue in self._clients:
            try:
                # Non-blocking put - if queue is full, skip this client
                client_queue.put_nowait(sse_message)
            except asyncio.QueueFull:
                logger.warning("Client queue full, dropping message")
            except Exception as e:
                logger.warning("Error sending to client, removing", error=str(e))
                disconnected_clients.add(client_queue)
        
        # Clean up disconnected clients
        self._clients -= disconnected_clients
        
        logger.debug(
            "Event broadcasted",
            event_type=event_type,
            clients=len(self._clients),
            data=data
        )
    
    async def start(self) -> None:
        """Start the OSC listener server."""
        if self._running:
            logger.warning("OSC listener already running")
            return
        
        if not settings.exaplay_osc_enable:
            logger.info("OSC listener disabled by configuration")
            return
            
        if not OSC_AVAILABLE:
            logger.warning("OSC library not available, cannot start OSC listener")
            return
        
        try:
            logger.info(
                "Starting OSC listener",
                host=settings.osc_host,
                port=settings.osc_port,
                prefix=settings.exaplay_osc_prefix
            )
            
            # Create OSC server
            self._server = osc_server.BlockingOSCUDPServer(
                (settings.osc_host, settings.osc_port),
                self._dispatcher
            )
            
            # Start server in background task
            self._server_task = asyncio.create_task(self._run_server())
            self._running = True
            
            logger.info("OSC listener started successfully")
            
        except Exception as e:
            logger.error("Failed to start OSC listener", error=str(e))
            self._running = False
            raise
    
    async def _run_server(self) -> None:
        """Run the OSC server in a background task."""
        try:
            if self._server:
                # Run server in executor to avoid blocking the event loop
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self._server.serve_forever)
        except Exception as e:
            logger.error("OSC server error", error=str(e))
        finally:
            self._running = False
    
    async def stop(self) -> None:
        """Stop the OSC listener server."""
        if not self._running:
            return
        
        logger.info("Stopping OSC listener")
        
        try:
            if self._server:
                self._server.shutdown()
            
            if self._server_task:
                self._server_task.cancel()
                try:
                    await self._server_task
                except asyncio.CancelledError:
                    pass
            
            # Clear all client connections
            self._clients.clear()
            
            self._running = False
            logger.info("OSC listener stopped")
            
        except Exception as e:
            logger.error("Error stopping OSC listener", error=str(e))
    
    def add_client(self) -> asyncio.Queue:
        """Add a new SSE client for event streaming.
        
        Returns:
            asyncio.Queue: Queue for sending events to the client
        """
        client_queue = asyncio.Queue(maxsize=100)  # Limit queue size
        self._clients.add(client_queue)
        
        logger.debug(
            "SSE client connected",
            total_clients=len(self._clients)
        )
        
        return client_queue
    
    def remove_client(self, client_queue: asyncio.Queue) -> None:
        """Remove an SSE client.
        
        Args:
            client_queue: Client queue to remove
        """
        self._clients.discard(client_queue)
        
        logger.debug(
            "SSE client disconnected",
            total_clients=len(self._clients)
        )
    
    async def get_client_events(self, client_queue: asyncio.Queue) -> AsyncGenerator[str, None]:
        """Generate SSE events for a specific client.
        
        Args:
            client_queue: Client's event queue
            
        Yields:
            str: SSE-formatted event messages
        """
        try:
            while True:
                # Wait for next event with timeout
                try:
                    event_message = await asyncio.wait_for(
                        client_queue.get(),
                        timeout=30.0  # Send keepalive every 30 seconds
                    )
                    yield event_message
                except asyncio.TimeoutError:
                    # Send keepalive comment
                    yield ": keepalive\n\n"
                    
        except asyncio.CancelledError:
            logger.debug("Client event stream cancelled")
            raise
        except Exception as e:
            logger.error("Error in client event stream", error=str(e))
        finally:
            self.remove_client(client_queue)


# Global broadcaster instance
osc_broadcaster = OSCEventBroadcaster()
