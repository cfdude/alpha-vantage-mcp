"""
Unit tests for ForexRequest schema validation.

Tests cover:
- Parameter validation for each timeframe
- Conditional requirements enforcement
- Invalid parameter combinations
- Edge cases and error messages
"""

import pytest
from pydantic import ValidationError

from src.tools.forex_schema import ForexRequest


class TestIntradayForex:
    """Test intraday timeframe validation."""

    def test_valid_intraday_request(self):
        """Test valid intraday request with all parameters."""
        request = ForexRequest(
            timeframe="intraday",
            from_symbol="EUR",
            to_symbol="USD",
            interval="5min",
            outputsize="compact",
            datatype="csv",
        )
        assert request.timeframe == "intraday"
        assert request.from_symbol == "EUR"
        assert request.to_symbol == "USD"
        assert request.interval == "5min"
        assert request.outputsize == "compact"

    def test_intraday_missing_interval(self):
        """Test intraday fails without interval."""
        with pytest.raises(ValidationError) as exc_info:
            ForexRequest(
                timeframe="intraday",
                from_symbol="EUR",
                to_symbol="USD",
            )
        errors = exc_info.value.errors()
        assert any("interval is required" in str(err) for err in errors)

    def test_intraday_all_intervals(self):
        """Test all valid interval values for intraday."""
        intervals = ["1min", "5min", "15min", "30min", "60min"]
        for interval in intervals:
            request = ForexRequest(
                timeframe="intraday",
                from_symbol="EUR",
                to_symbol="USD",
                interval=interval,
            )
            assert request.interval == interval

    def test_intraday_invalid_interval(self):
        """Test intraday rejects invalid interval."""
        with pytest.raises(ValidationError):
            ForexRequest(
                timeframe="intraday",
                from_symbol="EUR",
                to_symbol="USD",
                interval="3min",  # Not a valid interval
            )


class TestDailyForex:
    """Test daily timeframe validation."""

    def test_valid_daily_request(self):
        """Test valid daily request."""
        request = ForexRequest(
            timeframe="daily",
            from_symbol="GBP",
            to_symbol="USD",
            outputsize="full",
        )
        assert request.timeframe == "daily"
        assert request.from_symbol == "GBP"
        assert request.to_symbol == "USD"
        assert request.outputsize == "full"

    def test_daily_with_interval_rejected(self):
        """Test daily rejects interval parameter."""
        with pytest.raises(ValidationError) as exc_info:
            ForexRequest(
                timeframe="daily",
                from_symbol="EUR",
                to_symbol="USD",
                interval="5min",  # Should not be provided for daily
            )
        errors = exc_info.value.errors()
        assert any("not applicable" in str(err) for err in errors)

    def test_daily_default_outputsize(self):
        """Test daily uses default outputsize."""
        request = ForexRequest(
            timeframe="daily",
            from_symbol="EUR",
            to_symbol="USD",
        )
        assert request.outputsize == "compact"


class TestWeeklyForex:
    """Test weekly timeframe validation."""

    def test_valid_weekly_request(self):
        """Test valid weekly request."""
        request = ForexRequest(
            timeframe="weekly",
            from_symbol="EUR",
            to_symbol="JPY",
        )
        assert request.timeframe == "weekly"
        assert request.from_symbol == "EUR"
        assert request.to_symbol == "JPY"

    def test_weekly_with_interval_rejected(self):
        """Test weekly rejects interval parameter."""
        with pytest.raises(ValidationError) as exc_info:
            ForexRequest(
                timeframe="weekly",
                from_symbol="EUR",
                to_symbol="USD",
                interval="5min",
            )
        errors = exc_info.value.errors()
        assert any("not applicable" in str(err) for err in errors)


