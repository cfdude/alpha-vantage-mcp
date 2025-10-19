"""
Unit tests for time series routing logic.

Tests cover:
- API function name mapping
- Parameter transformation for each series_type
- Routing validation
- Error handling
"""

import pytest

from src.tools.time_series_router import (
    RoutingError,
    get_api_function_name,
    get_output_decision_params,
    route_request,
    transform_request_params,
    validate_routing,
)
from src.tools.time_series_schema import TimeSeriesRequest


class TestGetApiFunctionName:
    """Test API function name mapping."""

    def test_intraday_mapping(self):
        """Test intraday maps to TIME_SERIES_INTRADAY."""
        assert get_api_function_name("intraday") == "TIME_SERIES_INTRADAY"

    def test_daily_mapping(self):
        """Test daily maps to TIME_SERIES_DAILY."""
        assert get_api_function_name("daily") == "TIME_SERIES_DAILY"

    def test_daily_adjusted_mapping(self):
        """Test daily_adjusted maps to TIME_SERIES_DAILY_ADJUSTED."""
        assert get_api_function_name("daily_adjusted") == "TIME_SERIES_DAILY_ADJUSTED"

    def test_weekly_mapping(self):
        """Test weekly maps to TIME_SERIES_WEEKLY."""
        assert get_api_function_name("weekly") == "TIME_SERIES_WEEKLY"

    def test_weekly_adjusted_mapping(self):
        """Test weekly_adjusted maps to TIME_SERIES_WEEKLY_ADJUSTED."""
        assert get_api_function_name("weekly_adjusted") == "TIME_SERIES_WEEKLY_ADJUSTED"

    def test_monthly_mapping(self):
        """Test monthly maps to TIME_SERIES_MONTHLY."""
        assert get_api_function_name("monthly") == "TIME_SERIES_MONTHLY"

    def test_monthly_adjusted_mapping(self):
        """Test monthly_adjusted maps to TIME_SERIES_MONTHLY_ADJUSTED."""
        assert get_api_function_name("monthly_adjusted") == "TIME_SERIES_MONTHLY_ADJUSTED"

    def test_quote_mapping(self):
        """Test quote maps to GLOBAL_QUOTE."""
        assert get_api_function_name("quote") == "GLOBAL_QUOTE"

    def test_bulk_quotes_mapping(self):
        """Test bulk_quotes maps to REALTIME_BULK_QUOTES."""
        assert get_api_function_name("bulk_quotes") == "REALTIME_BULK_QUOTES"

    def test_search_mapping(self):
        """Test search maps to SYMBOL_SEARCH."""
        assert get_api_function_name("search") == "SYMBOL_SEARCH"

    def test_market_status_mapping(self):
        """Test market_status maps to MARKET_STATUS."""
        assert get_api_function_name("market_status") == "MARKET_STATUS"

    def test_invalid_series_type(self):
        """Test invalid series_type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_api_function_name("invalid_type")
        assert "Unknown series_type" in str(exc_info.value)


class TestTransformRequestParams:
    """Test parameter transformation."""

    def test_intraday_params(self):
        """Test intraday parameter transformation."""
        request = TimeSeriesRequest(
            series_type="intraday",
            symbol="IBM",
            interval="5min",
            adjusted=True,
            extended_hours=False,
            outputsize="compact",
            datatype="csv",
        )
        params = transform_request_params(request)

        assert params["symbol"] == "IBM"
        assert params["interval"] == "5min"
        assert params["adjusted"] == "true"
        assert params["extended_hours"] == "false"
        assert params["outputsize"] == "compact"
        assert params["datatype"] == "csv"

    def test_intraday_params_with_month(self):
        """Test intraday with month parameter."""
        request = TimeSeriesRequest(
            series_type="intraday",
            symbol="IBM",
            interval="15min",
            month="2024-01",
        )
        params = transform_request_params(request)

        assert params["month"] == "2024-01"

    def test_daily_params(self):
        """Test daily parameter transformation."""
        request = TimeSeriesRequest(
            series_type="daily",
            symbol="AAPL",
            outputsize="full",
            datatype="json",
        )
        params = transform_request_params(request)

        assert params["symbol"] == "AAPL"
        assert params["outputsize"] == "full"
        assert params["datatype"] == "json"

    def test_daily_adjusted_params(self):
        """Test daily_adjusted parameter transformation."""
        request = TimeSeriesRequest(
            series_type="daily_adjusted",
            symbol="MSFT",
            outputsize="compact",
        )
        params = transform_request_params(request)

        assert params["symbol"] == "MSFT"
        assert params["outputsize"] == "compact"

    def test_weekly_params(self):
        """Test weekly parameter transformation."""
        request = TimeSeriesRequest(
            series_type="weekly",
            symbol="GOOGL",
        )
        params = transform_request_params(request)

        assert params["symbol"] == "GOOGL"
        assert params["datatype"] == "csv"  # Default
        assert "outputsize" not in params  # Weekly doesn't use outputsize

    def test_monthly_params(self):
        """Test monthly parameter transformation."""
        request = TimeSeriesRequest(
            series_type="monthly",
            symbol="NVDA",
        )
        params = transform_request_params(request)

        assert params["symbol"] == "NVDA"
        assert "outputsize" not in params  # Monthly doesn't use outputsize

    def test_quote_params(self):
        """Test quote parameter transformation."""
        request = TimeSeriesRequest(
            series_type="quote",
            symbol="TSLA",
        )
        params = transform_request_params(request)

        assert params["symbol"] == "TSLA"

    def test_bulk_quotes_params(self):
        """Test bulk_quotes uses 'symbol' parameter for API (not 'symbols')."""
        request = TimeSeriesRequest(
            series_type="bulk_quotes",
            symbols="AAPL,MSFT,GOOGL",
        )
        params = transform_request_params(request)

        # Important: Alpha Vantage API uses 'symbol' not 'symbols'
        assert params["symbol"] == "AAPL,MSFT,GOOGL"
        assert "symbols" not in params

    def test_search_params(self):
        """Test search parameter transformation."""
        request = TimeSeriesRequest(
            series_type="search",
            keywords="microsoft",
        )
        params = transform_request_params(request)

        assert params["keywords"] == "microsoft"

    def test_market_status_params(self):
        """Test market_status has no parameters except datatype."""
        request = TimeSeriesRequest(series_type="market_status")
        params = transform_request_params(request)

        assert params["datatype"] == "csv"
        assert len(params) == 1  # Only datatype

    def test_entitlement_included_when_present(self):
        """Test entitlement parameter is included when provided."""
        request = TimeSeriesRequest(
            series_type="intraday",
            symbol="IBM",
            interval="5min",
            entitlement="realtime",
        )
        params = transform_request_params(request)

        assert params["entitlement"] == "realtime"

    def test_entitlement_excluded_when_none(self):
        """Test entitlement parameter is excluded when None."""
        request = TimeSeriesRequest(
            series_type="daily",
            symbol="IBM",
            entitlement=None,
        )
        params = transform_request_params(request)

        assert "entitlement" not in params


class TestValidateRouting:
    """Test routing validation."""

    def test_validate_intraday_valid(self):
        """Test intraday validation passes with required params."""
        request = TimeSeriesRequest(
            series_type="intraday",
            symbol="IBM",
            interval="5min",
        )
        validate_routing(request)  # Should not raise

    def test_validate_daily_valid(self):
        """Test daily validation passes with symbol."""
        request = TimeSeriesRequest(
            series_type="daily",
            symbol="AAPL",
        )
        validate_routing(request)  # Should not raise

    def test_validate_bulk_quotes_valid(self):
        """Test bulk_quotes validation passes with symbols."""
        request = TimeSeriesRequest(
            series_type="bulk_quotes",
            symbols="AAPL,MSFT",
        )
        validate_routing(request)  # Should not raise

    def test_validate_search_valid(self):
        """Test search validation passes with keywords."""
        request = TimeSeriesRequest(
            series_type="search",
            keywords="microsoft",
        )
        validate_routing(request)  # Should not raise

    def test_validate_market_status_valid(self):
        """Test market_status validation passes with no params."""
        request = TimeSeriesRequest(series_type="market_status")
        validate_routing(request)  # Should not raise


class TestGetOutputDecisionParams:
    """Test output decision parameter extraction."""

    def test_default_output_params(self):
        """Test default output decision params."""
        request = TimeSeriesRequest(
            series_type="daily",
            symbol="IBM",
        )
        params = get_output_decision_params(request)

        assert params["force_inline"] is False
        assert params["force_file"] is False

    def test_force_inline_true(self):
        """Test force_inline=True is extracted."""
        request = TimeSeriesRequest(
            series_type="daily",
            symbol="IBM",
            force_inline=True,
        )
        params = get_output_decision_params(request)

        assert params["force_inline"] is True
        assert params["force_file"] is False

    def test_force_file_true(self):
        """Test force_file=True is extracted."""
        request = TimeSeriesRequest(
            series_type="daily",
            symbol="IBM",
            force_file=True,
        )
        params = get_output_decision_params(request)

        assert params["force_inline"] is False
        assert params["force_file"] is True


class TestRouteRequest:
    """Test complete request routing."""

    def test_route_intraday_request(self):
        """Test routing intraday request."""
        request = TimeSeriesRequest(
            series_type="intraday",
            symbol="IBM",
            interval="5min",
            outputsize="full",
        )
        function_name, params = route_request(request)

        assert function_name == "TIME_SERIES_INTRADAY"
        assert params["symbol"] == "IBM"
        assert params["interval"] == "5min"
        assert params["outputsize"] == "full"

    def test_route_daily_adjusted_request(self):
        """Test routing daily_adjusted request."""
        request = TimeSeriesRequest(
            series_type="daily_adjusted",
            symbol="AAPL",
            outputsize="compact",
        )
        function_name, params = route_request(request)

        assert function_name == "TIME_SERIES_DAILY_ADJUSTED"
        assert params["symbol"] == "AAPL"
        assert params["outputsize"] == "compact"

    def test_route_bulk_quotes_request(self):
        """Test routing bulk_quotes request."""
        request = TimeSeriesRequest(
            series_type="bulk_quotes",
            symbols="AAPL,MSFT,GOOGL",
        )
        function_name, params = route_request(request)

        assert function_name == "REALTIME_BULK_QUOTES"
        assert params["symbol"] == "AAPL,MSFT,GOOGL"  # Note: 'symbol' not 'symbols'

    def test_route_search_request(self):
        """Test routing search request."""
        request = TimeSeriesRequest(
            series_type="search",
            keywords="tesla",
        )
        function_name, params = route_request(request)

        assert function_name == "SYMBOL_SEARCH"
        assert params["keywords"] == "tesla"

    def test_route_market_status_request(self):
        """Test routing market_status request."""
        request = TimeSeriesRequest(series_type="market_status")
        function_name, params = route_request(request)

        assert function_name == "MARKET_STATUS"
        assert params["datatype"] == "csv"

    def test_route_with_entitlement(self):
        """Test routing preserves entitlement parameter."""
        request = TimeSeriesRequest(
            series_type="intraday",
            symbol="IBM",
            interval="5min",
            entitlement="realtime",
        )
        function_name, params = route_request(request)

        assert params["entitlement"] == "realtime"


class TestParameterizedRouting:
    """Parameterized routing tests for all series types."""

    @pytest.mark.parametrize(
        "series_type,api_function,required_params",
        [
            ("intraday", "TIME_SERIES_INTRADAY", {"symbol": "IBM", "interval": "5min"}),
            ("daily", "TIME_SERIES_DAILY", {"symbol": "AAPL"}),
            ("daily_adjusted", "TIME_SERIES_DAILY_ADJUSTED", {"symbol": "MSFT"}),
            ("weekly", "TIME_SERIES_WEEKLY", {"symbol": "GOOGL"}),
            ("weekly_adjusted", "TIME_SERIES_WEEKLY_ADJUSTED", {"symbol": "TSLA"}),
            ("monthly", "TIME_SERIES_MONTHLY", {"symbol": "NVDA"}),
            ("monthly_adjusted", "TIME_SERIES_MONTHLY_ADJUSTED", {"symbol": "AMD"}),
            ("quote", "GLOBAL_QUOTE", {"symbol": "IBM"}),
            ("bulk_quotes", "REALTIME_BULK_QUOTES", {"symbols": "AAPL,MSFT"}),
            ("search", "SYMBOL_SEARCH", {"keywords": "microsoft"}),
            ("market_status", "MARKET_STATUS", {}),
        ],
    )
    def test_route_all_series_types(self, series_type, api_function, required_params):
        """Test routing for all series types."""
        request_params = {"series_type": series_type, **required_params}
        request = TimeSeriesRequest(**request_params)

        function_name, params = route_request(request)

        assert function_name == api_function
        assert params["datatype"] == "csv"  # Default for all


class TestErrorHandling:
    """Test error handling in routing."""

    def test_routing_validation_raises_value_error(self):
        """Test that routing validation raises ValueError for invalid requests."""
        # This is a defense-in-depth test - schema validation should catch this first
        # But we test that routing also catches it
        request = TimeSeriesRequest(
            series_type="daily",
            symbol="IBM",
        )

        # Manually break the request to test error handling
        request.symbol = None  # Make it invalid after validation

        with pytest.raises(ValueError) as exc_info:
            validate_routing(request)
        assert "requires symbol parameter" in str(exc_info.value)

    def test_route_request_wraps_in_routing_error(self):
        """Test that route_request wraps exceptions in RoutingError."""
        request = TimeSeriesRequest(
            series_type="daily",
            symbol="IBM",
        )

        # Manually break the request
        request.symbol = None

        with pytest.raises(RoutingError) as exc_info:
            route_request(request)
        assert "Failed to route request" in str(exc_info.value)
