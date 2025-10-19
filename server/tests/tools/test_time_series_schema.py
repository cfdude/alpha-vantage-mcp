"""
Unit tests for TimeSeriesRequest schema validation.

Tests cover:
- Parameter validation for each series_type
- Conditional requirements enforcement
- Invalid parameter combinations
- Edge cases and error messages
"""

import pytest
from pydantic import ValidationError

from src.tools.time_series_schema import TimeSeriesRequest


class TestIntraday:
    """Test intraday series type validation."""

    def test_valid_intraday_request(self):
        """Test valid intraday request with all parameters."""
        request = TimeSeriesRequest(
            series_type="intraday",
            symbol="IBM",
            interval="5min",
            adjusted=True,
            extended_hours=False,
            outputsize="compact",
            datatype="csv",
        )
        assert request.series_type == "intraday"
        assert request.symbol == "IBM"
        assert request.interval == "5min"
        assert request.adjusted is True
        assert request.extended_hours is False

    def test_intraday_missing_symbol(self):
        """Test intraday fails without symbol."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(
                series_type="intraday",
                interval="5min",
            )
        errors = exc_info.value.errors()
        assert any("symbol is required" in str(err) for err in errors)

    def test_intraday_missing_interval(self):
        """Test intraday fails without interval."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(
                series_type="intraday",
                symbol="IBM",
            )
        errors = exc_info.value.errors()
        assert any("interval is required" in str(err) for err in errors)

    def test_intraday_with_month(self):
        """Test intraday with specific month parameter."""
        request = TimeSeriesRequest(
            series_type="intraday",
            symbol="IBM",
            interval="15min",
            month="2024-01",
        )
        assert request.month == "2024-01"

    def test_intraday_invalid_month_format(self):
        """Test intraday rejects invalid month format."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(
                series_type="intraday",
                symbol="IBM",
                interval="5min",
                month="2024/01",  # Wrong format
            )
        errors = exc_info.value.errors()
        assert any("YYYY-MM format" in str(err) for err in errors)

    def test_intraday_invalid_month_year(self):
        """Test intraday rejects year before 2000."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(
                series_type="intraday",
                symbol="IBM",
                interval="5min",
                month="1999-12",  # Before 2000
            )
        errors = exc_info.value.errors()
        assert any("2000 or later" in str(err) for err in errors)

    def test_intraday_invalid_interval(self):
        """Test intraday rejects invalid interval."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(
                series_type="intraday",
                symbol="IBM",
                interval="3min",  # Not a valid interval
            )
        # Pydantic will catch this as it's not in the Literal
        assert exc_info.value is not None


class TestDailySeries:
    """Test daily and daily_adjusted series types."""

    def test_valid_daily_request(self):
        """Test valid daily request."""
        request = TimeSeriesRequest(
            series_type="daily",
            symbol="AAPL",
            outputsize="full",
        )
        assert request.series_type == "daily"
        assert request.symbol == "AAPL"
        assert request.outputsize == "full"

    def test_valid_daily_adjusted_request(self):
        """Test valid daily_adjusted request."""
        request = TimeSeriesRequest(
            series_type="daily_adjusted",
            symbol="MSFT",
            outputsize="compact",
        )
        assert request.series_type == "daily_adjusted"
        assert request.symbol == "MSFT"

    def test_daily_missing_symbol(self):
        """Test daily fails without symbol."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(series_type="daily")
        errors = exc_info.value.errors()
        assert any("symbol is required" in str(err) for err in errors)

    def test_daily_adjusted_missing_symbol(self):
        """Test daily_adjusted fails without symbol."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(series_type="daily_adjusted")
        errors = exc_info.value.errors()
        assert any("symbol is required" in str(err) for err in errors)


class TestWeeklySeries:
    """Test weekly and weekly_adjusted series types."""

    def test_valid_weekly_request(self):
        """Test valid weekly request."""
        request = TimeSeriesRequest(
            series_type="weekly",
            symbol="GOOGL",
        )
        assert request.series_type == "weekly"
        assert request.symbol == "GOOGL"

    def test_valid_weekly_adjusted_request(self):
        """Test valid weekly_adjusted request."""
        request = TimeSeriesRequest(
            series_type="weekly_adjusted",
            symbol="TSLA",
        )
        assert request.series_type == "weekly_adjusted"
        assert request.symbol == "TSLA"

    def test_weekly_missing_symbol(self):
        """Test weekly fails without symbol."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(series_type="weekly")
        errors = exc_info.value.errors()
        assert any("symbol is required" in str(err) for err in errors)


