"""Tests for ExaPlay response mapping utilities.

Tests the data mapping functions that convert ExaPlay's CSV responses
into normalized JSON structures.
"""

import pytest

from app.exaplay.mapper import (
    ExaPlayMappingError,
    parse_status_response,
    parse_version_response,
    parse_volume_response,
)
from app.exaplay.models import PlaybackState


class TestStatusResponseMapping:
    """Test cases for status response CSV parsing."""
    
    def test_parse_status_stopped(self) -> None:
        """Test parsing stopped status response."""
        csv_response = "0,0.0,0,-1,300.0"
        
        status = parse_status_response(csv_response)
        
        assert status.state == PlaybackState.STOPPED
        assert status.time == 0.0
        assert status.frame == 0
        assert status.clipIndex == -1
        assert status.duration == 300.0
    
    def test_parse_status_playing(self) -> None:
        """Test parsing playing status response."""
        csv_response = "1,15.65,939,2,300.0"
        
        status = parse_status_response(csv_response)
        
        assert status.state == PlaybackState.PLAYING
        assert status.time == 15.65
        assert status.frame == 939
        assert status.clipIndex == 2
        assert status.duration == 300.0
    
    def test_parse_status_paused(self) -> None:
        """Test parsing paused status response."""
        csv_response = "2,45.2,2714,3,180.0"
        
        status = parse_status_response(csv_response)
        
        assert status.state == PlaybackState.PAUSED
        assert status.time == 45.2
        assert status.frame == 2714
        assert status.clipIndex == 3
        assert status.duration == 180.0
    
    def test_parse_status_cuelist_format(self) -> None:
        """Test parsing status for cuelist with 1-based clip index."""
        csv_response = "1,30.5,915,1,120.0"
        
        status = parse_status_response(csv_response)
        
        assert status.state == PlaybackState.PLAYING
        assert status.time == 30.5
        assert status.frame == 915
        assert status.clipIndex == 1  # 1-based for cuelists
        assert status.duration == 120.0
    
    def test_parse_status_with_whitespace(self) -> None:
        """Test parsing status response with extra whitespace."""
        csv_response = " 1 , 15.65 , 939 , 2 , 300.0 "
        
        status = parse_status_response(csv_response)
        
        assert status.state == PlaybackState.PLAYING
        assert status.time == 15.65
        assert status.frame == 939
        assert status.clipIndex == 2
        assert status.duration == 300.0
    
    def test_parse_status_invalid_field_count(self) -> None:
        """Test parsing status with wrong number of fields."""
        csv_response = "1,15.65,939"  # Missing fields
        
        with pytest.raises(ExaPlayMappingError) as exc_info:
            parse_status_response(csv_response)
        
        assert "Expected 5 CSV fields, got 3" in str(exc_info.value)
        assert exc_info.value.raw_response == csv_response
    
    def test_parse_status_invalid_state(self) -> None:
        """Test parsing status with invalid state value."""
        csv_response = "5,15.65,939,2,300.0"  # Invalid state 5
        
        with pytest.raises(ExaPlayMappingError) as exc_info:
            parse_status_response(csv_response)
        
        assert "Invalid state value: 5" in str(exc_info.value)
    
    def test_parse_status_invalid_numeric_fields(self) -> None:
        """Test parsing status with invalid numeric values."""
        csv_response = "1,invalid,939,2,300.0"  # Invalid time
        
        with pytest.raises(ExaPlayMappingError) as exc_info:
            parse_status_response(csv_response)
        
        assert "Failed to parse numeric fields" in str(exc_info.value)
    
    def test_parse_status_negative_values(self) -> None:
        """Test parsing status with negative values (should log warning but not fail)."""
        csv_response = "1,-5.0,-100,-1,300.0"
        
        # Should parse successfully despite negative values
        status = parse_status_response(csv_response)
        
        assert status.state == PlaybackState.PLAYING
        assert status.time == -5.0
        assert status.frame == -100
        assert status.clipIndex == -1
        assert status.duration == 300.0


