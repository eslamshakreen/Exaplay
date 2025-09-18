"""Volume API routes for ExaPlay volume control.

Implements get and set volume endpoints for composition audio control.
All routes require authentication and translate to ExaPlay TCP commands.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from typing_extensions import Annotated

from app.deps import get_authenticated_request
from app.exaplay.mapper import ExaPlayMappingError, parse_volume_response
from app.exaplay.models import ErrorResponse, GenericReply, VolumeResponse, VolumeSetRequest
from app.exaplay.tcp_client import (
    ExaPlayError,
    send_exaplay_command,
)
from app.logging import PerformanceTimer, get_logger, get_trace_id

# Import error mapping from control routes
from app.api.routes_control import map_exaplay_error_to_http

logger = get_logger(__name__)

router = APIRouter(
    prefix="/compositions",
    tags=["Volume"],
    dependencies=get_authenticated_request()
)


@router.get(
    "/{name}/volume",
    response_model=VolumeResponse,
    summary="Get composition volume",
    description="Sends `get:vol,{name}` command to ExaPlay server and returns normalized volume value",
    responses={
        200: {
            "description": "Current volume value",
            "content": {
                "application/json": {
                    "example": {"value": 60}
                }
            }
        },
        502: {"description": "Upstream (TCP) error or malformed response from ExaPlay"},
        504: {"description": "Upstream TCP timeout while talking to ExaPlay"}
    }
)
async def get_volume(
    name: Annotated[str, Path(description="ExaPlay composition name (timeline or cuelist)", min_length=1)]
) -> VolumeResponse:
    """Get the current volume level for a composition.
    
    Retrieves the current volume setting from ExaPlay and returns
    it as a normalized integer value between 0 and 100.
    
    Args:
        name: Name of the composition
        
    Returns:
        VolumeResponse: Current volume level (0-100)
        
    Raises:
        HTTPException: For various error conditions (timeout, connection, protocol)
    """
    command = f"get:vol,{name}"
    
    try:
        with PerformanceTimer("get_volume", logger, composition=name):
            reply = await send_exaplay_command(command)
        
        # Parse the volume response
        try:
            volume_value = parse_volume_response(reply)
        except ExaPlayMappingError as e:
            logger.error(
                "Failed to parse volume response",
                composition=name,
                reply=reply,
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=ErrorResponse(
                    error=f"Malformed volume response: {str(e)}",
                    command=command,
                    traceId=get_trace_id()
                ).model_dump()
            )
        
        logger.info(
            "Get volume successful",
            composition=name,
            volume=volume_value,
            reply=reply
        )
        
        return VolumeResponse(value=volume_value)
        
    except ExaPlayError as e:
        logger.error(
            "Get volume failed",
            composition=name,
            command=command,
            error=str(e)
        )
        raise map_exaplay_error_to_http(e)


@router.post(
    "/{name}/volume",
    response_model=GenericReply,
    summary="Set composition volume (0..100)",
    description="Sends `set:vol,{name},{value}` command to ExaPlay server",
    responses={
        200: {"description": "ExaPlay acknowledged"},
        422: {"description": "ExaPlay returned ERR / cannot process command"},
        502: {"description": "Upstream (TCP) error or malformed response from ExaPlay"},
        504: {"description": "Upstream TCP timeout while talking to ExaPlay"}
    }
)
async def set_volume(
    name: Annotated[str, Path(description="ExaPlay composition name (timeline or cuelist)", min_length=1)],
    request: VolumeSetRequest
) -> GenericReply:
    """Set the volume level for a composition.
    
    Sets the volume to the specified level between 0 and 100.
    The change takes effect immediately during playback.
    
    Args:
        name: Name of the composition
        request: Request containing the target volume level (0-100)
        
    Returns:
        GenericReply: Command sent and ExaPlay's response
        
    Raises:
        HTTPException: For various error conditions (timeout, connection, protocol)
    """
    command = f"set:vol,{name},{request.value}"
    
    try:
        with PerformanceTimer("set_volume", logger, composition=name, volume=request.value):
            reply = await send_exaplay_command(command)
        
        logger.info(
            "Set volume successful",
            composition=name,
            volume=request.value,
            reply=reply
        )
        
        return GenericReply(sent=command, reply=reply)
        
    except ExaPlayError as e:
        logger.error(
            "Set volume failed",
            composition=name,
            volume=request.value,
            command=command,
            error=str(e)
        )
        raise map_exaplay_error_to_http(e)
