"""Data mapping utilities for ExaPlay responses.

Converts ExaPlay's CSV-based responses into normalized JSON structures
that match the OpenAPI specification. Handles type conversions, state
mapping, and error handling for malformed responses.
"""

from typing import List

from app.exaplay.models import PlaybackState, StatusResponse, VersionResponse
from app.logging import get_logger

logger = get_logger(__name__)


class ExaPlayMappingError(Exception):
    """Raised when ExaPlay response cannot be parsed or mapped."""
    
    def __init__(self, message: str, raw_response: str) -> None:
        super().__init__(message)
        self.raw_response = raw_response


def parse_status_response(raw_response: str) -> StatusResponse:
    """Parse ExaPlay status CSV response into normalized StatusResponse.
    
    ExaPlay status format (CSV):
    state(0=stopped,1=playing,2=paused), time(s), frame, clipIndex(-1 if N/A), duration(s)
    
    Example inputs:
    - "1,15.65,939,-1,300.0" -> StatusResponse(state="playing", time=15.65, ...)
    - "0,0.0,0,-1,120.5" -> StatusResponse(state="stopped", time=0.0, ...)
    - "2,45.2,2714,3,180.0" -> StatusResponse(state="paused", time=45.2, clipIndex=3, ...)
    
    Args:
        raw_response: Raw CSV response from ExaPlay
        
    Returns:
        StatusResponse: Normalized status object
        
    Raises:
        ExaPlayMappingError: If response format is invalid or contains unexpected values
    """
    logger.debug("Parsing status response", raw_response=raw_response)
    
    # Split CSV and validate field count
    fields = raw_response.strip().split(",")
    if len(fields) != 5:
        raise ExaPlayMappingError(
            f"Expected 5 CSV fields, got {len(fields)}",
            raw_response
        )
    
    try:
        # Parse individual fields with type conversion
        state_raw, time_raw, frame_raw, clip_index_raw, duration_raw = fields
        
        # Map numeric state to enum
        state_int = int(state_raw.strip())
        if state_int == 0:
            state = PlaybackState.STOPPED
        elif state_int == 1:
            state = PlaybackState.PLAYING
        elif state_int == 2:
            state = PlaybackState.PAUSED
        else:
            raise ExaPlayMappingError(
                f"Invalid state value: {state_int} (expected 0, 1, or 2)",
                raw_response
            )
        
        # Parse numeric fields
        time = float(time_raw.strip())
        frame = int(frame_raw.strip())
        clip_index = int(clip_index_raw.strip())
        duration = float(duration_raw.strip())
        
        # Validate ranges
        if time < 0:
            logger.warning("Negative time value in status", time=time)
        
        if frame < 0:
            logger.warning("Negative frame value in status", frame=frame)
        
        if duration < 0:
            logger.warning("Negative duration value in status", duration=duration)
        
        # Create response object
        status_response = StatusResponse(
            state=state,
            time=time,
            frame=frame,
            clipIndex=clip_index,
            duration=duration
        )
        
        logger.debug(
            "Successfully parsed status",
            state=state,
            time=time,
            frame=frame,
            clip_index=clip_index,
            duration=duration
        )
        
        return status_response
        
    except ValueError as e:
        raise ExaPlayMappingError(
            f"Failed to parse numeric fields: {e}",
            raw_response
        ) from e
    except Exception as e:
        raise ExaPlayMappingError(
            f"Unexpected error parsing status: {e}",
            raw_response
        ) from e


def parse_version_response(raw_response: str) -> VersionResponse:
    """Parse ExaPlay version response into normalized VersionResponse.
    
    ExaPlay version format is typically a simple version string like "2.21.0.0"
    or may include additional text that should be cleaned up.
    
    Args:
        raw_response: Raw version response from ExaPlay
        
    Returns:
        VersionResponse: Normalized version object
        
    Raises:
        ExaPlayMappingError: If response is empty or invalid
    """
    logger.debug("Parsing version response", raw_response=raw_response)
    
    version_str = raw_response.strip()
    
    # Validate non-empty response
    if not version_str:
        raise ExaPlayMappingError(
            "Empty version response",
            raw_response
        )
    
    # Handle common version response patterns
    # Some ExaPlay versions might return "Version: X.Y.Z" or similar
    if version_str.lower().startswith("version:"):
        version_str = version_str[8:].strip()
    elif version_str.lower().startswith("ver:"):
        version_str = version_str[4:].strip()
    
    # Basic validation - should contain at least one digit and dot
    if not any(c.isdigit() for c in version_str) or "." not in version_str:
        logger.warning(
            "Version string doesn't match expected format",
            version=version_str
        )
    
    version_response = VersionResponse(exaplayVersion=version_str)
    
    logger.debug("Successfully parsed version", version=version_str)
    return version_response


def parse_volume_response(raw_response: str) -> int:
    """Parse ExaPlay volume response into integer value.
    
    ExaPlay volume responses are typically just the numeric value,
    but may have whitespace or additional text to clean up.
    
    Args:
        raw_response: Raw volume response from ExaPlay
        
    Returns:
        int: Volume level (0-100)
        
    Raises:
        ExaPlayMappingError: If response cannot be parsed as valid volume
    """
    logger.debug("Parsing volume response", raw_response=raw_response)
    
    volume_str = raw_response.strip()
    
    # Handle potential prefixes like "Volume: 60" or "vol: 60"
    if ":" in volume_str:
        volume_str = volume_str.split(":")[-1].strip()
    
    try:
        volume = int(volume_str)
        
        # Validate range
        if not 0 <= volume <= 100:
            raise ExaPlayMappingError(
                f"Volume {volume} out of valid range (0-100)",
                raw_response
            )
        
        logger.debug("Successfully parsed volume", volume=volume)
        return volume
        
    except ValueError as e:
        raise ExaPlayMappingError(
            f"Failed to parse volume as integer: {e}",
            raw_response
        ) from e


def validate_csv_fields(raw_response: str, expected_count: int) -> List[str]:
    """Validate and split CSV response into expected number of fields.
    
    Args:
        raw_response: Raw CSV response
        expected_count: Expected number of CSV fields
        
    Returns:
        List[str]: List of trimmed field values
        
    Raises:
        ExaPlayMappingError: If field count doesn't match expected
    """
    fields = [field.strip() for field in raw_response.strip().split(",")]
    
    if len(fields) != expected_count:
        raise ExaPlayMappingError(
            f"Expected {expected_count} CSV fields, got {len(fields)}",
            raw_response
        )
    
    return fields


def safe_int_parse(value: str, field_name: str, raw_response: str) -> int:
    """Safely parse string to integer with error context.
    
    Args:
        value: String value to parse
        field_name: Name of the field for error reporting
        raw_response: Original response for error context
        
    Returns:
        int: Parsed integer value
        
    Raises:
        ExaPlayMappingError: If parsing fails
    """
    try:
        return int(value.strip())
    except ValueError as e:
        raise ExaPlayMappingError(
            f"Failed to parse {field_name} '{value}' as integer: {e}",
            raw_response
        ) from e


def safe_float_parse(value: str, field_name: str, raw_response: str) -> float:
    """Safely parse string to float with error context.
    
    Args:
        value: String value to parse
        field_name: Name of the field for error reporting
        raw_response: Original response for error context
        
    Returns:
        float: Parsed float value
        
    Raises:
        ExaPlayMappingError: If parsing fails
    """
    try:
        return float(value.strip())
    except ValueError as e:
        raise ExaPlayMappingError(
            f"Failed to parse {field_name} '{value}' as float: {e}",
            raw_response
        ) from e
