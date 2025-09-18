"""Admin API routes for ExaPlay raw command execution.

Implements the raw command endpoint for debugging and advanced usage.
Includes rate limiting and enhanced logging for security.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.deps import check_admin_rate_limit, get_authenticated_request
from app.exaplay.models import CommandRequest, ErrorResponse, GenericReply
from app.exaplay.tcp_client import (
    ExaPlayError,
    send_exaplay_command,
)
from app.logging import PerformanceTimer, get_logger, get_trace_id

# Import error mapping from control routes
from app.api.routes_control import map_exaplay_error_to_http

logger = get_logger(__name__)

router = APIRouter(
    prefix="/exaplay",
    tags=["Admin"],
    dependencies=get_authenticated_request()
)


@router.post(
    "/command",
    response_model=GenericReply,
    summary="Send a raw ExaPlay command (admin/debug)",
    description="Pass-through to TCP. Should be rate-limited and audited server-side.",
    dependencies=[Depends(check_admin_rate_limit)],
    responses={
        200: {
            "description": "Raw reply",
            "content": {
                "application/json": {
                    "examples": {
                        "play_command": {
                            "value": {"sent": "play,comp1", "reply": "OK"}
                        },
                        "status_command": {
                            "value": {"sent": "get:status,comp1", "reply": "1,15.65,939,2,300.0"}
                        }
                    }
                }
            }
        },
        400: {"description": "Bad request (validation failure)"},
        422: {"description": "ExaPlay returned ERR / cannot process command"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "Upstream (TCP) error or malformed response from ExaPlay"},
        504: {"description": "Upstream TCP timeout while talking to ExaPlay"}
    }
)
async def send_raw_command(
    request: CommandRequest,
    req: Request
) -> GenericReply:
    """Send a raw command directly to ExaPlay.
    
    This endpoint provides direct access to the ExaPlay TCP protocol
    for debugging, testing, and advanced use cases not covered by
    the specific API endpoints.
    
    SECURITY CONSIDERATIONS:
    - Rate limited to prevent abuse
    - All commands are logged with client information
    - Should only be used by authorized administrators
    - Consider disabling in production environments
    
    Args:
        request: Request containing the raw command string
        req: FastAPI request object for logging/rate limiting
        
    Returns:
        GenericReply: Command sent and ExaPlay's raw response
        
    Raises:
        HTTPException: For various error conditions including rate limits
    """
    command = request.raw.strip()
    
    # Validate command is not empty
    if not command:
        logger.warning(
            "Empty command rejected",
            client_ip=req.client.host if req.client else "unknown"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="Command cannot be empty",
                traceId=get_trace_id()
            ).model_dump()
        )
    
    # Enhanced logging for admin commands (security audit trail)
    logger.warning(  # Use warning level for admin commands to ensure visibility
        "Raw admin command executed",
        command_type=command.split(",")[0] if "," in command else command,
        command_length=len(command),
        client_ip=req.client.host if req.client else "unknown",
        user_agent=req.headers.get("User-Agent", "unknown"),
        # Don't log the full command to avoid potential sensitive data in logs
        # Log only the command type and length for security
    )
    
    try:
        with PerformanceTimer("raw_command", logger, command_type=command.split(",")[0]):
            reply = await send_exaplay_command(command)
        
        logger.info(
            "Raw command successful",
            command_type=command.split(",")[0],
            reply_length=len(reply),
            # Don't log full reply to avoid potential sensitive data
        )
        
        return GenericReply(sent=command, reply=reply)
        
    except ExaPlayError as e:
        logger.error(
            "Raw command failed",
            command_type=command.split(",")[0],
            error=str(e),
            client_ip=req.client.host if req.client else "unknown"
        )
        raise map_exaplay_error_to_http(e)
