
"""Structured JSON logging configuration with trace IDs.

Provides centralized logging setup with structured output suitable for
production monitoring and debugging. Includes trace ID injection for
request correlation.
"""

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional

import structlog
from structlog.types import FilteringBoundLogger

from app.settings import settings

# Context variable to store trace ID for the current request
trace_id_context: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


def get_trace_id() -> str:
    """Get the current trace ID, generating a new one if needed.
    
    Returns:
        str: Current trace ID or a newly generated UUID.
    """
    trace_id = trace_id_context.get()
    if trace_id is None:
        trace_id = str(uuid.uuid4()).replace("-", "")
        trace_id_context.set(trace_id)
    return trace_id


def set_trace_id(trace_id: str) -> None:
    """Set the trace ID for the current context.
    
    Args:
        trace_id: Unique identifier for request tracing.
    """
    trace_id_context.set(trace_id)


def clear_trace_id() -> None:
    """Clear the current trace ID from context."""
    trace_id_context.set(None)


def add_trace_id(logger: FilteringBoundLogger, name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Processor to inject trace ID into all log messages.
    
    Args:
        logger: The logger instance.
        name: Logger name.
        event_dict: Log event dictionary.
        
    Returns:
        dict: Event dictionary with trace_id added.
    """
    event_dict["trace_id"] = get_trace_id()
    return event_dict


def add_timestamp(logger: FilteringBoundLogger, name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Processor to add ISO timestamp to log messages.
    
    Args:
        logger: The logger instance.
        name: Logger name.
        event_dict: Log event dictionary.
        
    Returns:
        dict: Event dictionary with timestamp added.
    """
    # Use datetime for microsecond precision
    import datetime
    event_dict["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
    return event_dict


def add_component(logger: FilteringBoundLogger, name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Processor to add component name based on logger name.
    
    Args:
        logger: The logger instance.
        name: Logger name.
        event_dict: Log event dictionary.
        
    Returns:
        dict: Event dictionary with component added.
    """
    # Extract component from logger name (e.g., "app.exaplay.tcp_client" -> "tcp_client")
    if "." in name:
        event_dict["component"] = name.split(".")[-1]
    else:
        event_dict["component"] = name
    return event_dict


def json_renderer(logger: FilteringBoundLogger, name: str, event_dict: Dict[str, Any]) -> str:
    """Render log messages as JSON.
    
    Args:
        logger: The logger instance.
        name: Logger name.
        event_dict: Log event dictionary.
        
    Returns:
        str: JSON-formatted log line.
    """
    return json.dumps(event_dict, ensure_ascii=False, separators=(",", ":"))


def console_renderer(logger: FilteringBoundLogger, name: str, event_dict: Dict[str, Any]) -> str:
    """Render log messages in human-readable console format.
    
    Args:
        logger: The logger instance.
        name: Logger name.
        event_dict: Log event dictionary.
        
    Returns:
        str: Human-readable log line.
    """
    timestamp = event_dict.pop("timestamp", "")
    level = event_dict.pop("level", "").upper()
    trace_id = event_dict.pop("trace_id", "")[:8]  # Short trace ID for console
    component = event_dict.pop("component", "")
    event = event_dict.pop("event", "")
    
    # Format: [timestamp] LEVEL [trace_id] component: event {extra_fields}
    base = f"[{timestamp}] {level:5} [{trace_id}] {component}: {event}"
    
    if event_dict:
        # Add remaining fields as key=value pairs
        extras = " ".join(f"{k}={v}" for k, v in event_dict.items())
        return f"{base} {extras}"
    
    return base


def configure_logging() -> None:
    """Configure structured logging based on settings.
    
    Sets up structlog with appropriate processors and renderers
    based on the LOG_FORMAT setting (json or console).
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    
    # Choose renderer based on format setting
    if settings.log_format.lower() == "json":
        renderer = json_renderer
    else:
        renderer = console_renderer
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            add_timestamp,
            add_trace_id,
            add_component,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


class RequestLoggingContext:
    """Context manager for request-scoped logging with automatic trace ID management.
    
    Example:
        with RequestLoggingContext() as trace_id:
            logger.info("Processing request", user_id=123)
            # All log messages will include the trace_id
    """
    
    def __init__(self, trace_id: Optional[str] = None) -> None:
        """Initialize context manager.
        
        Args:
            trace_id: Optional trace ID. If None, a new one will be generated.
        """
        self.trace_id = trace_id or str(uuid.uuid4()).replace("-", "")
        self.previous_trace_id: Optional[str] = None
    
    def __enter__(self) -> str:
        """Enter the context and set trace ID.
        
        Returns:
            str: The trace ID for this context.
        """
        self.previous_trace_id = trace_id_context.get()
        set_trace_id(self.trace_id)
        return self.trace_id
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context and restore previous trace ID."""
        trace_id_context.set(self.previous_trace_id)


def get_logger(name: str) -> FilteringBoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name, typically __name__ from the calling module.
        
    Returns:
        FilteringBoundLogger: Configured structlog logger.
    """
    return structlog.get_logger(name)


# Performance logging helpers
class PerformanceTimer:
    """Context manager for measuring and logging operation duration.
    
    Example:
        with PerformanceTimer("tcp_command", logger, command="play,comp1"):
            await tcp_client.send_command("play,comp1")
        # Logs: "Operation completed" with latency_ms field
    """
    
    def __init__(
        self,
        operation: str,
        logger: FilteringBoundLogger,
        **extra_fields: Any
    ) -> None:
        """Initialize performance timer.
        
        Args:
            operation: Name of the operation being timed.
            logger: Logger instance to use for output.
            **extra_fields: Additional fields to include in log output.
        """
        self.operation = operation
        self.logger = logger
        self.extra_fields = extra_fields
        self.start_time: float = 0.0
    
    def __enter__(self) -> "PerformanceTimer":
        """Start timing the operation."""
        self.start_time = time.perf_counter()
        self.logger.debug(
            "Operation started",
            operation=self.operation,
            **self.extra_fields
        )
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop timing and log the duration."""
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        
        if exc_type is None:
            outcome = "success"
            log_level = "info"
        else:
            outcome = "error"
            log_level = "error"
        
        getattr(self.logger, log_level)(
            "Operation completed",
            operation=self.operation,
            latency_ms=round(duration_ms, 2),
            outcome=outcome,
            **self.extra_fields
        )


# Initialize logging on module import
configure_logging()
