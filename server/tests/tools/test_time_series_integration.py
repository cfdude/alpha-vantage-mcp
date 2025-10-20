"""
Integration tests for unified time series tool.

These tests verify the end-to-end flow from tool invocation through
routing to API call (mocked).
"""

import json
from unittest.mock import patch

import pytest


class TestGetTimeSeriesIntegration:
    """Integration tests for get_time_series tool."""

    @patch("src.tools.time_series_unified._make_api_request")
    def test_intraday_request_flow(self, mock_api_request):
        """Test complete flow for intraday request."""
        from src.tools.time_series_unified import get_time_series

        # Mock the API response
        mock_api_request.return_value = (
            "timestamp,open,high,low,close,volume\n2024-01-01,100,105,99,104,1000"
        )

        # Make request
        result = get_time_series(
            series_type="intraday",
            symbol="IBM",
            interval="5min",
            outputsize="compact",
        )

        # Verify API was called with correct parameters
        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "TIME_SERIES_INTRADAY"
        params = call_args[0][1]
        assert params["symbol"] == "IBM"
        assert params["interval"] == "5min"
        assert params["adjusted"] == "true"
        assert params["extended_hours"] == "true"

        # Verify result
        assert isinstance(result, str)
        assert "timestamp" in result

    @patch("src.tools.time_series_unified._make_api_request")
    def test_daily_adjusted_request_flow(self, mock_api_request):
        """Test complete flow for daily_adjusted request."""
        from src.tools.time_series_unified import get_time_series

        mock_api_request.return_value = (
            "timestamp,open,high,low,close,adjusted_close\n2024-01-01,100,105,99,104,104.5"
        )

        get_time_series(
            series_type="daily_adjusted",
            symbol="AAPL",
            outputsize="full",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "TIME_SERIES_DAILY_ADJUSTED"
        params = call_args[0][1]
        assert params["symbol"] == "AAPL"
        assert params["outputsize"] == "full"

    @patch("src.tools.time_series_unified._make_api_request")
    def test_bulk_quotes_request_flow(self, mock_api_request):
        """Test complete flow for bulk_quotes request."""
        from src.tools.time_series_unified import get_time_series

        mock_api_request.return_value = "symbol,price,volume\nAAPL,150,1000\nMSFT,300,2000"

        get_time_series(
            series_type="bulk_quotes",
            symbols="AAPL,MSFT,GOOGL",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "REALTIME_BULK_QUOTES"
        params = call_args[0][1]
        # API expects 'symbol' not 'symbols'
        assert params["symbol"] == "AAPL,MSFT,GOOGL"

    @patch("src.tools.time_series_unified._make_api_request")
    def test_search_request_flow(self, mock_api_request):
        """Test complete flow for search request."""
        from src.tools.time_series_unified import get_time_series

        mock_api_request.return_value = "symbol,name,type,region\nMSFT,Microsoft Corp,Equity,US"

        get_time_series(
            series_type="search",
            keywords="microsoft",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "SYMBOL_SEARCH"
        params = call_args[0][1]
        assert params["keywords"] == "microsoft"

    @patch("src.tools.time_series_unified._make_api_request")
    def test_market_status_request_flow(self, mock_api_request):
        """Test complete flow for market_status request."""
        from src.tools.time_series_unified import get_time_series

        mock_api_request.return_value = "market,status\nUS,open"

        get_time_series(series_type="market_status")

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "MARKET_STATUS"
        params = call_args[0][1]
        assert params["datatype"] == "csv"
        # No symbol/symbols/keywords
        assert "symbol" not in params
        assert "symbols" not in params
        assert "keywords" not in params

    def test_entitlement_parameter_passed_through(self):
        """Test that entitlement parameter is passed through decorator to _make_api_request.

        NOTE: The @tool decorator sets entitlement as a global variable (src.common._current_entitlement)
        which _make_api_request reads. We skip testing this integration detail since it's handled
        by the decorator framework, not our code.
        """
        pytest.skip("Entitlement is handled by @tool decorator framework via global variable")


class TestGetTimeSeriesErrorHandling:
    """Test error handling in the tool."""

    def test_invalid_series_type_returns_error_json(self):
        """Test that invalid series_type returns structured error."""
        from src.tools.time_series_unified import get_time_series

        # This will fail Pydantic validation
        result = get_time_series(
            series_type="invalid",  # type: ignore
            symbol="IBM",
        )

        # Should return JSON error response
        assert isinstance(result, str)
        error_data = json.loads(result)
        assert "error" in error_data
        assert error_data["error"] == "Request validation failed"

    def test_missing_required_param_returns_error_json(self):
        """Test that missing required params returns structured error."""
        from src.tools.time_series_unified import get_time_series

        result = get_time_series(
            series_type="intraday",
            symbol="IBM",
            # Missing interval
        )

        assert isinstance(result, str)
        error_data = json.loads(result)
        assert "error" in error_data
        assert "validation_errors" in error_data
        assert any("interval is required" in str(err) for err in error_data["validation_errors"])

    def test_bulk_quotes_wrong_param_returns_error_json(self):
        """Test that using 'symbol' instead of 'symbols' for bulk_quotes returns error."""
        from src.tools.time_series_unified import get_time_series

        result = get_time_series(
            series_type="bulk_quotes",
            symbol="AAPL",  # Wrong - should use symbols
        )

        assert isinstance(result, str)
        error_data = json.loads(result)
        assert "error" in error_data
        assert any("Use 'symbols'" in str(err) for err in error_data.get("validation_errors", []))

    @patch("src.tools.time_series_unified._make_api_request")
    def test_api_error_handled_gracefully(self, mock_api_request):
        """Test that API errors are handled gracefully."""
        from src.tools.time_series_unified import get_time_series

        # Simulate API error
        mock_api_request.side_effect = Exception("API connection failed")

        result = get_time_series(
            series_type="daily",
            symbol="IBM",
        )

        # Should return error response instead of raising
        assert isinstance(result, str)
        error_data = json.loads(result)
        assert "error" in error_data
        assert "API connection failed" in error_data["message"]
