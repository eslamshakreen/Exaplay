"""Robust async TCP client for ExaPlay communication.

Implements the ExaPlay TCP protocol with proper CR/CRLF handling,
timeouts, exponential backoff retries, and comprehensive error handling.

Protocol Details:
- Send commands as UTF-8 text lines terminated with CR (\r)
- Receive replies as single lines terminated with CRLF (\r\n)
- Commands and replies are comma-separated values
"""

import asyncio
import socket
from typing import Optional, Tuple

from app.logging import PerformanceTimer, get_logger
from app.settings import settings

logger = get_logger(__name__)


class ExaPlayError(Exception):
    """Base exception for ExaPlay-related errors."""
    
    def __init__(self, message: str, command: Optional[str] = None) -> None:
        super().__init__(message)
        self.command = command


class ExaPlayTimeoutError(ExaPlayError):
    """Raised when TCP operations timeout."""
    pass


class ExaPlayConnectionError(ExaPlayError):
    """Raised when TCP connection fails."""
    pass


class ExaPlayProtocolError(ExaPlayError):
    """Raised when ExaPlay returns an error or malformed response."""
    pass


class ExaPlayTCPClient:
    """Async TCP client for ExaPlay communication.
    
    Handles connection management, protocol framing, retries, and error mapping.
    Designed to be used as a singleton or short-lived instance per request.
    
    Example:
        client = ExaPlayTCPClient()
        try:
            reply = await client.send_command("play,comp1")
            logger.info("ExaPlay replied", reply=reply)
        except ExaPlayError as e:
            logger.error("Command failed", error=str(e), command=e.command)
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_backoff: Optional[float] = None
    ) -> None:
        """Initialize TCP client with connection parameters.
        
        Args:
            host: ExaPlay server hostname/IP (defaults to settings)
            port: ExaPlay TCP port (defaults to settings)
            timeout: Operation timeout in seconds (defaults to settings)
            max_retries: Maximum retry attempts (defaults to settings)
            retry_backoff: Initial backoff delay for retries (defaults to settings)
        """
        self.host = host or settings.exaplay_host
        self.port = port or settings.exaplay_tcp_port
        self.timeout = timeout or settings.tcp_timeout
        self.max_retries = max_retries or settings.tcp_max_retries
        self.retry_backoff = retry_backoff or settings.tcp_retry_backoff
        
        # Connection state
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connection_lock = asyncio.Lock()
    
    async def _connect(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Establish TCP connection to ExaPlay server.
        
        Returns:
            Tuple of (reader, writer) streams.
            
        Raises:
            ExaPlayConnectionError: If connection fails.
            ExaPlayTimeoutError: If connection times out.
        """
        try:
            logger.debug(
                "Connecting to ExaPlay",
                host=self.host,
                port=self.port,
                timeout=self.timeout
            )
            
            # Use asyncio.wait_for to enforce timeout
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout
            )
            
            logger.debug("Connected to ExaPlay successfully")
            return reader, writer
            
        except asyncio.TimeoutError as e:
            raise ExaPlayTimeoutError(
                f"Connection timeout after {self.timeout}s"
            ) from e
        except (OSError, socket.error) as e:
            raise ExaPlayConnectionError(
                f"Failed to connect to {self.host}:{self.port}: {e}"
            ) from e
    
    async def _send_command_raw(self, command: str) -> str:
        """Send a single command and receive reply without retries.
        
        Args:
            command: Raw command string (without CR terminator)
            
        Returns:
            str: Reply from ExaPlay (without CRLF terminator)
            
        Raises:
            ExaPlayTimeoutError: If operation times out.
            ExaPlayConnectionError: If connection fails.
            ExaPlayProtocolError: If reply is malformed.
        """
        reader, writer = await self._connect()
        
        try:
            # Send command with CR terminator
            command_bytes = f"{command}\r".encode("utf-8")
            logger.debug("Sending command", command=command, bytes_len=len(command_bytes))
            
            writer.write(command_bytes)
            await asyncio.wait_for(writer.drain(), timeout=self.timeout)
            
            # Read reply until CRLF
            reply_bytes = await asyncio.wait_for(
                reader.readuntil(b"\r\n"),
                timeout=self.timeout
            )
            
            # Decode and strip CRLF terminator
            reply = reply_bytes.decode("utf-8").rstrip("\r\n")
            logger.debug("Received reply", reply=reply, bytes_len=len(reply_bytes))
            
            return reply
            
        except asyncio.TimeoutError as e:
            raise ExaPlayTimeoutError(
                f"Command timeout after {self.timeout}s",
                command=command
            ) from e
        except (OSError, socket.error) as e:
            raise ExaPlayConnectionError(
                f"Connection error during command: {e}",
                command=command
            ) from e
        except UnicodeDecodeError as e:
            raise ExaPlayProtocolError(
                f"Invalid UTF-8 in reply: {e}",
                command=command
            ) from e
        finally:
            # Always close connection after single command
            writer.close()
            try:
                await asyncio.wait_for(writer.wait_closed(), timeout=1.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for connection to close")
            except Exception as e:
                logger.warning("Error closing connection", error=str(e))
    
    async def send_command(self, command: str) -> str:
        """Send command to ExaPlay with retry logic and error handling.
        
        Args:
            command: Raw command string (without CR terminator)
            
        Returns:
            str: Reply from ExaPlay, or raises exception
            
        Raises:
            ExaPlayTimeoutError: If all retry attempts timeout.
            ExaPlayConnectionError: If connection consistently fails.
            ExaPlayProtocolError: If ExaPlay returns ERR or malformed response.
        """
        async with self._connection_lock:
            last_exception: Optional[Exception] = None
            
            # Attempt command with exponential backoff retry
            for attempt in range(self.max_retries + 1):
                try:
                    with PerformanceTimer(
                        "tcp_command",
                        logger,
                        command=command,
                        attempt=attempt + 1
                    ):
                        reply = await self._send_command_raw(command)
                    
                    # Check for ExaPlay error response
                    if reply.startswith("ERR"):
                        raise ExaPlayProtocolError(
                            f"ExaPlay returned error: {reply}",
                            command=command
                        )
                    
                    # Log successful command
                    logger.info(
                        "Command completed successfully",
                        command=command,
                        reply=reply,
                        attempt=attempt + 1
                    )
                    
                    return reply
                    
                except (ExaPlayTimeoutError, ExaPlayConnectionError) as e:
                    last_exception = e
                    
                    if attempt < self.max_retries:
                        # Calculate backoff delay with exponential increase
                        delay = self.retry_backoff * (2 ** attempt)
                        
                        logger.warning(
                            "Command failed, retrying",
                            command=command,
                            attempt=attempt + 1,
                            max_retries=self.max_retries,
                            retry_delay=delay,
                            error=str(e)
                        )
                        
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            "Command failed after all retries",
                            command=command,
                            attempts=attempt + 1,
                            error=str(e)
                        )
                        break
                
                except ExaPlayProtocolError:
                    # Protocol errors (like ERR responses) should not be retried
                    raise
            
            # Re-raise the last exception if all retries failed
            if last_exception:
                raise last_exception
            
            # This should not happen, but provide a fallback
            raise ExaPlayConnectionError(
                "Unexpected error: no exception but no success",
                command=command
            )
    
    async def close(self) -> None:
        """Close any existing connections.
        
        This method is idempotent and safe to call multiple times.
        """
        if self._writer and not self._writer.is_closing():
            logger.debug("Closing TCP connection")
            self._writer.close()
            try:
                await asyncio.wait_for(self._writer.wait_closed(), timeout=1.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for connection to close")
            except Exception as e:
                logger.warning("Error closing connection", error=str(e))
            finally:
                self._writer = None
                self._reader = None
    
    async def __aenter__(self) -> "ExaPlayTCPClient":
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()


# Convenience functions for common operations
async def send_exaplay_command(command: str) -> str:
    """Send a single command to ExaPlay using default settings.
    
    Convenience function that creates a client, sends the command,
    and cleans up automatically.
    
    Args:
        command: Raw command string
        
    Returns:
        str: Reply from ExaPlay
        
    Raises:
        ExaPlayError: For any communication or protocol errors
    """
    async with ExaPlayTCPClient() as client:
        return await client.send_command(command)


async def test_exaplay_connection() -> bool:
    """Test if ExaPlay server is reachable and responding.
    
    Returns:
        bool: True if connection test succeeds, False otherwise
    """
    try:
        reply = await send_exaplay_command("get:ver")
        logger.info("Connection test successful", version=reply)
        return True
    except ExaPlayError as e:
        logger.warning("Connection test failed", error=str(e))
        return False
