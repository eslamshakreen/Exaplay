"""FastAPI dependencies for authentication, CORS, and request handling.

Provides reusable dependency functions for Bearer token authentication,
CORS configuration, and other common request processing needs.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware

from app.exaplay.models import ErrorResponse
from app.logging import RequestLoggingContext, get_logger, get_trace_id, set_trace_id
from app.settings import settings

logger = get_logger(__name__)

# HTTP Bearer security scheme for OpenAPI documentation
security = HTTPBearer(
    scheme_name="bearerAuth",
    description="API Key authentication. Use 'Bearer <API_KEY>' in Authorization header.",
    auto_error=False  # We'll handle errors manually for better control
)


async def verify_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> None:
    """Verify Bearer token authentication.
    
    Validates the provided Bearer token against the configured API key.
    Provides detailed error responses with trace IDs for debugging.
    
    Args:
        request: FastAPI request object for context
        credentials: Bearer token from Authorization header
        
    Raises:
        HTTPException: 401 for missing/invalid token, 403 for incorrect token
    """
    trace_id = get_trace_id()
    
    # Check if credentials were provided
    if not credentials:
        logger.warning(
            "Authentication failed: missing credentials",
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else "unknown"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error="Missing or invalid Authorization header. Use 'Bearer <API_KEY>'.",
                traceId=trace_id
            ).model_dump(),
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verify token matches configured API key
    if credentials.credentials != settings.api_key:
        logger.warning(
            "Authentication failed: invalid API key",
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else "unknown",
            provided_key_prefix=credentials.credentials[:8] + "..." if len(credentials.credentials) > 8 else "short_key"
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                error="Invalid API key",
                traceId=trace_id
            ).model_dump(),
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Log successful authentication
    logger.debug(
        "Authentication successful",
        path=request.url.path,
        method=request.method,
        client_ip=request.client.host if request.client else "unknown"
    )


async def setup_request_context(request: Request) -> str:
    """Set up request context with trace ID and logging.
    
    Extracts or generates a trace ID for the request and sets up
    the logging context. This should be one of the first dependencies
    to run for each request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Trace ID for this request
    """
    # Extract trace ID from headers if provided, otherwise generate new one
    trace_id = request.headers.get("X-Trace-ID")
    if not trace_id:
        # Generate new trace ID and set in context
        with RequestLoggingContext() as new_trace_id:
            trace_id = new_trace_id
    else:
        # Use provided trace ID
        set_trace_id(trace_id)
    
    # Log request start
    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params) if request.query_params else None,
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("User-Agent")
    )
    
    return trace_id


def configure_cors(app) -> None:
    """Configure CORS middleware for the FastAPI application.
    
    Sets up CORS based on the settings configuration, allowing
    cross-origin requests from specified origins with proper
    credential and header handling.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
        expose_headers=["X-Trace-ID"]  # Allow clients to see trace IDs
    )
    
    logger.info(
        "CORS configured",
        allowed_origins=settings.cors_allow_origins,
        allow_credentials=settings.cors_allow_credentials
    )


# Dependency combinations for common use cases
def get_authenticated_request() -> list:
    """Get dependencies for authenticated endpoints.
    
    Returns:
        list: Dependencies for endpoints requiring authentication
    """
    return [Depends(setup_request_context), Depends(verify_api_key)]


def get_public_request() -> list:
    """Get dependencies for public endpoints (no auth required).
    
    Returns:
        list: Dependencies for public endpoints
    """
    return [Depends(setup_request_context)]


# Rate limiting dependency (simplified implementation)
class RateLimiter:
    """Simple in-memory rate limiter for API endpoints.
    
    Note: This is a basic implementation suitable for single-instance
    deployments. For production clusters, consider using Redis or
    similar distributed rate limiting solutions.
    """
    
    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        """Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict = {}  # client_ip -> list of timestamps
    
    async def check_rate_limit(self, request: Request) -> None:
        """Check if request is within rate limits.
        
        Args:
            request: FastAPI request object
            
        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        import time
        
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Initialize or clean up old requests for this client
        if client_ip not in self._requests:
            self._requests[client_ip] = []
        
        # Remove requests outside the current window
        self._requests[client_ip] = [
            req_time for req_time in self._requests[client_ip]
            if current_time - req_time < self.window_seconds
        ]
        
        # Check if limit exceeded
        if len(self._requests[client_ip]) >= self.max_requests:
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                requests_in_window=len(self._requests[client_ip]),
                max_requests=self.max_requests,
                window_seconds=self.window_seconds
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=ErrorResponse(
                    error=f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds} seconds.",
                    traceId=get_trace_id()
                ).model_dump(),
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Window": str(self.window_seconds)
                }
            )
        
        # Record this request
        self._requests[client_ip].append(current_time)


# Create rate limiter instance for admin commands
admin_rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_commands_per_minute,
    window_seconds=60
)


async def check_admin_rate_limit(request: Request) -> None:
    """Rate limiting dependency for admin endpoints.
    
    Args:
        request: FastAPI request object
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    await admin_rate_limiter.check_rate_limit(request)
