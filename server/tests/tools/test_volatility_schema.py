"""
Unit tests for VolatilityRequest schema validation.

Tests cover:
- Parameter validation for each indicator_type
- All 7 volatility indicators (BBANDS, TRANGE, ATR, NATR, MIDPOINT, MIDPRICE, SAR)
- Complex BBANDS parameters (nbdevup, nbdevdn, matype)
- SAR-specific parameters (acceleration, maximum)
- Edge cases and error messages
- Parameterized tests for efficiency
"""

import pytest
from pydantic import ValidationError

from src.tools.volatility_schema import VolatilityRequest


class TestBBANDSIndicator:
    """Test BBANDS (Bollinger Bands) indicator - most complex volatility indicator."""

    def test_valid_bbands_request(self):
        """Test valid BBANDS request with all parameters."""
        request = VolatilityRequest(
            indicator_type="bbands",
            symbol="IBM",
            interval="daily",
            time_period=20,
            series_type="close",
            nbdevup=2,
            nbdevdn=2,
            matype=0,
        )
        assert request.indicator_type == "bbands"
        assert request.time_period == 20
        assert request.series_type == "close"
        assert request.nbdevup == 2
        assert request.nbdevdn == 2
        assert request.matype == 0

    def test_bbands_defaults(self):
        """Test BBANDS sets default values for optional params."""
        request = VolatilityRequest(
            indicator_type="bbands",
            symbol="IBM",
            interval="daily",
            time_period=20,
            series_type="close",
        )
        assert request.nbdevup == 2  # Default
        assert request.nbdevdn == 2  # Default
        assert request.matype == 0  # Default

    def test_bbands_missing_time_period(self):
        """Test BBANDS fails without time_period."""
        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(
                indicator_type="bbands",
                symbol="IBM",
                interval="daily",
                series_type="close",
            )
        assert "time_period is required" in str(exc_info.value)

    def test_bbands_missing_series_type(self):
        """Test BBANDS fails without series_type."""
        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(
                indicator_type="bbands",
                symbol="IBM",
                interval="daily",
                time_period=20,
            )
        assert "series_type is required" in str(exc_info.value)

    def test_bbands_rejects_sar_params(self):
        """Test BBANDS rejects SAR-specific parameters."""
        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(
                indicator_type="bbands",
                symbol="IBM",
                interval="daily",
                time_period=20,
                series_type="close",
                acceleration=0.02,  # Invalid for BBANDS
            )
        assert "not valid for" in str(exc_info.value)

    @pytest.mark.parametrize("matype", [0, 1, 2, 3, 4, 5, 6, 7, 8])
    def test_bbands_various_matypes(self, matype):
        """Test BBANDS with all valid matype values (0-8)."""
        request = VolatilityRequest(
            indicator_type="bbands",
            symbol="IBM",
            interval="daily",
            time_period=20,
            series_type="close",
            matype=matype,
        )
        assert request.matype == matype


class TestSARIndicator:
    """Test SAR (Parabolic SAR) indicator - unique acceleration/maximum params."""

    def test_valid_sar_request(self):
        """Test valid SAR request."""
        request = VolatilityRequest(
            indicator_type="sar",
            symbol="IBM",
            interval="daily",
            acceleration=0.02,
            maximum=0.20,
        )
        assert request.indicator_type == "sar"
        assert request.acceleration == 0.02
        assert request.maximum == 0.20

    def test_sar_defaults(self):
        """Test SAR sets default values."""
        request = VolatilityRequest(
            indicator_type="sar",
            symbol="IBM",
            interval="daily",
        )
        assert request.acceleration == 0.01  # Default
        assert request.maximum == 0.20  # Default

    def test_sar_rejects_time_period(self):
        """Test SAR rejects time_period parameter."""
        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(
                indicator_type="sar",
                symbol="IBM",
                interval="daily",
                time_period=14,  # Invalid for SAR
            )
        assert "not valid for" in str(exc_info.value)

    def test_sar_rejects_series_type(self):
        """Test SAR rejects series_type parameter."""
        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(
                indicator_type="sar",
                symbol="IBM",
                interval="daily",
                series_type="close",  # Invalid for SAR
            )
        assert "not valid for" in str(exc_info.value)

    def test_sar_acceleration_range(self):
        """Test SAR acceleration must be 0.0-1.0."""
        # Valid values
        request = VolatilityRequest(
            indicator_type="sar",
            symbol="IBM",
            interval="daily",
            acceleration=0.0,
            maximum=0.20,
        )
        assert request.acceleration == 0.0

        request = VolatilityRequest(
            indicator_type="sar",
            symbol="IBM",
            interval="daily",
            acceleration=1.0,
            maximum=0.20,
        )
        assert request.acceleration == 1.0

        # Invalid values
        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(
                indicator_type="sar",
                symbol="IBM",
                interval="daily",
                acceleration=1.5,  # Too high
                maximum=0.20,
            )
        assert "less than or equal to 1" in str(exc_info.value)


