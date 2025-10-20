"""
Unit tests for VolumeRequest schema validation.

Tests cover:
- Parameter validation for each indicator_type
- All 4 volume indicators (AD, ADOSC, OBV, MFI)
- ADOSC-specific parameters (fastperiod, slowperiod)
- Edge cases and error messages
- Parameterized tests for efficiency
"""

import pytest
from pydantic import ValidationError

from src.tools.volume_schema import VolumeRequest


class TestMFIIndicator:
    """Test MFI (Money Flow Index) indicator - requires time_period."""

    def test_valid_mfi_request(self):
        """Test valid MFI request."""
        request = VolumeRequest(
            indicator_type="mfi",
            symbol="IBM",
            interval="daily",
            time_period=14,
        )
        assert request.indicator_type == "mfi"
        assert request.time_period == 14

    def test_mfi_missing_time_period(self):
        """Test MFI fails without time_period."""
        with pytest.raises(ValidationError) as exc_info:
            VolumeRequest(
                indicator_type="mfi",
                symbol="IBM",
                interval="daily",
            )
        assert "time_period is required" in str(exc_info.value)

    def test_mfi_rejects_adosc_params(self):
        """Test MFI rejects ADOSC parameters."""
        with pytest.raises(ValidationError) as exc_info:
            VolumeRequest(
                indicator_type="mfi",
                symbol="IBM",
                interval="daily",
                time_period=14,
                fastperiod=3,  # Invalid for MFI
            )
        assert "not valid for" in str(exc_info.value)

    @pytest.mark.parametrize("time_period", [10, 14, 20, 30])
    def test_mfi_various_time_periods(self, time_period):
        """Test MFI with various time_period values."""
        request = VolumeRequest(
            indicator_type="mfi",
            symbol="IBM",
            interval="daily",
            time_period=time_period,
        )
        assert request.time_period == time_period


class TestADOSCIndicator:
    """Test ADOSC (Chaikin A/D Oscillator) indicator - requires fastperiod, slowperiod."""

    def test_valid_adosc_request(self):
        """Test valid ADOSC request."""
        request = VolumeRequest(
            indicator_type="adosc",
            symbol="IBM",
            interval="daily",
            fastperiod=3,
            slowperiod=10,
        )
        assert request.indicator_type == "adosc"
        assert request.fastperiod == 3
        assert request.slowperiod == 10

    def test_adosc_defaults(self):
        """Test ADOSC sets default values."""
        request = VolumeRequest(
            indicator_type="adosc",
            symbol="IBM",
            interval="daily",
        )
        assert request.fastperiod == 3  # Default
        assert request.slowperiod == 10  # Default

    def test_adosc_rejects_time_period(self):
        """Test ADOSC rejects time_period parameter."""
        with pytest.raises(ValidationError) as exc_info:
            VolumeRequest(
                indicator_type="adosc",
                symbol="IBM",
                interval="daily",
                time_period=14,  # Invalid for ADOSC
            )
        assert "not valid for" in str(exc_info.value)

    @pytest.mark.parametrize(
        "fastperiod,slowperiod",
        [(2, 8), (3, 10), (5, 15), (7, 20)],
    )
    def test_adosc_various_periods(self, fastperiod, slowperiod):
        """Test ADOSC with various period combinations."""
        request = VolumeRequest(
            indicator_type="adosc",
            symbol="IBM",
            interval="daily",
            fastperiod=fastperiod,
            slowperiod=slowperiod,
        )
        assert request.fastperiod == fastperiod
        assert request.slowperiod == slowperiod


