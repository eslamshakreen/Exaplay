"""Pydantic models for ExaPlay API requests and responses.

This module defines all the data models that match the OpenAPI specification
exactly, ensuring type safety and automatic validation/serialization.
"""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PlaybackState(str, Enum):
    """ExaPlay playback states mapped from numeric values.
    
    ExaPlay returns:
    - 0 = stopped
    - 1 = playing  
    - 2 = paused
    """
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


# Request Models
class CuetimeSetRequest(BaseModel):
    """Request to seek to a specific time in seconds for timeline compositions."""
    seconds: float = Field(..., ge=0, description="Time to seek to in seconds")
    
    model_config = {"json_schema_extra": {"examples": [{"seconds": 12.5}]}}


class CueSetRequest(BaseModel):
    """Request to jump to a specific cue (timeline) or clip (cuelist).
    
    For cuelists, index is 1-based clip number.
    For timelines, it is the cue index.
    """
    index: int = Field(..., ge=1, description="Cue/clip index (1-based for cuelists)")
    
    model_config = {"json_schema_extra": {"examples": [{"index": 3}]}}


class VolumeSetRequest(BaseModel):
    """Request to set composition volume."""
    value: int = Field(..., ge=0, le=100, description="Volume level 0-100")
    
    model_config = {"json_schema_extra": {"examples": [{"value": 60}]}}


class CommandRequest(BaseModel):
    """Request to send a raw ExaPlay command (admin/debug endpoint)."""
    raw: str = Field(..., description="Raw ExaPlay command without trailing CR")
    
    model_config = {"json_schema_extra": {"examples": [{"raw": "get:status,comp1"}]}}


# Response Models
class VersionResponse(BaseModel):
    """Response containing ExaPlay version information."""
    exaplayVersion: str = Field(..., description="ExaPlay version string")
    
    model_config = {"json_schema_extra": {"examples": [{"exaplayVersion": "2.21.0.0"}]}}


class GenericReply(BaseModel):
    """Generic response containing the sent command and ExaPlay's reply."""
    sent: str = Field(..., description="Raw command sent to ExaPlay")
    reply: str = Field(..., description="Raw single-line reply from ExaPlay")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{"sent": "play,comp1", "reply": "OK"}]
        }
    }


class VolumeResponse(BaseModel):
    """Response containing current volume level."""
    value: int = Field(..., ge=0, le=100, description="Current volume level 0-100")
    
    model_config = {"json_schema_extra": {"examples": [{"value": 60}]}}


class StatusResponse(BaseModel):
    """Normalized composition status response.
    
    Parsed from ExaPlay's CSV format:
    state(0=stopped,1=playing,2=paused), time(s), frame, clipIndex(-1 if N/A), duration(s)
    """
    state: PlaybackState = Field(..., description="Current playback state")
    time: float = Field(..., description="Current time position in seconds")
    frame: int = Field(..., description="Current frame number")
    clipIndex: int = Field(..., description="Current clip index (-1 if N/A)")
    duration: float = Field(..., description="Total duration in seconds")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "state": "playing",
                "time": 15.65,
                "frame": 939,
                "clipIndex": 2,
                "duration": 300.0
            }]
        }
    }


class ErrorResponse(BaseModel):
    """Standardized error response with trace ID for debugging."""
    error: str = Field(..., description="Error message")
    command: Optional[str] = Field(None, description="Command that caused the error")
    traceId: str = Field(..., description="Unique trace ID for request tracking")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "error": "ERR from ExaPlay",
                "command": "play,comp1", 
                "traceId": "7b0e9d3c2b6f4f88a2f7a1a9e98b2c4d"
            }]
        }
    }


class SSEStatusEvent(BaseModel):
    """Server-Sent Event payload for live status updates.
    
    Emitted when OSC is enabled and ExaPlay sends status updates.
    """
    composition: str = Field(..., description="Composition name")
    status: int = Field(..., description="Numeric status (0=stopped, 1=playing, 2=paused)")
    cuetime: float = Field(..., description="Current time in seconds")
    cueframe: int = Field(..., description="Current frame number")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "composition": "comp1",
                "status": 1,
                "cuetime": 15.6,
                "cueframe": 939
            }]
        }
    }


# Health Check Response
class HealthResponse(BaseModel):
    """Simple health check response."""
    status: str = Field(default="ok", description="Service health status")
    
    model_config = {"json_schema_extra": {"examples": [{"status": "ok"}]}}
