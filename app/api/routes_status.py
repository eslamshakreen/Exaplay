"""Status and metadata API routes for ExaPlay.

Implements status monitoring and version information endpoints.
All routes require authentication except where noted.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from typing_extensions import Annotated

from app.deps import get_authenticated_request, get_public_request
from app.exaplay.mapper import ExaPlayMappingError, parse_status_response, parse_version_response
from app.exaplay.models import ErrorResponse, HealthResponse, StatusResponse, VersionResponse
from app.exaplay.tcp_client import (
    ExaPlayError,
    send_exaplay_command,
)
from app.logging import PerformanceTimer, get_logger, get_trace_id

# Import error mapping from control routes  
from app.api.routes_control import map_exaplay_error_to_http

logger = get_logger(__name__)

# Health router (no auth required)
health_router = APIRouter(tags=["Health"])

# Status/meta routers (auth required)
status_router = APIRouter(
    prefix="/compositions",
    tags=["Status"],
    dependencies=get_authenticated_request()
)

meta_router = APIRouter(
    tags=["Meta"],
    dependencies=get_authenticated_request()
)


@health_router.get(
    "/healthz",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Simple health check endpoint that doesn't require authentication",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "ok"}
                }
            }
        }
    }
)
async def health_check() -> HealthResponse:
    """Health check endpoint for service monitoring.
    
    This endpoint is used by load balancers, container orchestrators,
    and monitoring systems to verify that the service is running and
    responsive. It does not require authentication.
    
    Returns:
        HealthResponse: Simple status indicator
    """
    logger.debug("Health check requested")
    return HealthResponse(status="ok")


@meta_router.get(
    "/version",
    response_model=VersionResponse,
    summary="Get ExaPlay version (via `get:ver`)",
    description="Retrieves version information from the connected ExaPlay server",
    responses={
        200: {
            "description": "ExaPlay version string",
            "content": {
                "application/json": {
                    "example": {"exaplayVersion": "2.21.0.0"}
                }
            }
        },
        502: {"description": "Upstream (TCP) error or malformed response from ExaPlay"},
        504: {"description": "Upstream TCP timeout while talking to ExaPlay"}
    }
)
async def get_version() -> VersionResponse:
    """Get ExaPlay server version information.
    
    Sends the `get:ver` command to ExaPlay and returns the version
    string. This can be useful for compatibility checking and debugging.
    
    Returns:
        VersionResponse: ExaPlay version information
        
    Raises:
        HTTPException: For various error conditions (timeout, connection, protocol)
    """
    command = "get:ver"
    
    try:
        with PerformanceTimer("get_version", logger):
            reply = await send_exaplay_command(command)
        
        # Parse the version response
        try:
            version_response = parse_version_response(reply)
        except ExaPlayMappingError as e:
            logger.error(
                "Failed to parse version response",
                reply=reply,
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=ErrorResponse(
                    error=f"Malformed version response: {str(e)}",
                    command=command,
                    traceId=get_trace_id()
                ).model_dump()
            )
        
        logger.info(
            "Get version successful",
            version=version_response.exaplayVersion,
            reply=reply
        )
        
        return version_response
        
    except ExaPlayError as e:
        logger.error(
            "Get version failed",
            command=command,
            error=str(e)
        )
        raise map_exaplay_error_to_http(e)


@status_router.get(
    "/{name}/status",
    response_model=StatusResponse,
    summary="Get normalized composition status",
    description="Wraps `get:status,{name}` and maps CSV to normalized JSON",
    responses={
        200: {
            "description": "Normalized status payload",
            "content": {
                "application/json": {
                    "example": {
                        "state": "playing",
                        "time": 15.65,
                        "frame": 939,
                        "clipIndex": 2,
                        "duration": 300.0
                    }
                }
            }
        },
        502: {"description": "Upstream (TCP) error or malformed response from ExaPlay"},
        504: {"description": "Upstream TCP timeout while talking to ExaPlay"}
    }
)
async def get_status(
    name: Annotated[str, Path(description="ExaPlay composition name (timeline or cuelist)", min_length=1)]
) -> StatusResponse:
    """Get normalized composition status.
    
    Retrieves the current status of a composition from ExaPlay and
    converts it from the raw CSV format to a normalized JSON structure.
    
    The CSV format from ExaPlay is:
    state(0=stopped,1=playing,2=paused), time(s), frame, clipIndex(-1 if N/A), duration(s)
    
    This is converted to a structured response with enum state values
    and properly typed numeric fields.
    
    Args:
        name: Name of the composition to query
        
    Returns:
        StatusResponse: Normalized status information
        
    Raises:
        HTTPException: For various error conditions (timeout, connection, protocol)
    """
    command = f"get:status,{name}"
    
    try:
        with PerformanceTimer("get_status", logger, composition=name):
            reply = await send_exaplay_command(command)
        
        # Parse the status response from CSV to normalized JSON
        try:
            status_response = parse_status_response(reply)
        except ExaPlayMappingError as e:
            logger.error(
                "Failed to parse status response",
                composition=name,
                reply=reply,
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=ErrorResponse(
                    error=f"Malformed status response: {str(e)}",
                    command=command,
                    traceId=get_trace_id()
                ).model_dump()
            )
        
        logger.info(
            "Get status successful",
            composition=name,
            state=status_response.state,
            time=status_response.time,
            frame=status_response.frame,
            clip_index=status_response.clipIndex,
            duration=status_response.duration
        )
        
        return status_response
        
    except ExaPlayError as e:
        logger.error(
            "Get status failed",
            composition=name,
            command=command,
            error=str(e)
        )
        raise map_exaplay_error_to_http(e)