class TestADAndOBVIndicators:
    """Test AD and OBV indicators - no additional params."""

    @pytest.mark.parametrize("indicator_type", ["ad", "obv"])
    def test_valid_ad_obv_request(self, indicator_type):
        """Test valid request for AD and OBV."""
        request = VolumeRequest(
            indicator_type=indicator_type,
            symbol="IBM",
            interval="daily",
        )
        assert request.indicator_type == indicator_type

    @pytest.mark.parametrize("indicator_type", ["ad", "obv"])
    def test_ad_obv_reject_time_period(self, indicator_type):
        """Test AD and OBV reject time_period."""
        with pytest.raises(ValidationError) as exc_info:
            VolumeRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="daily",
                time_period=14,  # Invalid for AD/OBV
            )
        assert "not valid for" in str(exc_info.value)

    @pytest.mark.parametrize("indicator_type", ["ad", "obv"])
    def test_ad_obv_reject_adosc_params(self, indicator_type):
        """Test AD and OBV reject ADOSC parameters."""
        with pytest.raises(ValidationError) as exc_info:
            VolumeRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="daily",
                fastperiod=3,  # Invalid for AD/OBV
            )
        assert "not valid for" in str(exc_info.value)

    @pytest.mark.parametrize(
        "indicator_type,interval",
        [
            ("ad", "5min"),
            ("ad", "daily"),
            ("obv", "15min"),
            ("obv", "weekly"),
        ],
    )
    def test_ad_obv_various_intervals(self, indicator_type, interval):
        """Test AD and OBV with various intervals."""
        request = VolumeRequest(
            indicator_type=indicator_type,
            symbol="AAPL",
            interval=interval,
        )
        assert request.interval == interval


class TestMonthParameter:
    """Test month parameter validation."""

    @pytest.mark.parametrize("indicator_type", ["mfi", "adosc", "ad", "obv"])
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
        if indicator_type == "mfi":
            params["time_period"] = 14

        with pytest.raises(ValidationError) as exc_info:
            VolumeRequest(**params)
        assert "month parameter is only applicable for intraday intervals" in str(exc_info.value)

    def test_valid_month_with_intraday(self):
        """Test valid month parameter with intraday interval."""
        request = VolumeRequest(
            indicator_type="mfi",
            symbol="IBM",
            interval="5min",
            time_period=14,
            month="2024-01",
        )
        assert request.month == "2024-01"


class TestOutputParameters:
    """Test output control parameters."""

    def test_force_inline(self):
        """Test force_inline parameter."""
        request = VolumeRequest(
            indicator_type="mfi",
            symbol="IBM",
            interval="daily",
            time_period=14,
            force_inline=True,
        )
        assert request.force_inline is True

    def test_force_inline_and_force_file_mutually_exclusive(self):
        """Test force_inline and force_file are mutually exclusive."""
        with pytest.raises(ValidationError) as exc_info:
            VolumeRequest(
                indicator_type="mfi",
                symbol="IBM",
                interval="daily",
                time_period=14,
                force_inline=True,
                force_file=True,
            )
        assert "mutually exclusive" in str(exc_info.value)


class TestDataTypeParameter:
    """Test datatype parameter validation."""

    @pytest.mark.parametrize("datatype", ["json", "csv"])
    def test_valid_datatype(self, datatype):
        """Test valid datatype values."""
        request = VolumeRequest(
            indicator_type="obv",
            symbol="IBM",
            interval="daily",
            datatype=datatype,
        )
        assert request.datatype == datatype

    def test_default_datatype(self):
        """Test default datatype is csv."""
        request = VolumeRequest(
            indicator_type="obv",
            symbol="IBM",
            interval="daily",
        )
        assert request.datatype == "csv"


class TestSymbolValidation:
    """Test symbol parameter validation."""

    @pytest.mark.parametrize("symbol", ["IBM", "AAPL", "MSFT", "GOOGL"])
    def test_various_symbols(self, symbol):
        """Test various valid symbols."""
        request = VolumeRequest(
            indicator_type="ad",
            symbol=symbol,
            interval="daily",
        )
        assert request.symbol == symbol

    def test_symbol_required(self):
        """Test symbol is required."""
        with pytest.raises(ValidationError) as exc_info:
            VolumeRequest(
                indicator_type="obv",
                interval="daily",
            )
        errors = exc_info.value.errors()
        assert any("symbol" in str(err) for err in errors)