class TestATRIndicators:
    """Test ATR, NATR, MIDPRICE - simple time_period indicators."""

    @pytest.mark.parametrize("indicator_type", ["atr", "natr", "midprice"])
    def test_valid_atr_family_request(self, indicator_type):
        """Test valid request for ATR family indicators."""
        request = VolatilityRequest(
            indicator_type=indicator_type,
            symbol="IBM",
            interval="daily",
            time_period=14,
        )
        assert request.indicator_type == indicator_type
        assert request.time_period == 14

    @pytest.mark.parametrize("indicator_type", ["atr", "natr", "midprice"])
    def test_atr_family_missing_time_period(self, indicator_type):
        """Test ATR family fails without time_period."""
        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="daily",
            )
        assert "time_period is required" in str(exc_info.value)

    @pytest.mark.parametrize("indicator_type", ["atr", "natr", "midprice"])
    def test_atr_family_rejects_series_type(self, indicator_type):
        """Test ATR family rejects series_type."""
        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="daily",
                time_period=14,
                series_type="close",  # Invalid for ATR family
            )
        assert "not valid for" in str(exc_info.value)

    @pytest.mark.parametrize("indicator_type", ["atr", "natr", "midprice"])
    def test_atr_family_rejects_bbands_params(self, indicator_type):
        """Test ATR family rejects BBANDS parameters."""
        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="daily",
                time_period=14,
                nbdevup=2,  # Invalid for ATR family
            )
        assert "not valid for" in str(exc_info.value)


class TestMIDPOINTIndicator:
    """Test MIDPOINT indicator - requires time_period + series_type."""

    def test_valid_midpoint_request(self):
        """Test valid MIDPOINT request."""
        request = VolatilityRequest(
            indicator_type="midpoint",
            symbol="IBM",
            interval="daily",
            time_period=14,
            series_type="close",
        )
        assert request.indicator_type == "midpoint"
        assert request.time_period == 14
        assert request.series_type == "close"

    def test_midpoint_missing_time_period(self):
        """Test MIDPOINT fails without time_period."""
        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(
                indicator_type="midpoint",
                symbol="IBM",
                interval="daily",
                series_type="close",
            )
        assert "time_period is required" in str(exc_info.value)

    def test_midpoint_missing_series_type(self):
        """Test MIDPOINT fails without series_type."""
        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(
                indicator_type="midpoint",
                symbol="IBM",
                interval="daily",
                time_period=14,
            )
        assert "series_type is required" in str(exc_info.value)

    def test_midpoint_rejects_bbands_params(self):
        """Test MIDPOINT rejects BBANDS parameters."""
        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(
                indicator_type="midpoint",
                symbol="IBM",
                interval="daily",
                time_period=14,
                series_type="close",
                matype=1,  # Invalid for MIDPOINT
            )
        assert "not valid for" in str(exc_info.value)


class TestTRANGEIndicator:
    """Test TRANGE indicator - no additional params."""

    def test_valid_trange_request(self):
        """Test valid TRANGE request."""
        request = VolatilityRequest(
            indicator_type="trange",
            symbol="IBM",
            interval="daily",
        )
        assert request.indicator_type == "trange"

    def test_trange_rejects_time_period(self):
        """Test TRANGE rejects time_period."""
        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(
                indicator_type="trange",
                symbol="IBM",
                interval="daily",
                time_period=14,  # Invalid for TRANGE
            )
        assert "not valid for" in str(exc_info.value)

    def test_trange_rejects_series_type(self):
        """Test TRANGE rejects series_type."""
        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(
                indicator_type="trange",
                symbol="IBM",
                interval="daily",
                series_type="close",  # Invalid for TRANGE
            )
        assert "not valid for" in str(exc_info.value)

    def test_trange_rejects_all_optional_params(self):
        """Test TRANGE rejects all optional parameters."""
        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(
                indicator_type="trange",
                symbol="IBM",
                interval="daily",
                acceleration=0.02,  # Invalid for TRANGE
            )
        assert "not valid for" in str(exc_info.value)


class TestMonthParameter:
    """Test month parameter validation."""

    @pytest.mark.parametrize("indicator_type", ["bbands", "atr", "sar", "trange"])
    def test_month_only_for_intraday(self, indicator_type):
        """Test month parameter rejected for non-intraday intervals."""
        # Build params based on indicator type
        params = {
            "indicator_type": indicator_type,
            "symbol": "IBM",
            "interval": "daily",
            "month": "2024-01",
        }

        # Add required params based on indicator
        if indicator_type == "bbands":
            params["time_period"] = 20
            params["series_type"] = "close"
        elif indicator_type == "atr":
            params["time_period"] = 14

        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(**params)
        assert "month parameter is only applicable for intraday intervals" in str(exc_info.value)


class TestOutputParameters:
    """Test output control parameters."""

    def test_force_inline_and_force_file_mutually_exclusive(self):
        """Test force_inline and force_file are mutually exclusive."""
        with pytest.raises(ValidationError) as exc_info:
            VolatilityRequest(
                indicator_type="atr",
                symbol="IBM",
                interval="daily",
                time_period=14,
                force_inline=True,
                force_file=True,
            )
        assert "mutually exclusive" in str(exc_info.value)
