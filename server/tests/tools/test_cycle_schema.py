"""
Unit tests for CycleRequest schema validation.

Tests cover:
- Parameter validation for all 6 Hilbert Transform indicators
- HT_TRENDLINE, HT_SINE, HT_TRENDMODE, HT_DCPERIOD, HT_DCPHASE, HT_PHASOR
- All indicators use same parameters (symbol, interval, series_type)
- Month parameter validation
- Edge cases and error messages
- Parameterized tests for efficiency
"""

import pytest
from pydantic import ValidationError

from src.tools.cycle_schema import CycleRequest


class TestCycleIndicators:
    """Test all 6 Hilbert Transform indicators."""

    @pytest.mark.parametrize(
        "indicator_type",
        ["ht_trendline", "ht_sine", "ht_trendmode", "ht_dcperiod", "ht_dcphase", "ht_phasor"],
    )
    def test_valid_cycle_indicator_request(self, indicator_type):
        """Test valid request for all cycle indicators."""
        request = CycleRequest(
            indicator_type=indicator_type,
            symbol="IBM",
            interval="daily",
            series_type="close",
        )
        assert request.indicator_type == indicator_type
        assert request.symbol == "IBM"
        assert request.interval == "daily"
        assert request.series_type == "close"

    @pytest.mark.parametrize(
        "indicator_type",
        ["ht_trendline", "ht_sine", "ht_trendmode", "ht_dcperiod", "ht_dcphase", "ht_phasor"],
    )
    def test_cycle_indicator_missing_series_type(self, indicator_type):
        """Test cycle indicators fail without series_type."""
        with pytest.raises(ValidationError) as exc_info:
            CycleRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="daily",
            )
        errors = exc_info.value.errors()
        assert any("series_type" in str(err) for err in errors)

    @pytest.mark.parametrize(
        "indicator_type,interval,series_type",
        [
            ("ht_trendline", "5min", "close"),
            ("ht_sine", "15min", "high"),
            ("ht_trendmode", "30min", "low"),
            ("ht_dcperiod", "60min", "open"),
            ("ht_dcphase", "daily", "close"),
            ("ht_phasor", "weekly", "high"),
        ],
    )
    def test_cycle_indicator_various_intervals(self, indicator_type, interval, series_type):
        """Test cycle indicators with various intervals and series types."""
        request = CycleRequest(
            indicator_type=indicator_type,
            symbol="AAPL",
            interval=interval,
            series_type=series_type,
        )
        assert request.interval == interval
        assert request.series_type == series_type


class TestSeriesTypeParameter:
    """Test series_type parameter validation."""

    @pytest.mark.parametrize("series_type", ["close", "open", "high", "low"])
    def test_valid_series_types(self, series_type):
        """Test all valid series_type values."""
        request = CycleRequest(
            indicator_type="ht_trendline",
            symbol="IBM",
            interval="daily",
            series_type=series_type,
        )
        assert request.series_type == series_type

    def test_series_type_required(self):
        """Test series_type is required for all cycle indicators."""
        with pytest.raises(ValidationError) as exc_info:
            CycleRequest(
                indicator_type="ht_dcperiod",
                symbol="IBM",
                interval="daily",
            )
        errors = exc_info.value.errors()
        assert any("series_type" in str(err) for err in errors)


