"""Main FastAPI application entry point.

Sets up the FastAPI app with all routes, middleware, error handling,
and lifecycle management for the ExaPlay Control API.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api import routes_admin, routes_control, routes_events, routes_position, routes_status, routes_volume
from app.deps import configure_cors
from app.exaplay.models import ErrorResponse
from app.exaplay.osc_listener import osc_broadcaster
from app.logging import RequestLoggingContext, get_logger, get_trace_id
from app.settings import settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup and shutdown tasks.
    
    Handles:
    - OSC listener startup/shutdown (if enabled)
    - Graceful resource cleanup
    - Application lifecycle logging
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info(
        "ExaPlay Control API starting up",
        version=settings.api_version,
        exaplay_host=settings.exaplay_host,
        exaplay_port=settings.exaplay_tcp_port,
        osc_enabled=settings.exaplay_osc_enable,
        log_level=settings.log_level
    )
    
    # Start OSC listener if enabled
    if settings.exaplay_osc_enable:
        try:
            await osc_broadcaster.start()
            logger.info("OSC broadcaster started successfully")
        except Exception as e:
            logger.error("Failed to start OSC broadcaster", error=str(e))
            # Continue startup even if OSC fails (feature is optional)
    
    logger.info("ExaPlay Control API startup complete")
    
    yield
    
    # Shutdown
    logger.info("ExaPlay Control API shutting down")
    
    # Stop OSC listener
    if settings.exaplay_osc_enable:
        try:
            await osc_broadcaster.stop()
            logger.info("OSC broadcaster stopped")
        except Exception as e:
            logger.error("Error stopping OSC broadcaster", error=str(e))
    
    logger.info("ExaPlay Control API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    # Security scheme will be added via route decorators
)

# Configure CORS
configure_cors(app)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors with proper error format.
    
    Args:
        request: FastAPI request object
        exc: Validation error exception
        
    Returns:
        JSONResponse: Formatted error response with trace ID
    """
    trace_id = get_trace_id()
    
    logger.warning(
        "Request validation failed",
        path=request.url.path,
        method=request.method,
        errors=exc.errors(),
        client_ip=request.client.host if request.client else "unknown"
    )
    
    # Create user-friendly error message
    error_details = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_details.append(f"{field}: {message}")
    
    error_response = ErrorResponse(
        error=f"Validation error: {'; '.join(error_details)}",
        traceId=trace_id,
        details={"validation_errors": exc.errors()}
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.model_dump()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with proper error format.
    
    Args:
        request: FastAPI request object
        exc: The unhandled exception
        
    Returns:
        JSONResponse: Formatted error response with trace ID
    """
    trace_id = get_trace_id()
    
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exception_type=type(exc).__name__,
        client_ip=request.client.host if request.client else "unknown",
        exc_info=True
    )
    
    error_response = ErrorResponse(
        error="Internal server error",
        traceId=trace_id,
        details={"exception_type": type(exc).__name__}
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )


# Middleware for request/response logging
@app.middleware("http")
async def request_response_logging_middleware(request: Request, call_next):
    """Middleware to log request/response details and timing.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/route handler
        
    Returns:
        Response from the next handler
    """
    # Set up request context with trace ID
    with RequestLoggingContext() as trace_id:
        # Add trace ID to response headers
        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        
        # Log response details
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            response_size=response.headers.get("content-length", "unknown"),
            client_ip=request.client.host if request.client else "unknown"
        )
        
        return response


# Include all route modules
app.include_router(routes_status.health_router)  # Health endpoint (no auth)
app.include_router(routes_status.meta_router)    # Version endpoint
app.include_router(routes_status.status_router)  # Status endpoints
app.include_router(routes_control.router)        # Control endpoints
app.include_router(routes_position.router)       # Position endpoints  
app.include_router(routes_volume.router)         # Volume endpoints
app.include_router(routes_admin.router)          # Admin endpoints
app.include_router(routes_events.router)         # Events/SSE endpoints

logger.info(
    "FastAPI routes configured",
    total_routes=len(app.routes),
    docs_url="/docs",
    openapi_url="/openapi.json"
)


# Root endpoint for API information
@app.get(
    "/",
    tags=["Meta"],
    summary="API Information",
    description="Returns basic API information and links to documentation"
)
async def api_root() -> Dict[str, Any]:
    """Root endpoint providing API information and navigation.
    
    Returns:
        Dict: API metadata and documentation links
    """
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": "Production-grade REST API for ExaPlay media server control",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/healthz",
        "exaplay": {
            "host": settings.exaplay_host,
            "tcp_port": settings.exaplay_tcp_port,
            "osc_enabled": settings.exaplay_osc_enable
        }
    }


if __name__ == "__main__":
    # This allows running the app directly with `python -m app.main`
    # For production, use uvicorn from command line or container
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level.lower(),
        reload=False  # Set to True for development
    )