class TestMonthlyForex:
    """Test monthly timeframe validation."""

    def test_valid_monthly_request(self):
        """Test valid monthly request."""
        request = ForexRequest(
            timeframe="monthly",
            from_symbol="CAD",
            to_symbol="USD",
        )
        assert request.timeframe == "monthly"
        assert request.from_symbol == "CAD"
        assert request.to_symbol == "USD"

    def test_monthly_with_interval_rejected(self):
        """Test monthly rejects interval parameter."""
        with pytest.raises(ValidationError) as exc_info:
            ForexRequest(
                timeframe="monthly",
                from_symbol="EUR",
                to_symbol="USD",
                interval="5min",
            )
        errors = exc_info.value.errors()
        assert any("not applicable" in str(err) for err in errors)


class TestOutputControls:
    """Test output control parameters."""

    def test_force_inline(self):
        """Test force_inline parameter."""
        request = ForexRequest(
            timeframe="daily",
            from_symbol="EUR",
            to_symbol="USD",
            force_inline=True,
        )
        assert request.force_inline is True
        assert request.force_file is False

    def test_force_file(self):
        """Test force_file parameter."""
        request = ForexRequest(
            timeframe="daily",
            from_symbol="EUR",
            to_symbol="USD",
            force_file=True,
        )
        assert request.force_file is True
        assert request.force_inline is False

    def test_force_inline_and_force_file_mutually_exclusive(self):
        """Test that force_inline and force_file cannot both be True."""
        with pytest.raises(ValidationError) as exc_info:
            ForexRequest(
                timeframe="daily",
                from_symbol="EUR",
                to_symbol="USD",
                force_inline=True,
                force_file=True,
            )
        errors = exc_info.value.errors()
        assert any("mutually exclusive" in str(err) for err in errors)


class TestDatatype:
    """Test datatype parameter."""

    def test_datatype_json(self):
        """Test datatype=json."""
        request = ForexRequest(
            timeframe="daily",
            from_symbol="EUR",
            to_symbol="USD",
            datatype="json",
        )
        assert request.datatype == "json"

    def test_datatype_csv_default(self):
        """Test datatype=csv (default)."""
        request = ForexRequest(
            timeframe="daily",
            from_symbol="EUR",
            to_symbol="USD",
        )
        assert request.datatype == "csv"

    def test_invalid_datatype(self):
        """Test invalid datatype is rejected."""
        with pytest.raises(ValidationError):
            ForexRequest(
                timeframe="daily",
                from_symbol="EUR",
                to_symbol="USD",
                datatype="xml",  # Not in Literal["json", "csv"]
            )


class TestParameterizedValidation:
    """Parameterized tests for all timeframes."""

    @pytest.mark.parametrize(
        "timeframe,required_params,optional_params",
        [
            ("intraday", {"from_symbol": "EUR", "to_symbol": "USD", "interval": "5min"}, {}),
            ("daily", {"from_symbol": "GBP", "to_symbol": "USD"}, {"outputsize": "full"}),
            ("weekly", {"from_symbol": "EUR", "to_symbol": "JPY"}, {}),
            ("monthly", {"from_symbol": "CAD", "to_symbol": "USD"}, {}),
        ],
    )
    def test_all_timeframes_valid(self, timeframe, required_params, optional_params):
        """Test all timeframes with valid parameters."""
        all_params = {"timeframe": timeframe, **required_params, **optional_params}
        request = ForexRequest(**all_params)
        assert request.timeframe == timeframe

    @pytest.mark.parametrize(
        "from_sym,to_sym",
        [
            ("EUR", "USD"),
            ("GBP", "USD"),
            ("USD", "JPY"),
            ("AUD", "CAD"),
            ("NZD", "CHF"),
        ],
    )
    def test_various_currency_pairs(self, from_sym, to_sym):
        """Test various forex currency pairs."""
        request = ForexRequest(
            timeframe="daily",
            from_symbol=from_sym,
            to_symbol=to_sym,
        )
        assert request.from_symbol == from_sym
        assert request.to_symbol == to_sym


class TestInvalidTimeframe:
    """Test invalid timeframe values."""

    def test_invalid_timeframe(self):
        """Test that invalid timeframe is rejected."""
        with pytest.raises(ValidationError):
            ForexRequest(
                timeframe="hourly",  # Not a valid timeframe
                from_symbol="EUR",
                to_symbol="USD",
            )
