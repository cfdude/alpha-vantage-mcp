"""
Integration tests for unified moving average tool.

These tests verify the end-to-end flow from tool invocation through
routing to API call (mocked).

NOTE: These tests use sys.modules mocking to avoid import errors
from dependencies that may not be initialized during test collection.
"""

import json
from unittest.mock import patch

import pytest


class TestGetMovingAverageIntegration:
    """Integration tests for get_moving_average tool."""

    @patch("src.tools.moving_average_unified._make_api_request")
    def test_sma_request_flow(self, mock_api_request):
        """Test complete flow for SMA request."""
        # Import after mocks are in place
        from src.tools.moving_average_unified import (
            get_moving_average,
        )

        # Mock the API response
        mock_api_request.return_value = "timestamp,SMA\n2024-01-01,102.5\n2024-01-02,103.0"

        # Make request
        result = get_moving_average(
            indicator_type="sma",
            symbol="IBM",
            interval="daily",
            time_period=60,
            series_type="close",
        )

        # Verify API was called with correct parameters
        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "SMA"
        params = call_args[0][1]
        assert params["symbol"] == "IBM"
        assert params["interval"] == "daily"
        assert params["time_period"] == 60
        assert params["series_type"] == "close"
        assert params["datatype"] == "csv"

        # Verify result
        assert isinstance(result, str)
        assert "SMA" in result

        # Reset mock for next test

    @patch("src.tools.moving_average_unified._make_api_request")
    def test_ema_request_flow(self, mock_api_request):
        """Test complete flow for EMA request."""
        from src.tools.moving_average_unified import (
            get_moving_average,
        )

        mock_api_request.return_value = "timestamp,EMA\n2024-01-01,150.25\n2024-01-02,150.75"

        result = get_moving_average(
            indicator_type="ema",
            symbol="AAPL",
            interval="weekly",
            time_period=200,
            series_type="high",
            datatype="csv",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "EMA"
        params = call_args[0][1]
        assert params["symbol"] == "AAPL"
        assert params["interval"] == "weekly"
        assert params["time_period"] == 200
        assert params["series_type"] == "high"

        assert isinstance(result, str)

    @patch("src.tools.moving_average_unified._make_api_request")
    def test_mama_request_flow(self, mock_api_request):
        """Test complete flow for MAMA request."""
        from src.tools.moving_average_unified import (
            get_moving_average,
        )

        mock_api_request.return_value = (
            "timestamp,MAMA,FAMA\n2024-01-01,100.5,99.8\n2024-01-02,101.0,100.2"
        )

        result = get_moving_average(
            indicator_type="mama",
            symbol="MSFT",
            interval="daily",
            series_type="close",
            fastlimit=0.02,
            slowlimit=0.05,
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "MAMA"
        params = call_args[0][1]
        assert params["symbol"] == "MSFT"
        assert params["interval"] == "daily"
        assert params["series_type"] == "close"
        assert params["fastlimit"] == 0.02
        assert params["slowlimit"] == 0.05
        # time_period should NOT be in params
        assert "time_period" not in params

        assert isinstance(result, str)

    @patch("src.tools.moving_average_unified._make_api_request")
    def test_mama_request_with_defaults(self, mock_api_request):
        """Test MAMA request uses default fastlimit/slowlimit."""
        from src.tools.moving_average_unified import (
            get_moving_average,
        )

        mock_api_request.return_value = "timestamp,MAMA,FAMA\n2024-01-01,100.5,99.8"

        get_moving_average(
            indicator_type="mama",
            symbol="GOOGL",
            interval="daily",
            series_type="low",
        )

        call_args = mock_api_request.call_args
        params = call_args[0][1]
        assert params["fastlimit"] == 0.01  # Default
        assert params["slowlimit"] == 0.01  # Default

    @patch("src.tools.moving_average_unified._make_api_request")
    def test_vwap_request_flow(self, mock_api_request):
        """Test complete flow for VWAP request."""
        from src.tools.moving_average_unified import (
            get_moving_average,
        )

        mock_api_request.return_value = (
            "timestamp,VWAP\n2024-01-01 09:30,150.25\n2024-01-01 09:35,150.30"
        )

        result = get_moving_average(
            indicator_type="vwap",
            symbol="TSLA",
            interval="5min",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "VWAP"
        params = call_args[0][1]
        assert params["symbol"] == "TSLA"
        assert params["interval"] == "5min"
        # These should NOT be in params
        assert "time_period" not in params
        assert "series_type" not in params
        assert "fastlimit" not in params
        assert "slowlimit" not in params

        assert isinstance(result, str)

    @patch("src.tools.moving_average_unified._make_api_request")
    def test_intraday_with_month(self, mock_api_request):
        """Test intraday request with month parameter."""
        from src.tools.moving_average_unified import (
            get_moving_average,
        )

        mock_api_request.return_value = "timestamp,SMA\n2024-01-01 09:30,100.5"

        get_moving_average(
            indicator_type="sma",
            symbol="IBM",
            interval="15min",
            time_period=50,
            series_type="close",
            month="2024-01",
        )

        call_args = mock_api_request.call_args
        params = call_args[0][1]
        assert params["month"] == "2024-01"

    @patch("src.tools.moving_average_unified._make_api_request")
    def test_json_datatype(self, mock_api_request):
        """Test request with JSON datatype."""
        from src.tools.moving_average_unified import (
            get_moving_average,
        )

        mock_api_request.return_value = {
            "Meta Data": {"Symbol": "IBM"},
            "Technical Analysis: SMA": {"2024-01-01": {"SMA": "102.5"}},
        }

        get_moving_average(
            indicator_type="sma",
            symbol="IBM",
            interval="daily",
            time_period=60,
            series_type="close",
            datatype="json",
        )

        call_args = mock_api_request.call_args
        params = call_args[0][1]
        assert params["datatype"] == "json"


class TestGetMovingAverageErrors:
    """Test error handling in get_moving_average tool."""

    @patch("src.tools.moving_average_unified._make_api_request")
    def test_validation_error_missing_time_period(self, mock_api_request):
        """Test validation error when time_period is missing for standard indicator."""
        from src.tools.moving_average_unified import get_moving_average

        result = get_moving_average(
            indicator_type="sma",
            symbol="IBM",
            interval="daily",
            series_type="close",
            # Missing time_period
        )

        # Should return error JSON
        assert isinstance(result, str)
        error_data = json.loads(result)
        assert "error" in error_data
        assert error_data["error"] == "Request validation failed"
        assert "validation_errors" in error_data

    @patch("src.tools.moving_average_unified._make_api_request")
    def test_validation_error_vwap_non_intraday(self, mock_api_request):
        """Test validation error when VWAP uses non-intraday interval."""
        from src.tools.moving_average_unified import get_moving_average

        result = get_moving_average(
            indicator_type="vwap",
            symbol="IBM",
            interval="daily",  # VWAP requires intraday
        )

        # Should return error JSON
        assert isinstance(result, str)
        error_data = json.loads(result)
        assert "error" in error_data
        assert error_data["error"] == "Request validation failed"

    @patch("src.tools.moving_average_unified._make_api_request")
    def test_validation_error_mama_with_time_period(self, mock_api_request):
        """Test validation error when MAMA is given time_period."""
        from src.tools.moving_average_unified import get_moving_average

        result = get_moving_average(
            indicator_type="mama",
            symbol="IBM",
            interval="daily",
            series_type="close",
            time_period=60,  # Not valid for MAMA
        )

        # Should return error JSON
        assert isinstance(result, str)
        error_data = json.loads(result)
        assert "error" in error_data
        assert error_data["error"] == "Request validation failed"

    @patch("src.tools.moving_average_unified._make_api_request")
    def test_validation_error_vwap_with_series_type(self, mock_api_request):
        """Test validation error when VWAP is given series_type."""
        from src.tools.moving_average_unified import get_moving_average

        result = get_moving_average(
            indicator_type="vwap",
            symbol="IBM",
            interval="5min",
            series_type="close",  # Not valid for VWAP
        )

        # Should return error JSON
        assert isinstance(result, str)
        error_data = json.loads(result)
        assert "error" in error_data
        assert error_data["error"] == "Request validation failed"

    @patch("src.tools.moving_average_unified._make_api_request")
    def test_validation_error_force_inline_and_force_file(self, mock_api_request):
        """Test validation error when both force_inline and force_file are True."""
        from src.tools.moving_average_unified import get_moving_average

        result = get_moving_average(
            indicator_type="sma",
            symbol="IBM",
            interval="daily",
            time_period=60,
            series_type="close",
            force_inline=True,
            force_file=True,  # Mutually exclusive
        )

        # Should return error JSON
        assert isinstance(result, str)
        error_data = json.loads(result)
        assert "error" in error_data
        assert error_data["error"] == "Request validation failed"


class TestGetMovingAverageAllIndicators:
    """Test all indicator types can be invoked successfully."""

    @pytest.mark.parametrize(
        "indicator_type,expected_function",
        [
            ("sma", "SMA"),
            ("ema", "EMA"),
            ("wma", "WMA"),
            ("dema", "DEMA"),
            ("tema", "TEMA"),
            ("trima", "TRIMA"),
            ("kama", "KAMA"),
            ("t3", "T3"),
        ],
    )
    @patch("src.tools.moving_average_unified._make_api_request")
    def test_standard_indicator_invocation(
        self, mock_api_request, indicator_type, expected_function
    ):
        """Test all standard indicators can be invoked and route correctly."""
        from src.tools.moving_average_unified import (
            get_moving_average,
        )

        mock_api_request.return_value = f"timestamp,{expected_function}\n2024-01-01,100.5"

        get_moving_average(
            indicator_type=indicator_type,
            symbol="IBM",
            interval="daily",
            time_period=50,
            series_type="close",
        )

        call_args = mock_api_request.call_args
        assert call_args[0][0] == expected_function

    @patch("src.tools.moving_average_unified._make_api_request")
    def test_mama_invocation(self, mock_api_request):
        """Test MAMA can be invoked and routes correctly."""
        from src.tools.moving_average_unified import (
            get_moving_average,
        )

        mock_api_request.return_value = "timestamp,MAMA,FAMA\n2024-01-01,100.5,99.8"

        get_moving_average(
            indicator_type="mama",
            symbol="IBM",
            interval="daily",
            series_type="close",
        )

        call_args = mock_api_request.call_args
        assert call_args[0][0] == "MAMA"

    @patch("src.tools.moving_average_unified._make_api_request")
    def test_vwap_invocation(self, mock_api_request):
        """Test VWAP can be invoked and routes correctly."""
        from src.tools.moving_average_unified import (
            get_moving_average,
        )

        mock_api_request.return_value = "timestamp,VWAP\n2024-01-01 09:30,100.5"

        get_moving_average(
            indicator_type="vwap",
            symbol="IBM",
            interval="5min",
        )

        call_args = mock_api_request.call_args
        assert call_args[0][0] == "VWAP"
