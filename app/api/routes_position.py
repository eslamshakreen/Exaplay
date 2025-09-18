"""Position API routes for ExaPlay cuetime and cue control.

Implements cuetime (seek) and cue (jump to cue/clip) endpoints.
All routes require authentication and translate to ExaPlay TCP commands.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from typing_extensions import Annotated

from app.deps import get_authenticated_request
from app.exaplay.models import CueSetRequest, CuetimeSetRequest, ErrorResponse, GenericReply
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
    tags=["Positioning"],
    dependencies=get_authenticated_request()
)


@router.post(
    "/{name}/cuetime",
    response_model=GenericReply,
    summary="Seek to a time (seconds) for timeline compositions",
    description="Sends `set:cuetime,{name},{seconds}` command to ExaPlay server",
    responses={
        200: {"description": "ExaPlay acknowledged"},
        422: {"description": "ExaPlay returned ERR / cannot process command"},
        502: {"description": "Upstream (TCP) error or malformed response from ExaPlay"},
        504: {"description": "Upstream TCP timeout while talking to ExaPlay"}
    }
)
async def set_cuetime(
    name: Annotated[str, Path(description="ExaPlay composition name (timeline or cuelist)", min_length=1)],
    request: CuetimeSetRequest
) -> GenericReply:
    """Seek to a specific time position in seconds.
    
    This command is primarily intended for timeline compositions.
    For cuelist compositions, the behavior may vary depending on
    the ExaPlay configuration and cuelist structure.
    
    Args:
        name: Name of the composition
        request: Request containing the target time in seconds
        
    Returns:
        GenericReply: Command sent and ExaPlay's response
        
    Raises:
        HTTPException: For various error conditions (timeout, connection, protocol)
    """
    command = f"set:cuetime,{name},{request.seconds}"
    
    try:
        with PerformanceTimer("set_cuetime", logger, composition=name, seconds=request.seconds):
            reply = await send_exaplay_command(command)
        
        logger.info(
            "Cuetime command successful",
            composition=name,
            seconds=request.seconds,
            reply=reply
        )
        
        return GenericReply(sent=command, reply=reply)
        
    except ExaPlayError as e:
        logger.error(
            "Cuetime command failed",
            composition=name,
            seconds=request.seconds,
            command=command,
            error=str(e)
        )
        raise map_exaplay_error_to_http(e)


@router.post(
    "/{name}/cue",
    response_model=GenericReply,
    summary="Jump to a cue (timeline) or clip (cuelist)",
    description="Sends `set:cue,{name},{index}` command to ExaPlay server. Index is 1-based for cuelists.",
    responses={
        200: {"description": "ExaPlay acknowledged"},
        422: {"description": "ExaPlay returned ERR / cannot process command"},
        502: {"description": "Upstream (TCP) error or malformed response from ExaPlay"},
        504: {"description": "Upstream TCP timeout while talking to ExaPlay"}
    }
)
async def set_cue(
    name: Annotated[str, Path(description="ExaPlay composition name (timeline or cuelist)", min_length=1)],
    request: CueSetRequest
) -> GenericReply:
    """Jump to a specific cue or clip index.
    
    The behavior depends on the composition type:
    - For timeline compositions: Jumps to the specified cue index
    - For cuelist compositions: Jumps to the specified clip (1-based index)
    
    Note: Cuelist clip indices are 1-based, meaning the first clip is index 1.
    
    Args:
        name: Name of the composition
        request: Request containing the target cue/clip index
        
    Returns:
        GenericReply: Command sent and ExaPlay's response
        
    Raises:
        HTTPException: For various error conditions (timeout, connection, protocol)
    """
    command = f"set:cue,{name},{request.index}"
    
    try:
        with PerformanceTimer("set_cue", logger, composition=name, index=request.index):
            reply = await send_exaplay_command(command)
        
        logger.info(
            "Cue command successful",
            composition=name,
            index=request.index,
            reply=reply
        )
        
        return GenericReply(sent=command, reply=reply)
        
    except ExaPlayError as e:
        logger.error(
            "Cue command failed",
            composition=name,
            index=request.index,
            command=command,
            error=str(e)
        )
        raise map_exaplay_error_to_http(e)