class TestMonthlySeries:
    """Test monthly and monthly_adjusted series types."""

    def test_valid_monthly_request(self):
        """Test valid monthly request."""
        request = TimeSeriesRequest(
            series_type="monthly",
            symbol="NVDA",
        )
        assert request.series_type == "monthly"
        assert request.symbol == "NVDA"

    def test_valid_monthly_adjusted_request(self):
        """Test valid monthly_adjusted request."""
        request = TimeSeriesRequest(
            series_type="monthly_adjusted",
            symbol="AMD",
        )
        assert request.series_type == "monthly_adjusted"
        assert request.symbol == "AMD"

    def test_monthly_missing_symbol(self):
        """Test monthly fails without symbol."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(series_type="monthly")
        errors = exc_info.value.errors()
        assert any("symbol is required" in str(err) for err in errors)


class TestQuote:
    """Test quote series type."""

    def test_valid_quote_request(self):
        """Test valid quote request."""
        request = TimeSeriesRequest(
            series_type="quote",
            symbol="IBM",
        )
        assert request.series_type == "quote"
        assert request.symbol == "IBM"

    def test_quote_missing_symbol(self):
        """Test quote fails without symbol."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(series_type="quote")
        errors = exc_info.value.errors()
        assert any("symbol is required" in str(err) for err in errors)


class TestBulkQuotes:
    """Test bulk_quotes series type."""

    def test_valid_bulk_quotes_request(self):
        """Test valid bulk quotes request."""
        request = TimeSeriesRequest(
            series_type="bulk_quotes",
            symbols="AAPL,MSFT,GOOGL",
        )
        assert request.series_type == "bulk_quotes"
        assert request.symbols == "AAPL,MSFT,GOOGL"

    def test_bulk_quotes_missing_symbols(self):
        """Test bulk_quotes fails without symbols parameter."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(series_type="bulk_quotes")
        errors = exc_info.value.errors()
        assert any("symbols parameter is required" in str(err) for err in errors)

    def test_bulk_quotes_wrong_parameter_name(self):
        """Test bulk_quotes fails if symbol (not symbols) is provided."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(
                series_type="bulk_quotes",
                symbol="AAPL",  # Wrong - should use symbols
            )
        errors = exc_info.value.errors()
        assert any("Use 'symbols' (not 'symbol')" in str(err) for err in errors)

    def test_bulk_quotes_too_many_symbols(self):
        """Test bulk_quotes rejects more than 100 symbols."""
        # Create 101 symbols
        symbols = ",".join([f"SYM{i}" for i in range(101)])

        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(
                series_type="bulk_quotes",
                symbols=symbols,
            )
        errors = exc_info.value.errors()
        assert any("maximum 100 symbols" in str(err) for err in errors)

    def test_bulk_quotes_exactly_100_symbols(self):
        """Test bulk_quotes accepts exactly 100 symbols."""
        symbols = ",".join([f"SYM{i}" for i in range(100)])
        request = TimeSeriesRequest(
            series_type="bulk_quotes",
            symbols=symbols,
        )
        assert request.symbols == symbols


