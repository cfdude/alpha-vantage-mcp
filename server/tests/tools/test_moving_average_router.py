"""
Unit tests for moving average routing logic.

Tests cover:
- API function name mapping for all indicator types
- Parameter transformation for each indicator type
- Output decision parameter extraction
- Routing validation and error handling
"""

import pytest

from src.tools.moving_average_router import (
    get_api_function_name,
    get_output_decision_params,
    route_request,
    transform_request_params,
    validate_routing,
)
from src.tools.moving_average_schema import MovingAverageRequest


class TestAPIFunctionMapping:
    """Test get_api_function_name for all indicator types."""

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
            ("mama", "MAMA"),
            ("t3", "T3"),
            ("vwap", "VWAP"),
        ],
    )
    def test_indicator_type_to_function_mapping(self, indicator_type, expected_function):
        """Test all indicator types map to correct API function names."""
        function_name = get_api_function_name(indicator_type)
        assert function_name == expected_function

    def test_invalid_indicator_type(self):
        """Test invalid indicator_type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_api_function_name("invalid_indicator")
        assert "Unknown indicator_type" in str(exc_info.value)
        assert "invalid_indicator" in str(exc_info.value)


class TestStandardIndicatorTransform:
    """Test parameter transformation for standard indicators (SMA, EMA, WMA, etc.)."""

    @pytest.mark.parametrize(
        "indicator_type",
        ["sma", "ema", "wma", "dema", "tema", "trima", "kama", "t3"],
    )
    def test_standard_indicator_basic_params(self, indicator_type):
        """Test standard indicators transform with basic parameters."""
        request = MovingAverageRequest(
            indicator_type=indicator_type,
            symbol="IBM",
            interval="daily",
            time_period=60,
            series_type="close",
        )
        params = transform_request_params(request)

        # Check all required parameters are present
        assert params["symbol"] == "IBM"
        assert params["interval"] == "daily"
        assert params["time_period"] == 60
        assert params["series_type"] == "close"
        assert params["datatype"] == "csv"

    @pytest.mark.parametrize(
        "indicator_type",
        ["sma", "ema", "wma", "dema", "tema", "trima", "kama", "t3"],
    )
    def test_standard_indicator_with_month_intraday(self, indicator_type):
        """Test standard indicators include month parameter for intraday intervals."""
        request = MovingAverageRequest(
            indicator_type=indicator_type,
            symbol="AAPL",
            interval="5min",
            time_period=50,
            series_type="close",
            month="2024-01",
        )
        params = transform_request_params(request)

        assert params["month"] == "2024-01"

    @pytest.mark.parametrize(
        "indicator_type",
        ["sma", "ema", "wma", "dema", "tema", "trima", "kama", "t3"],
    )
    def test_standard_indicator_month_not_added_for_daily(self, indicator_type):
        """Test month parameter not added for non-intraday intervals (even if provided)."""
        request = MovingAverageRequest(
            indicator_type=indicator_type,
            symbol="AAPL",
            interval="daily",
            time_period=50,
            series_type="close",
        )
        params = transform_request_params(request)

        # month should not be in params for daily interval
        assert "month" not in params

    @pytest.mark.parametrize("series_type", ["close", "open", "high", "low"])
    def test_standard_indicator_all_series_types(self, series_type):
        """Test standard indicators work with all series types."""
        request = MovingAverageRequest(
            indicator_type="sma",
            symbol="IBM",
            interval="daily",
            time_period=60,
            series_type=series_type,
        )
        params = transform_request_params(request)

        assert params["series_type"] == series_type


class TestMAMATransform:
    """Test parameter transformation for MAMA indicator."""

    def test_mama_basic_params(self):
        """Test MAMA transforms with basic parameters."""
        request = MovingAverageRequest(
            indicator_type="mama",
            symbol="IBM",
            interval="daily",
            series_type="close",
        )
        params = transform_request_params(request)

        # Check all required parameters are present
        assert params["symbol"] == "IBM"
        assert params["interval"] == "daily"
        assert params["series_type"] == "close"
        assert params["fastlimit"] == 0.01  # Default
        assert params["slowlimit"] == 0.01  # Default
        assert params["datatype"] == "csv"

        # time_period should NOT be in params
        assert "time_period" not in params

    def test_mama_custom_limits(self):
        """Test MAMA transforms with custom fastlimit/slowlimit."""
        request = MovingAverageRequest(
            indicator_type="mama",
            symbol="AAPL",
            interval="daily",
            series_type="close",
            fastlimit=0.02,
            slowlimit=0.05,
        )
        params = transform_request_params(request)

        assert params["fastlimit"] == 0.02
        assert params["slowlimit"] == 0.05

    def test_mama_with_month_intraday(self):
        """Test MAMA includes month parameter for intraday intervals."""
        request = MovingAverageRequest(
            indicator_type="mama",
            symbol="MSFT",
            interval="15min",
            series_type="close",
            month="2024-01",
        )
        params = transform_request_params(request)

        assert params["month"] == "2024-01"


class TestVWAPTransform:
    """Test parameter transformation for VWAP indicator."""

    def test_vwap_basic_params(self):
        """Test VWAP transforms with basic parameters."""
        request = MovingAverageRequest(
            indicator_type="vwap",
            symbol="IBM",
            interval="5min",
        )
        params = transform_request_params(request)

        # Check required parameters are present
        assert params["symbol"] == "IBM"
        assert params["interval"] == "5min"
        assert params["datatype"] == "csv"

        # These should NOT be in params for VWAP
        assert "time_period" not in params
        assert "series_type" not in params
        assert "fastlimit" not in params
        assert "slowlimit" not in params

    def test_vwap_with_month(self):
        """Test VWAP includes month parameter."""
        request = MovingAverageRequest(
            indicator_type="vwap",
            symbol="GOOGL",
            interval="15min",
            month="2024-01",
        )
        params = transform_request_params(request)

        assert params["month"] == "2024-01"

    @pytest.mark.parametrize("interval", ["1min", "5min", "15min", "30min", "60min"])
    def test_vwap_all_valid_intervals(self, interval):
        """Test VWAP works with all valid intraday intervals."""
        request = MovingAverageRequest(
            indicator_type="vwap",
            symbol="TSLA",
            interval=interval,
        )
        params = transform_request_params(request)

        assert params["interval"] == interval


class TestOutputDecisionParams:
    """Test output decision parameter extraction."""

    def test_force_inline_true(self):
        """Test force_inline extraction."""
        request = MovingAverageRequest(
            indicator_type="sma",
            symbol="IBM",
            interval="daily",
            time_period=60,
            series_type="close",
            force_inline=True,
        )
        output_params = get_output_decision_params(request)

        assert output_params["force_inline"] is True
        assert output_params["force_file"] is False

    def test_force_file_true(self):
        """Test force_file extraction."""
        request = MovingAverageRequest(
            indicator_type="sma",
            symbol="IBM",
            interval="daily",
            time_period=60,
            series_type="close",
            force_file=True,
        )
        output_params = get_output_decision_params(request)

        assert output_params["force_file"] is True
        assert output_params["force_inline"] is False

    def test_both_false_default(self):
        """Test default output params (both false)."""
        request = MovingAverageRequest(
            indicator_type="sma",
            symbol="IBM",
            interval="daily",
            time_period=60,
            series_type="close",
        )
        output_params = get_output_decision_params(request)

        assert output_params["force_inline"] is False
        assert output_params["force_file"] is False


class TestRoutingValidation:
    """Test routing validation."""

    @pytest.mark.parametrize(
        "indicator_type",
        ["sma", "ema", "wma", "dema", "tema", "trima", "kama", "t3"],
    )
    def test_validate_routing_standard_indicators(self, indicator_type):
        """Test routing validation passes for standard indicators."""
        request = MovingAverageRequest(
            indicator_type=indicator_type,
            symbol="IBM",
            interval="daily",
            time_period=60,
            series_type="close",
        )
        # Should not raise any error
        validate_routing(request)

    def test_validate_routing_mama(self):
        """Test routing validation passes for MAMA."""
        request = MovingAverageRequest(
            indicator_type="mama",
            symbol="IBM",
            interval="daily",
            series_type="close",
        )
        # Should not raise any error
        validate_routing(request)

    def test_validate_routing_vwap(self):
        """Test routing validation passes for VWAP."""
        request = MovingAverageRequest(
            indicator_type="vwap",
            symbol="IBM",
            interval="5min",
        )
        # Should not raise any error
        validate_routing(request)


class TestRouteRequest:
    """Test complete request routing (integration of all routing components)."""

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
            ("mama", "MAMA"),
            ("t3", "T3"),
            ("vwap", "VWAP"),
        ],
    )
    def test_route_request_returns_correct_function_name(self, indicator_type, expected_function):
        """Test route_request returns correct API function name."""
        if indicator_type == "vwap":
            request = MovingAverageRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="5min",
            )
        elif indicator_type == "mama":
            request = MovingAverageRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="daily",
                series_type="close",
            )
        else:
            request = MovingAverageRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="daily",
                time_period=60,
                series_type="close",
            )

        function_name, params = route_request(request)
        assert function_name == expected_function

    def test_route_request_sma_complete(self):
        """Test complete routing for SMA."""
        request = MovingAverageRequest(
            indicator_type="sma",
            symbol="AAPL",
            interval="weekly",
            time_period=200,
            series_type="high",
        )
        function_name, params = route_request(request)

        assert function_name == "SMA"
        assert params["symbol"] == "AAPL"
        assert params["interval"] == "weekly"
        assert params["time_period"] == 200
        assert params["series_type"] == "high"
        assert params["datatype"] == "csv"

    def test_route_request_mama_complete(self):
        """Test complete routing for MAMA."""
        request = MovingAverageRequest(
            indicator_type="mama",
            symbol="MSFT",
            interval="monthly",
            series_type="low",
            fastlimit=0.03,
            slowlimit=0.07,
        )
        function_name, params = route_request(request)

        assert function_name == "MAMA"
        assert params["symbol"] == "MSFT"
        assert params["interval"] == "monthly"
        assert params["series_type"] == "low"
        assert params["fastlimit"] == 0.03
        assert params["slowlimit"] == 0.07
        assert "time_period" not in params

    def test_route_request_vwap_complete(self):
        """Test complete routing for VWAP."""
        request = MovingAverageRequest(
            indicator_type="vwap",
            symbol="GOOGL",
            interval="30min",
            month="2024-01",
        )
        function_name, params = route_request(request)

        assert function_name == "VWAP"
        assert params["symbol"] == "GOOGL"
        assert params["interval"] == "30min"
        assert params["month"] == "2024-01"
        assert "time_period" not in params
        assert "series_type" not in params

    def test_route_request_with_json_datatype(self):
        """Test routing with JSON datatype."""
        request = MovingAverageRequest(
            indicator_type="ema",
            symbol="IBM",
            interval="daily",
            time_period=50,
            series_type="close",
            datatype="json",
        )
        function_name, params = route_request(request)

        assert params["datatype"] == "json"
