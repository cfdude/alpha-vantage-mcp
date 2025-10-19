"""
Unit tests for MovingAverageRequest schema validation.

Tests cover:
- Parameter validation for each indicator_type
- Conditional requirements enforcement (standard, MAMA, VWAP)
- Invalid parameter combinations
- Edge cases and error messages
- Parameterized tests for efficiency
"""

import pytest
from pydantic import ValidationError

from src.tools.moving_average_schema import MovingAverageRequest


class TestStandardIndicators:
    """Test standard moving average indicators (SMA, EMA, WMA, DEMA, TEMA, TRIMA, KAMA, T3)."""

    # Parameterize test to cover all 8 standard indicators with one test function
    @pytest.mark.parametrize(
        "indicator_type",
        ["sma", "ema", "wma", "dema", "tema", "trima", "kama", "t3"],
    )
    def test_valid_standard_indicator_request(self, indicator_type):
        """Test valid request for standard indicators."""
        request = MovingAverageRequest(
            indicator_type=indicator_type,
            symbol="IBM",
            interval="daily",
            time_period=60,
            series_type="close",
        )
        assert request.indicator_type == indicator_type
        assert request.symbol == "IBM"
        assert request.interval == "daily"
        assert request.time_period == 60
        assert request.series_type == "close"

    @pytest.mark.parametrize(
        "indicator_type",
        ["sma", "ema", "wma", "dema", "tema", "trima", "kama", "t3"],
    )
    def test_standard_indicator_missing_time_period(self, indicator_type):
        """Test standard indicators fail without time_period."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="daily",
                series_type="close",
            )
        errors = exc_info.value.errors()
        assert any("time_period is required" in str(err) for err in errors)

    @pytest.mark.parametrize(
        "indicator_type",
        ["sma", "ema", "wma", "dema", "tema", "trima", "kama", "t3"],
    )
    def test_standard_indicator_missing_series_type(self, indicator_type):
        """Test standard indicators fail without series_type."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="daily",
                time_period=60,
            )
        errors = exc_info.value.errors()
        assert any("series_type is required" in str(err) for err in errors)

    @pytest.mark.parametrize(
        "indicator_type",
        ["sma", "ema", "wma", "dema", "tema", "trima", "kama", "t3"],
    )
    def test_standard_indicator_rejects_mama_params(self, indicator_type):
        """Test standard indicators reject MAMA-specific parameters."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="daily",
                time_period=60,
                series_type="close",
                fastlimit=0.01,  # Not valid for standard indicators
            )
        errors = exc_info.value.errors()
        assert any("not valid for" in str(err) for err in errors)

    @pytest.mark.parametrize(
        "indicator_type,interval,time_period,series_type",
        [
            ("sma", "5min", 20, "close"),
            ("ema", "15min", 50, "high"),
            ("wma", "30min", 100, "low"),
            ("dema", "60min", 200, "open"),
            ("tema", "daily", 10, "close"),
            ("trima", "weekly", 30, "close"),
            ("kama", "monthly", 40, "close"),
            ("t3", "daily", 5, "close"),
        ],
    )
    def test_standard_indicator_various_intervals(
        self, indicator_type, interval, time_period, series_type
    ):
        """Test standard indicators work with various intervals and parameters."""
        request = MovingAverageRequest(
            indicator_type=indicator_type,
            symbol="AAPL",
            interval=interval,
            time_period=time_period,
            series_type=series_type,
        )
        assert request.indicator_type == indicator_type
        assert request.interval == interval
        assert request.time_period == time_period
        assert request.series_type == series_type

    @pytest.mark.parametrize(
        "indicator_type",
        ["sma", "ema", "wma", "dema", "tema", "trima", "kama", "t3"],
    )
    def test_standard_indicator_with_month_intraday(self, indicator_type):
        """Test standard indicators accept month parameter for intraday intervals."""
        request = MovingAverageRequest(
            indicator_type=indicator_type,
            symbol="IBM",
            interval="15min",
            time_period=50,
            series_type="close",
            month="2024-01",
        )
        assert request.month == "2024-01"

    @pytest.mark.parametrize(
        "indicator_type",
        ["sma", "ema", "wma", "dema", "tema", "trima", "kama", "t3"],
    )
    def test_standard_indicator_rejects_month_for_daily(self, indicator_type):
        """Test standard indicators reject month parameter for non-intraday intervals."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="daily",
                time_period=60,
                series_type="close",
                month="2024-01",  # Only valid for intraday
            )
        errors = exc_info.value.errors()
        assert any("only applicable for intraday" in str(err) for err in errors)