class TestVersionResponseMapping:
    """Test cases for version response parsing."""
    
    def test_parse_version_simple(self) -> None:
        """Test parsing simple version string."""
        response = "2.21.0.0"
        
        version = parse_version_response(response)
        
        assert version.exaplayVersion == "2.21.0.0"
    
    def test_parse_version_with_prefix(self) -> None:
        """Test parsing version with prefix."""
        response = "Version: 2.21.0.0"
        
        version = parse_version_response(response)
        
        assert version.exaplayVersion == "2.21.0.0"
    
    def test_parse_version_with_ver_prefix(self) -> None:
        """Test parsing version with 'ver:' prefix."""
        response = "ver: 2.21.0.0"
        
        version = parse_version_response(response)
        
        assert version.exaplayVersion == "2.21.0.0"
    
    def test_parse_version_with_whitespace(self) -> None:
        """Test parsing version with extra whitespace."""
        response = "  2.21.0.0  "
        
        version = parse_version_response(response)
        
        assert version.exaplayVersion == "2.21.0.0"
    
    def test_parse_version_empty(self) -> None:
        """Test parsing empty version response."""
        response = ""
        
        with pytest.raises(ExaPlayMappingError) as exc_info:
            parse_version_response(response)
        
        assert "Empty version response" in str(exc_info.value)
    
    def test_parse_version_unusual_format(self) -> None:
        """Test parsing version with unusual format (should still work)."""
        response = "ExaPlay-2.21.0.0-beta"
        
        version = parse_version_response(response)
        
        assert version.exaplayVersion == "ExaPlay-2.21.0.0-beta"


class TestVolumeResponseMapping:
    """Test cases for volume response parsing."""
    
    def test_parse_volume_simple(self) -> None:
        """Test parsing simple volume value."""
        response = "60"
        
        volume = parse_volume_response(response)
        
        assert volume == 60
    
    def test_parse_volume_with_prefix(self) -> None:
        """Test parsing volume with prefix."""
        response = "Volume: 75"
        
        volume = parse_volume_response(response)
        
        assert volume == 75
    
    def test_parse_volume_with_vol_prefix(self) -> None:
        """Test parsing volume with 'vol:' prefix."""
        response = "vol: 50"
        
        volume = parse_volume_response(response)
        
        assert volume == 50
    
    def test_parse_volume_with_whitespace(self) -> None:
        """Test parsing volume with extra whitespace."""
        response = "  85  "
        
        volume = parse_volume_response(response)
        
        assert volume == 85
    
    def test_parse_volume_boundary_values(self) -> None:
        """Test parsing volume boundary values."""
        # Minimum value
        volume_min = parse_volume_response("0")
        assert volume_min == 0
        
        # Maximum value
        volume_max = parse_volume_response("100")
        assert volume_max == 100
    
    def test_parse_volume_out_of_range(self) -> None:
        """Test parsing volume values outside valid range."""
        # Below minimum
        with pytest.raises(ExaPlayMappingError) as exc_info:
            parse_volume_response("-5")
        assert "out of valid range" in str(exc_info.value)
        
        # Above maximum
        with pytest.raises(ExaPlayMappingError) as exc_info:
            parse_volume_response("150")
        assert "out of valid range" in str(exc_info.value)
    
    def test_parse_volume_invalid_format(self) -> None:
        """Test parsing invalid volume format."""
        response = "invalid"
        
        with pytest.raises(ExaPlayMappingError) as exc_info:
            parse_volume_response(response)
        
        assert "Failed to parse volume as integer" in str(exc_info.value)
    
    def test_parse_volume_float_value(self) -> None:
        """Test parsing volume with decimal (should fail as volume is integer)."""
        response = "60.5"
        
        with pytest.raises(ExaPlayMappingError) as exc_info:
            parse_volume_response(response)
        
        assert "Failed to parse volume as integer" in str(exc_info.value)


class TestMappingErrorHandling:
    """Test cases for error handling in mapping functions."""
    
    def test_mapping_error_preserves_raw_response(self) -> None:
        """Test that mapping errors preserve the original response."""
        raw_response = "invalid,data,format"
        
        with pytest.raises(ExaPlayMappingError) as exc_info:
            parse_status_response(raw_response)
        
        assert exc_info.value.raw_response == raw_response
    
    def test_mapping_error_includes_context(self) -> None:
        """Test that mapping errors include helpful context."""
        raw_response = "1,2"  # Too few fields
        
        with pytest.raises(ExaPlayMappingError) as exc_info:
            parse_status_response(raw_response)
        
        error_msg = str(exc_info.value)
        assert "Expected 5 CSV fields" in error_msg
        assert "got 2" in error_msg