class TestMonthParameter:
    """Test month parameter validation."""

    def test_valid_month_format(self):
        """Test valid month format (YYYY-MM)."""
        request = CycleRequest(
            indicator_type="ht_trendline",
            symbol="IBM",
            interval="5min",
            series_type="close",
            month="2024-01",
        )
        assert request.month == "2024-01"

    def test_month_only_for_intraday(self):
        """Test month parameter rejected for non-intraday intervals."""
        with pytest.raises(ValidationError) as exc_info:
            CycleRequest(
                indicator_type="ht_sine",
                symbol="IBM",
                interval="daily",
                series_type="close",
                month="2024-01",
            )
        assert "month parameter is only applicable for intraday intervals" in str(exc_info.value)

    @pytest.mark.parametrize("interval", ["1min", "5min", "15min", "30min", "60min"])
    def test_month_valid_for_all_intraday_intervals(self, interval):
        """Test month parameter valid for all intraday intervals."""
        request = CycleRequest(
            indicator_type="ht_dcphase",
            symbol="IBM",
            interval=interval,
            series_type="close",
            month="2024-01",
        )
        assert request.month == "2024-01"

    def test_invalid_month_format(self):
        """Test invalid month format."""
        with pytest.raises(ValidationError) as exc_info:
            CycleRequest(
                indicator_type="ht_trendline",
                symbol="IBM",
                interval="5min",
                series_type="close",
                month="2024/01",  # Should use dash, not slash
            )
        assert "YYYY-MM" in str(exc_info.value)

    def test_month_before_2000(self):
        """Test month year before 2000 rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CycleRequest(
                indicator_type="ht_trendline",
                symbol="IBM",
                interval="5min",
                series_type="close",
                month="1999-12",
            )
        assert "2000 or later" in str(exc_info.value)

    def test_invalid_month_number(self):
        """Test invalid month number rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CycleRequest(
                indicator_type="ht_trendline",
                symbol="IBM",
                interval="5min",
                series_type="close",
                month="2024-13",  # Month must be 01-12
            )
        assert "between 01 and 12" in str(exc_info.value)


class TestOutputParameters:
    """Test output control parameters."""

    def test_force_inline(self):
        """Test force_inline parameter."""
        request = CycleRequest(
            indicator_type="ht_dcperiod",
            symbol="IBM",
            interval="daily",
            series_type="close",
            force_inline=True,
        )
        assert request.force_inline is True
        assert request.force_file is False

    def test_force_file(self):
        """Test force_file parameter."""
        request = CycleRequest(
            indicator_type="ht_dcperiod",
            symbol="IBM",
            interval="daily",
            series_type="close",
            force_file=True,
        )
        assert request.force_file is True
        assert request.force_inline is False

    def test_force_inline_and_force_file_mutually_exclusive(self):
        """Test force_inline and force_file are mutually exclusive."""
        with pytest.raises(ValidationError) as exc_info:
            CycleRequest(
                indicator_type="ht_dcperiod",
                symbol="IBM",
                interval="daily",
                series_type="close",
                force_inline=True,
                force_file=True,
            )
        assert "mutually exclusive" in str(exc_info.value)


class TestDataTypeParameter:
    """Test datatype parameter validation."""

    @pytest.mark.parametrize("datatype", ["json", "csv"])
    def test_valid_datatype(self, datatype):
        """Test valid datatype values."""
        request = CycleRequest(
            indicator_type="ht_phasor",
            symbol="IBM",
            interval="daily",
            series_type="close",
            datatype=datatype,
        )
        assert request.datatype == datatype

    def test_default_datatype(self):
        """Test default datatype is csv."""
        request = CycleRequest(
            indicator_type="ht_phasor",
            symbol="IBM",
            interval="daily",
            series_type="close",
        )
        assert request.datatype == "csv"


class TestSymbolValidation:
    """Test symbol parameter validation."""

    @pytest.mark.parametrize("symbol", ["IBM", "AAPL", "MSFT", "GOOGL", "TSLA"])
    def test_various_symbols(self, symbol):
        """Test various valid symbols."""
        request = CycleRequest(
            indicator_type="ht_sine",
            symbol=symbol,
            interval="daily",
            series_type="close",
        )
        assert request.symbol == symbol

    def test_symbol_required(self):
        """Test symbol is required."""
        with pytest.raises(ValidationError) as exc_info:
            CycleRequest(
                indicator_type="ht_trendmode",
                interval="daily",
                series_type="close",
            )
        errors = exc_info.value.errors()
        assert any("symbol" in str(err) for err in errors)


class TestIntervalValidation:
    """Test interval parameter validation."""

    @pytest.mark.parametrize(
        "interval",
        ["1min", "5min", "15min", "30min", "60min", "daily", "weekly", "monthly"],
    )
    def test_all_valid_intervals(self, interval):
        """Test all valid interval values."""
        request = CycleRequest(
            indicator_type="ht_trendline",
            symbol="IBM",
            interval=interval,
            series_type="close",
        )
        assert request.interval == interval

    def test_interval_required(self):
        """Test interval is required."""
        with pytest.raises(ValidationError) as exc_info:
            CycleRequest(
                indicator_type="ht_dcphase",
                symbol="IBM",
                series_type="close",
            )
        errors = exc_info.value.errors()
        assert any("interval" in str(err) for err in errors)