class TestMAMA:
    """Test MAMA (MESA Adaptive Moving Average) indicator validation."""

    def test_valid_mama_request_with_defaults(self):
        """Test valid MAMA request using default fastlimit/slowlimit."""
        request = MovingAverageRequest(
            indicator_type="mama",
            symbol="IBM",
            interval="daily",
            series_type="close",
        )
        assert request.indicator_type == "mama"
        assert request.fastlimit == 0.01  # Default
        assert request.slowlimit == 0.01  # Default
        assert request.series_type == "close"

    def test_valid_mama_request_with_custom_limits(self):
        """Test valid MAMA request with custom fastlimit/slowlimit."""
        request = MovingAverageRequest(
            indicator_type="mama",
            symbol="AAPL",
            interval="daily",
            series_type="close",
            fastlimit=0.02,
            slowlimit=0.05,
        )
        assert request.fastlimit == 0.02
        assert request.slowlimit == 0.05

    def test_mama_missing_series_type(self):
        """Test MAMA fails without series_type."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type="mama",
                symbol="IBM",
                interval="daily",
            )
        errors = exc_info.value.errors()
        assert any("series_type is required" in str(err) for err in errors)

    def test_mama_rejects_time_period(self):
        """Test MAMA rejects time_period parameter."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type="mama",
                symbol="IBM",
                interval="daily",
                series_type="close",
                time_period=60,  # Not valid for MAMA
            )
        errors = exc_info.value.errors()
        assert any("time_period is not valid" in str(err) for err in errors)

    def test_mama_fastlimit_boundary_values(self):
        """Test MAMA fastlimit accepts valid boundary values."""
        # Min value
        request = MovingAverageRequest(
            indicator_type="mama",
            symbol="IBM",
            interval="daily",
            series_type="close",
            fastlimit=0.0,
        )
        assert request.fastlimit == 0.0

        # Max value
        request = MovingAverageRequest(
            indicator_type="mama",
            symbol="IBM",
            interval="daily",
            series_type="close",
            fastlimit=1.0,
        )
        assert request.fastlimit == 1.0

    def test_mama_fastlimit_out_of_range(self):
        """Test MAMA fastlimit rejects values outside 0.0-1.0 range."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type="mama",
                symbol="IBM",
                interval="daily",
                series_type="close",
                fastlimit=1.5,  # Out of range
            )
        # Pydantic will catch this with ge/le validation
        assert exc_info.value is not None

    def test_mama_slowlimit_out_of_range(self):
        """Test MAMA slowlimit rejects values outside 0.0-1.0 range."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type="mama",
                symbol="IBM",
                interval="daily",
                series_type="close",
                slowlimit=-0.1,  # Out of range
            )
        # Pydantic will catch this with ge/le validation
        assert exc_info.value is not None

    def test_mama_with_month_intraday(self):
        """Test MAMA accepts month parameter for intraday intervals."""
        request = MovingAverageRequest(
            indicator_type="mama",
            symbol="IBM",
            interval="5min",
            series_type="close",
            month="2024-01",
        )
        assert request.month == "2024-01"


class TestVWAP:
    """Test VWAP (Volume Weighted Average Price) indicator validation."""

    def test_valid_vwap_request(self):
        """Test valid VWAP request."""
        request = MovingAverageRequest(
            indicator_type="vwap",
            symbol="IBM",
            interval="5min",
        )
        assert request.indicator_type == "vwap"
        assert request.symbol == "IBM"
        assert request.interval == "5min"

    @pytest.mark.parametrize("interval", ["1min", "5min", "15min", "30min", "60min"])
    def test_vwap_valid_intraday_intervals(self, interval):
        """Test VWAP accepts all valid intraday intervals."""
        request = MovingAverageRequest(
            indicator_type="vwap",
            symbol="IBM",
            interval=interval,
        )
        assert request.interval == interval

    @pytest.mark.parametrize("interval", ["daily", "weekly", "monthly"])
    def test_vwap_rejects_non_intraday_intervals(self, interval):
        """Test VWAP rejects non-intraday intervals."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type="vwap",
                symbol="IBM",
                interval=interval,
            )
        errors = exc_info.value.errors()
        assert any("only supports intraday" in str(err) for err in errors)

    def test_vwap_rejects_time_period(self):
        """Test VWAP rejects time_period parameter."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type="vwap",
                symbol="IBM",
                interval="5min",
                time_period=60,  # Not valid for VWAP
            )
        errors = exc_info.value.errors()
        assert any("time_period is not valid" in str(err) for err in errors)

    def test_vwap_rejects_series_type(self):
        """Test VWAP rejects series_type parameter."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type="vwap",
                symbol="IBM",
                interval="5min",
                series_type="close",  # Not valid for VWAP
            )
        errors = exc_info.value.errors()
        assert any("series_type is not valid" in str(err) for err in errors)

    def test_vwap_rejects_mama_params(self):
        """Test VWAP rejects MAMA-specific parameters."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type="vwap",
                symbol="IBM",
                interval="5min",
                fastlimit=0.01,  # Not valid for VWAP
            )
        errors = exc_info.value.errors()
        assert any("not valid for" in str(err) for err in errors)

    def test_vwap_with_month(self):
        """Test VWAP accepts month parameter for intraday intervals."""
        request = MovingAverageRequest(
            indicator_type="vwap",
            symbol="IBM",
            interval="15min",
            month="2024-01",
        )
        assert request.month == "2024-01"


