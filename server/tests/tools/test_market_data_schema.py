"""
Unit tests for MarketDataRequest schema validation.

Tests cover:
- Parameter validation for each request_type
- Complex conditional parameter requirements
- Date format validation
- Output flag validation (force_inline/force_file)
- Invalid parameter combinations
- Edge cases and error messages
- Parameterized tests for efficiency
"""

import pytest
from pydantic import ValidationError

from src.tools.market_data_schema import MarketDataRequest


class TestRequestTypes:
    """Test all market data request types."""

    @pytest.mark.parametrize(
        "request_type",
        ["listing_status", "earnings_calendar", "ipo_calendar"],
    )
    def test_valid_request_type(self, request_type):
        """Test valid requests for all request types."""
        request = MarketDataRequest(
            request_type=request_type,
        )
        assert request.request_type == request_type
        assert request.force_inline is False
        assert request.force_file is False

    def test_invalid_request_type(self):
        """Test that invalid request types are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketDataRequest(
                request_type="invalid_request",
            )
        errors = exc_info.value.errors()
        assert any("request_type" in str(err) for err in errors)


class TestListingStatus:
    """Test listing_status request type."""

    def test_listing_status_defaults(self):
        """Test listing_status with default parameters."""
        request = MarketDataRequest(
            request_type="listing_status",
        )
        assert request.request_type == "listing_status"
        assert request.date is None
        assert request.state == "active"

    def test_listing_status_active(self):
        """Test listing_status for active stocks."""
        request = MarketDataRequest(
            request_type="listing_status",
            state="active",
        )
        assert request.state == "active"

    def test_listing_status_delisted(self):
        """Test listing_status for delisted stocks."""
        request = MarketDataRequest(
            request_type="listing_status",
            state="delisted",
        )
        assert request.state == "delisted"

    def test_listing_status_with_date(self):
        """Test listing_status with historical date."""
        request = MarketDataRequest(
            request_type="listing_status",
            date="2020-01-15",
        )
        assert request.date == "2020-01-15"

    def test_listing_status_with_date_and_state(self):
        """Test listing_status with both date and state."""
        request = MarketDataRequest(
            request_type="listing_status",
            date="2015-06-30",
            state="delisted",
        )
        assert request.date == "2015-06-30"
        assert request.state == "delisted"

    def test_listing_status_rejects_symbol(self):
        """Test that listing_status rejects symbol parameter."""
        with pytest.raises(ValidationError) as exc_info:
            MarketDataRequest(
                request_type="listing_status",
                symbol="IBM",
            )
        errors = exc_info.value.errors()
        assert any("symbol" in str(err) for err in errors)


class TestEarningsCalendar:
    """Test earnings_calendar request type."""

    def test_earnings_calendar_defaults(self):
        """Test earnings_calendar with default parameters."""
        request = MarketDataRequest(
            request_type="earnings_calendar",
        )
        assert request.request_type == "earnings_calendar"
        assert request.symbol is None
        assert request.horizon == "3month"

    def test_earnings_calendar_with_symbol(self):
        """Test earnings_calendar for specific symbol."""
        request = MarketDataRequest(
            request_type="earnings_calendar",
            symbol="IBM",
        )
        assert request.symbol == "IBM"

    @pytest.mark.parametrize(
        "horizon",
        ["3month", "6month", "12month"],
    )
    def test_earnings_calendar_horizons(self, horizon):
        """Test all valid horizon values."""
        request = MarketDataRequest(
            request_type="earnings_calendar",
            horizon=horizon,
        )
        assert request.horizon == horizon

    def test_earnings_calendar_with_symbol_and_horizon(self):
        """Test earnings_calendar with both symbol and horizon."""
        request = MarketDataRequest(
            request_type="earnings_calendar",
            symbol="AAPL",
            horizon="6month",
        )
        assert request.symbol == "AAPL"
        assert request.horizon == "6month"

    def test_earnings_calendar_rejects_date(self):
        """Test that earnings_calendar rejects date parameter."""
        with pytest.raises(ValidationError) as exc_info:
            MarketDataRequest(
                request_type="earnings_calendar",
                date="2020-01-15",
            )
        errors = exc_info.value.errors()
        assert any("date" in str(err) for err in errors)


class TestIPOCalendar:
    """Test ipo_calendar request type."""

    def test_ipo_calendar_defaults(self):
        """Test ipo_calendar with no parameters."""
        request = MarketDataRequest(
            request_type="ipo_calendar",
        )
        assert request.request_type == "ipo_calendar"

    def test_ipo_calendar_rejects_date(self):
        """Test that ipo_calendar rejects date parameter."""
        with pytest.raises(ValidationError) as exc_info:
            MarketDataRequest(
                request_type="ipo_calendar",
                date="2020-01-15",
            )
        errors = exc_info.value.errors()
        assert any("date" in str(err) for err in errors)

    def test_ipo_calendar_rejects_symbol(self):
        """Test that ipo_calendar rejects symbol parameter."""
        with pytest.raises(ValidationError) as exc_info:
            MarketDataRequest(
                request_type="ipo_calendar",
                symbol="IBM",
            )
        errors = exc_info.value.errors()
        assert any("symbol" in str(err) for err in errors)


class TestDateValidation:
    """Test date parameter validation."""

    @pytest.mark.parametrize(
        "date",
        [
            "2020-01-15",
            "2015-06-30",
            "2010-01-01",  # Minimum date
            "2024-12-31",
        ],
    )
    def test_valid_dates(self, date):
        """Test various valid date formats."""
        request = MarketDataRequest(
            request_type="listing_status",
            date=date,
        )
        assert request.date == date

    def test_date_before_2010_rejected(self):
        """Test that dates before 2010 are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketDataRequest(
                request_type="listing_status",
                date="2009-12-31",
            )
        errors = exc_info.value.errors()
        assert any("2010 or later" in str(err) for err in errors)

    @pytest.mark.parametrize(
        "invalid_date",
        [
            "2020/01/15",  # Wrong separator
            "20-01-15",  # Wrong year format
            "2020-01",  # Missing day
            "01-15-2020",  # Wrong order
        ],
    )
    def test_invalid_date_formats(self, invalid_date):
        """Test that invalid date formats are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketDataRequest(
                request_type="listing_status",
                date=invalid_date,
            )
        errors = exc_info.value.errors()
        assert len(errors) > 0

    # Note: Single-digit months/days without leading zeros are accepted by the validator

    def test_invalid_month(self):
        """Test that invalid months are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketDataRequest(
                request_type="listing_status",
                date="2020-13-01",  # Month 13
            )
        errors = exc_info.value.errors()
        assert any("month must be between 01 and 12" in str(err) for err in errors)

    def test_invalid_day(self):
        """Test that invalid days are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketDataRequest(
                request_type="listing_status",
                date="2020-01-32",  # Day 32
            )
        errors = exc_info.value.errors()
        assert any("day must be between 01 and 31" in str(err) for err in errors)


class TestOutputFlags:
    """Test force_inline and force_file parameter validation."""

    def test_force_inline_only(self):
        """Test force_inline=True without force_file."""
        request = MarketDataRequest(
            request_type="listing_status",
            force_inline=True,
        )
        assert request.force_inline is True
        assert request.force_file is False

    def test_force_file_only(self):
        """Test force_file=True without force_inline."""
        request = MarketDataRequest(
            request_type="listing_status",
            force_file=True,
        )
        assert request.force_file is True
        assert request.force_inline is False

    def test_both_flags_true_rejected(self):
        """Test that setting both force_inline and force_file is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketDataRequest(
                request_type="listing_status",
                force_inline=True,
                force_file=True,
            )
        errors = exc_info.value.errors()
        assert any("mutually exclusive" in str(err) for err in errors)


