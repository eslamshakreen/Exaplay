"""Application settings and configuration management.

Loads configuration from environment variables using Pydantic BaseSettings.
Supports .env file loading for development environments.
"""

from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.
    
    All settings can be overridden via environment variables.
    For development, create a .env file with the required values.
    """
    
    # ExaPlay Connection Settings
    exaplay_host: str = Field(
        default="192.168.1.174",
        description="ExaPlay server hostname or IP address"
    )
    exaplay_tcp_port: int = Field(
        default=7000,
        description="ExaPlay TCP control port"
    )
    
    # TCP Client Settings  
    tcp_timeout: float = Field(
        default=5.0,
        description="TCP operation timeout in seconds"
    )
    tcp_max_retries: int = Field(
        default=3,
        description="Maximum number of TCP retry attempts"
    )
    tcp_retry_backoff: float = Field(
        default=1.0,
        description="Initial retry backoff delay in seconds (exponential)"
    )
    
    # OSC Settings (Optional live status streaming)
    exaplay_osc_enable: bool = Field(
        default=False,
        description="Enable OSC listener for live status updates"
    )
    exaplay_osc_prefix: str = Field(
        default="exaplay",
        description="OSC address prefix filter"
    )
    exaplay_osc_listen: str = Field(
        default="0.0.0.0:8000",
        description="OSC listener bind address and port"
    )
    
    # Security Settings
    api_key: str = Field(
        ...,
        description="Bearer token for API authentication (required)"
    )
    
    # CORS Settings
    cors_allow_origins_str: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated list of allowed CORS origins",
        alias="CORS_ALLOW_ORIGINS"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )
    cors_allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods for CORS"
    )
    cors_allow_headers: List[str] = Field(
        default=["*"],
        description="Allowed headers for CORS"
    )
    
    # Logging Settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or console)"
    )
    
    # API Settings
    api_title: str = Field(
        default="ExaPlay Control API",
        description="API title for OpenAPI documentation"
    )
    api_version: str = Field(
        default="1.0.0",
        description="API version"
    )
    api_description: str = Field(
        default="""Backend-only REST API to control and monitor ExaPlay over TCP (and optionally OSC OUT).
        
- Phase 1: No UI. HTTP endpoints translate to ExaPlay TCP commands.
- Security: Static Bearer token on all routes except `/healthz`.
- Notes:
  * TCP commands are sent as ASCII/UTF-8 lines ending with CR (`\\r`); replies end with CRLF (`\\r\\n`).
  * `set:cue` targets a timeline cue **or** a cuelist clip (1-based index).
  * `get:status` returns: state(0=stopped,1=playing,2=paused), time(s), frame, clipIndex(-1 if N/A), duration(s).""",
        description="API description for OpenAPI documentation"
    )
    
    # Performance Settings
    rate_limit_commands_per_minute: int = Field(
        default=60,
        description="Rate limit for /exaplay/command endpoint (requests per minute)"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def cors_allow_origins(self) -> List[str]:
        """Parse CORS origins from string to list."""
        return [origin.strip() for origin in self.cors_allow_origins_str.split(",") if origin.strip()]
    
    @property
    def osc_host(self) -> str:
        """Extract host from OSC listen address."""
        return self.exaplay_osc_listen.split(":")[0]
    
    @property
    def osc_port(self) -> int:
        """Extract port from OSC listen address."""
        return int(self.exaplay_osc_listen.split(":")[1])
    
    def validate_settings(self) -> None:
        """Validate settings for consistency and required values.
        
        Raises:
            ValueError: If settings are invalid or inconsistent.
        """
        if not self.api_key or len(self.api_key) < 32:
            raise ValueError("API_KEY must be at least 32 characters long")
        
        if self.tcp_timeout <= 0:
            raise ValueError("TCP_TIMEOUT must be positive")
        
        if self.tcp_max_retries < 0:
            raise ValueError("TCP_MAX_RETRIES must be non-negative")
        
        if self.exaplay_osc_enable:
            try:
                # Validate OSC listen address format
                host, port = self.exaplay_osc_listen.split(":")
                port_num = int(port)
                if not (1 <= port_num <= 65535):
                    raise ValueError(f"OSC port {port_num} out of valid range")
            except (ValueError, IndexError) as e:
                raise ValueError(f"Invalid EXAPLAY_OSC_LISTEN format: {e}") from e


# Global settings instance
# This will be imported by other modules to access configuration
settings = Settings()

# Validate settings on import
try:
    settings.validate_settings()
except ValueError as e:
    # In production, you might want to log this and exit gracefully
    # For now, we'll raise the error to catch configuration issues early
    raise RuntimeError(f"Invalid configuration: {e}") from e