class TestSearch:
    """Test search series type."""

    def test_valid_search_request(self):
        """Test valid search request."""
        request = TimeSeriesRequest(
            series_type="search",
            keywords="microsoft",
        )
        assert request.series_type == "search"
        assert request.keywords == "microsoft"

    def test_search_missing_keywords(self):
        """Test search fails without keywords."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(series_type="search")
        errors = exc_info.value.errors()
        assert any("keywords parameter is required" in str(err) for err in errors)


class TestMarketStatus:
    """Test market_status series type."""

    def test_valid_market_status_request(self):
        """Test valid market status request."""
        request = TimeSeriesRequest(series_type="market_status")
        assert request.series_type == "market_status"

    def test_market_status_rejects_symbol(self):
        """Test market_status rejects symbol parameter."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(
                series_type="market_status",
                symbol="IBM",
            )
        errors = exc_info.value.errors()
        assert any("does not require symbol" in str(err) for err in errors)

    def test_market_status_rejects_symbols(self):
        """Test market_status rejects symbols parameter."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(
                series_type="market_status",
                symbols="AAPL,MSFT",
            )
        errors = exc_info.value.errors()
        assert any("does not require" in str(err) for err in errors)


class TestOutputControls:
    """Test output control parameters."""

    def test_force_inline(self):
        """Test force_inline parameter."""
        request = TimeSeriesRequest(
            series_type="daily",
            symbol="IBM",
            force_inline=True,
        )
        assert request.force_inline is True
        assert request.force_file is False

    def test_force_file(self):
        """Test force_file parameter."""
        request = TimeSeriesRequest(
            series_type="daily",
            symbol="IBM",
            force_file=True,
        )
        assert request.force_file is True
        assert request.force_inline is False

    def test_force_inline_and_force_file_mutually_exclusive(self):
        """Test that force_inline and force_file cannot both be True."""
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(
                series_type="daily",
                symbol="IBM",
                force_inline=True,
                force_file=True,
            )
        errors = exc_info.value.errors()
        assert any("mutually exclusive" in str(err) for err in errors)


class TestEntitlement:
    """Test entitlement parameter."""

    def test_entitlement_delayed(self):
        """Test entitlement with delayed option."""
        request = TimeSeriesRequest(
            series_type="intraday",
            symbol="IBM",
            interval="5min",
            entitlement="delayed",
        )
        assert request.entitlement == "delayed"

    def test_entitlement_realtime(self):
        """Test entitlement with realtime option."""
        request = TimeSeriesRequest(
            series_type="intraday",
            symbol="IBM",
            interval="5min",
            entitlement="realtime",
        )
        assert request.entitlement == "realtime"

    def test_invalid_entitlement(self):
        """Test invalid entitlement value is rejected."""
        with pytest.raises(ValidationError):
            TimeSeriesRequest(
                series_type="intraday",
                symbol="IBM",
                interval="5min",
                entitlement="invalid",  # Not in Literal["delayed", "realtime"]
            )


class TestDatatype:
    """Test datatype parameter."""

    def test_datatype_json(self):
        """Test datatype=json."""
        request = TimeSeriesRequest(
            series_type="daily",
            symbol="IBM",
            datatype="json",
        )
        assert request.datatype == "json"

    def test_datatype_csv(self):
        """Test datatype=csv (default)."""
        request = TimeSeriesRequest(
            series_type="daily",
            symbol="IBM",
        )
        assert request.datatype == "csv"

    def test_invalid_datatype(self):
        """Test invalid datatype is rejected."""
        with pytest.raises(ValidationError):
            TimeSeriesRequest(
                series_type="daily",
                symbol="IBM",
                datatype="xml",  # Not in Literal["json", "csv"]
            )


class TestParameterizedValidation:
    """Parameterized tests for all series types."""

    @pytest.mark.parametrize(
        "series_type,required_params,optional_params",
        [
            ("intraday", {"symbol": "IBM", "interval": "5min"}, {"month": "2024-01"}),
            ("daily", {"symbol": "AAPL"}, {"outputsize": "full"}),
            ("daily_adjusted", {"symbol": "MSFT"}, {"outputsize": "compact"}),
            ("weekly", {"symbol": "GOOGL"}, {}),
            ("weekly_adjusted", {"symbol": "TSLA"}, {}),
            ("monthly", {"symbol": "NVDA"}, {}),
            ("monthly_adjusted", {"symbol": "AMD"}, {}),
            ("quote", {"symbol": "IBM"}, {}),
            ("bulk_quotes", {"symbols": "AAPL,MSFT"}, {}),
            ("search", {"keywords": "microsoft"}, {}),
            ("market_status", {}, {}),
        ],
    )
    def test_all_series_types_valid(self, series_type, required_params, optional_params):
        """Test all series types with valid parameters."""
        all_params = {"series_type": series_type, **required_params, **optional_params}
        request = TimeSeriesRequest(**all_params)
        assert request.series_type == series_type

    @pytest.mark.parametrize(
        "series_type,missing_param",
        [
            ("intraday", "symbol"),
            ("intraday", "interval"),
            ("daily", "symbol"),
            ("daily_adjusted", "symbol"),
            ("weekly", "symbol"),
            ("weekly_adjusted", "symbol"),
            ("monthly", "symbol"),
            ("monthly_adjusted", "symbol"),
            ("quote", "symbol"),
            ("bulk_quotes", "symbols"),
            ("search", "keywords"),
        ],
    )
    def test_all_series_types_missing_required_param(self, series_type, missing_param):
        """Test all series types fail when missing required parameters."""
        with pytest.raises(ValidationError) as exc_info:
            # Provide minimal params but intentionally omit the missing_param
            params = {"series_type": series_type}

            # Add all required params except the missing one
            if series_type == "intraday":
                if missing_param != "symbol":
                    params["symbol"] = "IBM"
                if missing_param != "interval":
                    params["interval"] = "5min"
            elif series_type == "bulk_quotes":
                if missing_param != "symbols":
                    params["symbols"] = "AAPL"
            elif series_type == "search":
                if missing_param != "keywords":
                    params["keywords"] = "test"
            elif missing_param != "symbol" and series_type != "market_status":
                params["symbol"] = "IBM"

            TimeSeriesRequest(**params)

        errors = exc_info.value.errors()
        assert any(
            f"{missing_param} is required" in str(err) or missing_param in str(err)
            for err in errors
        )