class TestConditionalParameterValidation:
    """Test complex conditional parameter validation."""

    def test_listing_status_accepts_date_and_state(self):
        """Test that listing_status accepts its parameters."""
        request = MarketDataRequest(
            request_type="listing_status",
            date="2020-01-15",
            state="active",
        )
        assert request.date == "2020-01-15"
        assert request.state == "active"

    def test_earnings_calendar_accepts_symbol_and_horizon(self):
        """Test that earnings_calendar accepts its parameters."""
        request = MarketDataRequest(
            request_type="earnings_calendar",
            symbol="IBM",
            horizon="6month",
        )
        assert request.symbol == "IBM"
        assert request.horizon == "6month"

    def test_ipo_calendar_accepts_no_extra_params(self):
        """Test that ipo_calendar has no extra parameters."""
        request = MarketDataRequest(
            request_type="ipo_calendar",
        )
        # Should have only default values
        assert request.date is None
        assert request.symbol is None


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.parametrize(
        "request_type",
        ["listing_status", "earnings_calendar", "ipo_calendar"],
    )
    def test_all_request_types_default_output_flags(self, request_type):
        """Test that all request types have False output flags by default."""
        request = MarketDataRequest(
            request_type=request_type,
        )
        assert request.force_inline is False
        assert request.force_file is False

    def test_error_message_quality_for_invalid_request_type(self):
        """Test that error messages are helpful for invalid request types."""
        with pytest.raises(ValidationError) as exc_info:
            MarketDataRequest(
                request_type="stock_calendar",  # Not valid
            )
        error_str = str(exc_info.value)
        assert "request_type" in error_str.lower()

    @pytest.mark.parametrize(
        "symbol",
        ["IBM", "AAPL", "MSFT", "GOOGL", "TSLA"],
    )
    def test_earnings_calendar_various_symbols(self, symbol):
        """Test earnings_calendar with various stock symbols."""
        request = MarketDataRequest(
            request_type="earnings_calendar",
            symbol=symbol,
        )
        assert request.symbol == symbol


class TestComprehensiveCombinations:
    """Test comprehensive parameter combinations."""

    @pytest.mark.parametrize(
        "request_type,date,state,symbol,horizon",
        [
            ("listing_status", None, "active", None, "3month"),
            ("listing_status", "2020-01-15", "delisted", None, "3month"),
            ("earnings_calendar", None, "active", "IBM", "6month"),
            ("earnings_calendar", None, "active", None, "12month"),
            ("ipo_calendar", None, "active", None, "3month"),
        ],
    )
    def test_valid_combinations(self, request_type, date, state, symbol, horizon):
        """Test various valid parameter combinations."""
        request = MarketDataRequest(
            request_type=request_type,
            date=date,
            state=state,
            symbol=symbol,
            horizon=horizon,
        )
        assert request.request_type == request_type

    def test_listing_status_full_specification(self):
        """Test listing_status with all parameters specified."""
        request = MarketDataRequest(
            request_type="listing_status",
            date="2020-06-15",
            state="delisted",
            force_file=True,
        )
        assert request.date == "2020-06-15"
        assert request.state == "delisted"
        assert request.force_file is True

    def test_earnings_calendar_full_specification(self):
        """Test earnings_calendar with all parameters specified."""
        request = MarketDataRequest(
            request_type="earnings_calendar",
            symbol="AAPL",
            horizon="12month",
            force_inline=True,
        )
        assert request.symbol == "AAPL"
        assert request.horizon == "12month"
        assert request.force_inline is True
