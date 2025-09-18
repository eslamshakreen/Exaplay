"""Control API routes for ExaPlay playback commands.

Implements play, pause, and stop endpoints for composition control.
All routes require authentication and translate to ExaPlay TCP commands.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from typing_extensions import Annotated

from app.deps import get_authenticated_request
from app.exaplay.models import ErrorResponse, GenericReply
from app.exaplay.tcp_client import (
    ExaPlayConnectionError,
    ExaPlayError,
    ExaPlayProtocolError,
    ExaPlayTimeoutError,
    send_exaplay_command,
)
from app.logging import PerformanceTimer, get_logger, get_trace_id

logger = get_logger(__name__)

router = APIRouter(
    prefix="/compositions",
    tags=["Control"],
    dependencies=get_authenticated_request()
)


def map_exaplay_error_to_http(error: ExaPlayError) -> HTTPException:
    """Map ExaPlay errors to appropriate HTTP status codes.
    
    Args:
        error: ExaPlay-specific error
        
    Returns:
        HTTPException: Appropriate HTTP exception with error details
    """
    trace_id = get_trace_id()
    
    if isinstance(error, ExaPlayTimeoutError):
        return HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=ErrorResponse(
                error="TCP timeout",
                command=error.command,
                traceId=trace_id
            ).model_dump()
        )
    elif isinstance(error, ExaPlayConnectionError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=ErrorResponse(
                error=f"TCP error: {str(error)}",
                command=error.command,
                traceId=trace_id
            ).model_dump()
        )
    elif isinstance(error, ExaPlayProtocolError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ErrorResponse(
                error=str(error),
                command=error.command,
                traceId=trace_id
            ).model_dump()
        )
    else:
        # Generic ExaPlay error
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=ErrorResponse(
                error=f"ExaPlay error: {str(error)}",
                command=error.command,
                traceId=trace_id
            ).model_dump()
        )


@router.post(
    "/{name}/play",
    response_model=GenericReply,
    summary="Play a composition (timeline or cuelist)",
    description="Sends `play,{name}` command to ExaPlay server",
    responses={
        200: {
            "description": "ExaPlay acknowledged",
            "content": {
                "application/json": {
                    "example": {"sent": "play,comp1", "reply": "OK"}
                }
            }
        },
        422: {"description": "ExaPlay returned ERR / cannot process command"},
        502: {"description": "Upstream (TCP) error or malformed response from ExaPlay"},
        504: {"description": "Upstream TCP timeout while talking to ExaPlay"}
    }
)
async def play_composition(
    name: Annotated[str, Path(description="ExaPlay composition name (timeline or cuelist)", min_length=1)]
) -> GenericReply:
    """Play a composition (timeline or cuelist).
    
    Sends the `play,{name}` command to ExaPlay and returns the response.
    The composition can be either a timeline or cuelist - ExaPlay will
    determine the appropriate playback behavior.
    
    Args:
        name: Name of the composition to play
        
    Returns:
        GenericReply: Command sent and ExaPlay's response
        
    Raises:
        HTTPException: For various error conditions (timeout, connection, protocol)
    """
    command = f"play,{name}"
    
    try:
        with PerformanceTimer("play_composition", logger, composition=name):
            reply = await send_exaplay_command(command)
        
        logger.info(
            "Play command successful",
            composition=name,
            reply=reply
        )
        
        return GenericReply(sent=command, reply=reply)
        
    except ExaPlayError as e:
        logger.error(
            "Play command failed",
            composition=name,
            command=command,
            error=str(e)
        )
        raise map_exaplay_error_to_http(e)


@router.post(
    "/{name}/pause",
    response_model=GenericReply,
    summary="Pause a composition",
    description="Sends `pause,{name}` command to ExaPlay server",
    responses={
        200: {"description": "ExaPlay acknowledged"},
        422: {"description": "ExaPlay returned ERR / cannot process command"},
        502: {"description": "Upstream (TCP) error or malformed response from ExaPlay"},
        504: {"description": "Upstream TCP timeout while talking to ExaPlay"}
    }
)
async def pause_composition(
    name: Annotated[str, Path(description="ExaPlay composition name (timeline or cuelist)", min_length=1)]
) -> GenericReply:
    """Pause a composition.
    
    Sends the `pause,{name}` command to ExaPlay. This will pause playback
    at the current position, allowing it to be resumed later.
    
    Args:
        name: Name of the composition to pause
        
    Returns:
        GenericReply: Command sent and ExaPlay's response
        
    Raises:
        HTTPException: For various error conditions (timeout, connection, protocol)
    """
    command = f"pause,{name}"
    
    try:
        with PerformanceTimer("pause_composition", logger, composition=name):
            reply = await send_exaplay_command(command)
        
        logger.info(
            "Pause command successful",
            composition=name,
            reply=reply
        )
        
        return GenericReply(sent=command, reply=reply)
        
    except ExaPlayError as e:
        logger.error(
            "Pause command failed",
            composition=name,
            command=command,
            error=str(e)
        )
        raise map_exaplay_error_to_http(e)


@router.post(
    "/{name}/stop",
    response_model=GenericReply,
    summary="Stop a composition",
    description="Sends `stop,{name}` command to ExaPlay server",
    responses={
        200: {"description": "ExaPlay acknowledged"},
        422: {"description": "ExaPlay returned ERR / cannot process command"},
        502: {"description": "Upstream (TCP) error or malformed response from ExaPlay"},
        504: {"description": "Upstream TCP timeout while talking to ExaPlay"}
    }
)
async def stop_composition(
    name: Annotated[str, Path(description="ExaPlay composition name (timeline or cuelist)", min_length=1)]
) -> GenericReply:
    """Stop a composition.
    
    Sends the `stop,{name}` command to ExaPlay. This will stop playback
    and reset the position to the beginning.
    
    Args:
        name: Name of the composition to stop
        
    Returns:
        GenericReply: Command sent and ExaPlay's response
        
    Raises:
        HTTPException: For various error conditions (timeout, connection, protocol)
    """
    command = f"stop,{name}"
    
    try:
        with PerformanceTimer("stop_composition", logger, composition=name):
            reply = await send_exaplay_command(command)
        
        logger.info(
            "Stop command successful",
            composition=name,
            reply=reply
        )
        
        return GenericReply(sent=command, reply=reply)
        
    except ExaPlayError as e:
        logger.error(
            "Stop command failed",
            composition=name,
            command=command,
            error=str(e)
        )
        raise map_exaplay_error_to_http(e)
