"""
Unit tests for TrendRequest schema validation.

Tests cover:
- Parameter validation for each indicator_type
- All 7 trend indicators
- Month parameter validation
- Edge cases and error messages
- Parameterized tests for efficiency
"""

import pytest
from pydantic import ValidationError

from src.tools.trend_schema import TrendRequest


class TestTrendIndicators:
    """Test all 7 trend indicators (AROON, AROONOSC, DX, MINUS_DI, PLUS_DI, MINUS_DM, PLUS_DM)."""

    @pytest.mark.parametrize(
        "indicator_type",
        ["aroon", "aroonosc", "dx", "minus_di", "plus_di", "minus_dm", "plus_dm"],
    )
    def test_valid_trend_indicator_request(self, indicator_type):
        """Test valid request for all trend indicators."""
        request = TrendRequest(
            indicator_type=indicator_type,
            symbol="IBM",
            interval="daily",
            time_period=14,
        )
        assert request.indicator_type == indicator_type
        assert request.symbol == "IBM"
        assert request.interval == "daily"
        assert request.time_period == 14

    @pytest.mark.parametrize(
        "indicator_type",
        ["aroon", "aroonosc", "dx", "minus_di", "plus_di", "minus_dm", "plus_dm"],
    )
    def test_trend_indicator_missing_time_period(self, indicator_type):
        """Test trend indicators fail without time_period."""
        with pytest.raises(ValidationError) as exc_info:
            TrendRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="daily",
            )
        errors = exc_info.value.errors()
        assert any("time_period" in str(err) for err in errors)

    @pytest.mark.parametrize(
        "indicator_type,interval,time_period",
        [
            ("aroon", "5min", 14),
            ("aroonosc", "15min", 25),
            ("dx", "30min", 10),
            ("minus_di", "60min", 20),
            ("plus_di", "daily", 14),
            ("minus_dm", "weekly", 30),
            ("plus_dm", "monthly", 40),
        ],
    )
    def test_trend_indicator_various_intervals(self, indicator_type, interval, time_period):
        """Test trend indicators with various intervals."""
        request = TrendRequest(
            indicator_type=indicator_type,
            symbol="AAPL",
            interval=interval,
            time_period=time_period,
        )
        assert request.interval == interval
        assert request.time_period == time_period


class TestMonthParameter:
    """Test month parameter validation."""

    def test_valid_month_format(self):
        """Test valid month format (YYYY-MM)."""
        request = TrendRequest(
            indicator_type="aroon",
            symbol="IBM",
            interval="5min",
            time_period=14,
            month="2024-01",
        )
        assert request.month == "2024-01"

    def test_month_only_for_intraday(self):
        """Test month parameter rejected for non-intraday intervals."""
        with pytest.raises(ValidationError) as exc_info:
            TrendRequest(
                indicator_type="dx",
                symbol="IBM",
                interval="daily",
                time_period=14,
                month="2024-01",
            )
        assert "month parameter is only applicable for intraday intervals" in str(exc_info.value)

    def test_invalid_month_format(self):
        """Test invalid month format."""
        with pytest.raises(ValidationError) as exc_info:
            TrendRequest(
                indicator_type="aroon",
                symbol="IBM",
                interval="5min",
                time_period=14,
                month="2024/01",  # Should use dash, not slash
            )
        assert "YYYY-MM" in str(exc_info.value)

    def test_month_before_2000(self):
        """Test month year before 2000 rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TrendRequest(
                indicator_type="aroon",
                symbol="IBM",
                interval="5min",
                time_period=14,
                month="1999-12",
            )
        assert "2000 or later" in str(exc_info.value)

    def test_invalid_month_number(self):
        """Test invalid month number rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TrendRequest(
                indicator_type="aroon",
                symbol="IBM",
                interval="5min",
                time_period=14,
                month="2024-13",  # Month must be 01-12
            )
        assert "between 01 and 12" in str(exc_info.value)


class TestOutputParameters:
    """Test output control parameters."""

    def test_force_inline(self):
        """Test force_inline parameter."""
        request = TrendRequest(
            indicator_type="dx",
            symbol="IBM",
            interval="daily",
            time_period=14,
            force_inline=True,
        )
        assert request.force_inline is True
        assert request.force_file is False

    def test_force_file(self):
        """Test force_file parameter."""
        request = TrendRequest(
            indicator_type="dx",
            symbol="IBM",
            interval="daily",
            time_period=14,
            force_file=True,
        )
        assert request.force_file is True
        assert request.force_inline is False

    def test_force_inline_and_force_file_mutually_exclusive(self):
        """Test force_inline and force_file are mutually exclusive."""
        with pytest.raises(ValidationError) as exc_info:
            TrendRequest(
                indicator_type="dx",
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
        request = TrendRequest(
            indicator_type="aroon",
            symbol="IBM",
            interval="daily",
            time_period=14,
            datatype=datatype,
        )
        assert request.datatype == datatype

    def test_default_datatype(self):
        """Test default datatype is csv."""
        request = TrendRequest(
            indicator_type="aroon",
            symbol="IBM",
            interval="daily",
            time_period=14,
        )
        assert request.datatype == "csv"


class TestSymbolValidation:
    """Test symbol parameter validation."""

    @pytest.mark.parametrize("symbol", ["IBM", "AAPL", "MSFT", "GOOGL", "TSLA"])
    def test_various_symbols(self, symbol):
        """Test various valid symbols."""
        request = TrendRequest(
            indicator_type="dx",
            symbol=symbol,
            interval="daily",
            time_period=14,
        )
        assert request.symbol == symbol

    def test_symbol_required(self):
        """Test symbol is required."""
        with pytest.raises(ValidationError) as exc_info:
            TrendRequest(
                indicator_type="dx",
                interval="daily",
                time_period=14,
            )
        errors = exc_info.value.errors()
        assert any("symbol" in str(err) for err in errors)


class TestTimePeriodValidation:
    """Test time_period parameter validation."""

    @pytest.mark.parametrize("time_period", [1, 10, 14, 20, 50, 100, 200])
    def test_valid_time_periods(self, time_period):
        """Test various valid time_period values."""
        request = TrendRequest(
            indicator_type="aroon",
            symbol="IBM",
            interval="daily",
            time_period=time_period,
        )
        assert request.time_period == time_period

    def test_time_period_must_be_positive(self):
        """Test time_period must be >= 1."""
        with pytest.raises(ValidationError) as exc_info:
            TrendRequest(
                indicator_type="dx",
                symbol="IBM",
                interval="daily",
                time_period=0,
            )
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_negative_time_period_rejected(self):
        """Test negative time_period rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TrendRequest(
                indicator_type="dx",
                symbol="IBM",
                interval="daily",
                time_period=-5,
            )
        assert "greater than or equal to 1" in str(exc_info.value)
