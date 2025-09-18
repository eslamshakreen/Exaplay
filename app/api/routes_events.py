"""Events API routes for ExaPlay real-time status streaming.

Implements Server-Sent Events (SSE) endpoint for live status updates
when OSC is enabled. Provides real-time composition status without polling.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

from app.deps import get_authenticated_request
from app.exaplay.osc_listener import osc_broadcaster
from app.logging import get_logger
from app.settings import settings

logger = get_logger(__name__)

router = APIRouter(
    prefix="/events",
    tags=["Events"],
    dependencies=get_authenticated_request()
)


@router.get(
    "/status",
    summary="Live status stream (SSE)",
    description="""Optional Server-Sent Events (SSE) stream of ExaPlay status updates.
    
If enabled, the backend ingests ExaPlay OSC OUT and emits JSON events per composition.
Returns 503 if OSC is not enabled in configuration.""",
    responses={
        200: {
            "description": "text/event-stream emitting JSON status objects",
            "headers": {
                "Content-Type": {
                    "description": "text/event-stream",
                    "schema": {"type": "string", "example": "text/event-stream"}
                }
            },
            "content": {
                "text/event-stream": {
                    "example": """event: status
data: {"composition":"comp1","status":1,"cuetime":15.6,"cueframe":939}

event: cuetime  
data: {"composition":"comp1","status":1,"cuetime":16.1,"cueframe":966}

: keepalive

"""
                }
            }
        },
        503: {
            "description": "OSC streaming not enabled or not available"
        }
    }
)
async def status_stream(request: Request) -> StreamingResponse:
    """Stream live ExaPlay status updates via Server-Sent Events.
    
    This endpoint provides a continuous stream of real-time status updates
    from ExaPlay when OSC is enabled. Clients can connect and receive
    live updates without polling.
    
    The stream includes:
    - status events: Overall playback state changes
    - cuetime events: Time position updates  
    - cueframe events: Frame position updates
    - keepalive comments: Periodic heartbeat to maintain connection
    
    Args:
        request: FastAPI request object for client management
        
    Returns:
        StreamingResponse: SSE stream with real-time events
        
    Raises:
        HTTPException: 503 if OSC is not enabled
    """
    # Check if OSC is enabled
    if not settings.exaplay_osc_enable:
        logger.info(
            "SSE stream requested but OSC disabled",
            client_ip=request.client.host if request.client else "unknown"
        )
        return StreamingResponse(
            content=_disabled_stream(),
            media_type="text/event-stream",
            status_code=503,
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
    
    # Register client with broadcaster
    client_queue = osc_broadcaster.add_client()
    
    logger.info(
        "SSE client connected",
        client_ip=request.client.host if request.client else "unknown",
        total_clients=len(osc_broadcaster._clients)
    )
    
    async def event_stream() -> AsyncGenerator[str, None]:
        """Generate SSE events for the connected client."""
        try:
            # Send initial connection event
            yield "event: connected\ndata: {\"message\":\"Connected to ExaPlay status stream\"}\n\n"
            
            # Stream events from the broadcaster
            async for event_data in osc_broadcaster.get_client_events(client_queue):
                yield event_data
                
        except Exception as e:
            logger.error(
                "Error in SSE stream",
                client_ip=request.client.host if request.client else "unknown",
                error=str(e)
            )
            yield f"event: error\ndata: {{\"error\":\"Stream error: {str(e)}\"}}\n\n"
        finally:
            logger.info(
                "SSE client disconnected",
                client_ip=request.client.host if request.client else "unknown"
            )
    
    return StreamingResponse(
        content=event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


async def _disabled_stream() -> AsyncGenerator[str, None]:
    """Generate a stream indicating OSC is disabled."""
    yield "event: error\n"
    yield "data: {\"error\":\"OSC streaming not enabled. Set EXAPLAY_OSC_ENABLE=true to enable.\"}\n\n"
    
    # Send periodic keepalive to maintain connection
    import asyncio
    for i in range(5):  # Send a few keepalives then close
        await asyncio.sleep(10)
        yield ": OSC disabled\n\n"
    
    yield "event: close\n"
    yield "data: {\"message\":\"Stream closed - OSC not enabled\"}\n\n"