class TestMonthValidation:
    """Test month parameter validation across all indicators."""

    def test_valid_month_format(self):
        """Test valid month format is accepted."""
        request = MovingAverageRequest(
            indicator_type="sma",
            symbol="IBM",
            interval="5min",
            time_period=60,
            series_type="close",
            month="2024-01",
        )
        assert request.month == "2024-01"

    def test_invalid_month_format_slash(self):
        """Test invalid month format with slashes is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type="sma",
                symbol="IBM",
                interval="5min",
                time_period=60,
                series_type="close",
                month="2024/01",  # Wrong format
            )
        errors = exc_info.value.errors()
        assert any("YYYY-MM format" in str(err) for err in errors)

    def test_invalid_month_format_no_dash(self):
        """Test invalid month format without dash is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type="sma",
                symbol="IBM",
                interval="5min",
                time_period=60,
                series_type="close",
                month="202401",  # Missing dash
            )
        errors = exc_info.value.errors()
        assert any("YYYY-MM format" in str(err) for err in errors)

    def test_month_year_before_2000(self):
        """Test month year before 2000 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type="sma",
                symbol="IBM",
                interval="5min",
                time_period=60,
                series_type="close",
                month="1999-12",
            )
        errors = exc_info.value.errors()
        assert any("2000 or later" in str(err) for err in errors)

    def test_month_invalid_month_number(self):
        """Test invalid month number (13) is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type="sma",
                symbol="IBM",
                interval="5min",
                time_period=60,
                series_type="close",
                month="2024-13",  # Invalid month
            )
        errors = exc_info.value.errors()
        assert any("between 01 and 12" in str(err) for err in errors)

    def test_month_zero_month_number(self):
        """Test month number 00 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type="sma",
                symbol="IBM",
                interval="5min",
                time_period=60,
                series_type="close",
                month="2024-00",  # Invalid month
            )
        errors = exc_info.value.errors()
        assert any("between 01 and 12" in str(err) for err in errors)


class TestOutputControl:
    """Test output control parameters (force_inline, force_file)."""

    def test_force_inline_and_force_file_mutually_exclusive(self):
        """Test force_inline and force_file cannot both be True."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type="sma",
                symbol="IBM",
                interval="daily",
                time_period=60,
                series_type="close",
                force_inline=True,
                force_file=True,
            )
        errors = exc_info.value.errors()
        assert any("mutually exclusive" in str(err) for err in errors)

    def test_force_inline_only(self):
        """Test force_inline can be set alone."""
        request = MovingAverageRequest(
            indicator_type="sma",
            symbol="IBM",
            interval="daily",
            time_period=60,
            series_type="close",
            force_inline=True,
        )
        assert request.force_inline is True
        assert request.force_file is False

    def test_force_file_only(self):
        """Test force_file can be set alone."""
        request = MovingAverageRequest(
            indicator_type="sma",
            symbol="IBM",
            interval="daily",
            time_period=60,
            series_type="close",
            force_file=True,
        )
        assert request.force_file is True
        assert request.force_inline is False


class TestDatatypeValidation:
    """Test datatype parameter validation."""

    @pytest.mark.parametrize("datatype", ["json", "csv"])
    def test_valid_datatype(self, datatype):
        """Test valid datatype values are accepted."""
        request = MovingAverageRequest(
            indicator_type="sma",
            symbol="IBM",
            interval="daily",
            time_period=60,
            series_type="close",
            datatype=datatype,
        )
        assert request.datatype == datatype

    def test_invalid_datatype(self):
        """Test invalid datatype is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MovingAverageRequest(
                indicator_type="sma",
                symbol="IBM",
                interval="daily",
                time_period=60,
                series_type="close",
                datatype="xml",  # Not valid
            )
        # Pydantic will catch this as it's not in the Literal
        assert exc_info.value is not None

    def test_default_datatype(self):
        """Test datatype defaults to csv."""
        request = MovingAverageRequest(
            indicator_type="sma",
            symbol="IBM",
            interval="daily",
            time_period=60,
            series_type="close",
        )
        assert request.datatype == "csv"
