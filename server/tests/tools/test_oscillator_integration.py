"""
Integration tests for unified oscillator tool.

These tests verify the end-to-end flow from tool invocation through
routing to API call (mocked).

NOTE: These tests use sys.modules mocking to avoid import errors
from dependencies that may not be initialized during test collection.
"""

import json
from unittest.mock import patch

import pytest


class TestSimplePeriodIndicatorsIntegration:
    """Integration tests for simple period oscillators (WILLR, ADX, ADXR, CCI)."""

    @pytest.mark.parametrize(
        "indicator_type,expected_function",
        [
            ("willr", "WILLR"),
            ("adx", "ADX"),
            ("adxr", "ADXR"),
            ("cci", "CCI"),
        ],
    )
    @patch("src.tools.oscillator_unified._make_api_request")
    def test_simple_period_request_flow(self, mock_api_request, indicator_type, expected_function):
        """Test complete flow for simple period indicators."""
        from src.tools.oscillator_unified import get_oscillator

        # Mock the API response
        mock_api_request.return_value = (
            f"timestamp,{expected_function}\n2024-01-01,50.5\n2024-01-02,51.2"
        )

        # Make request
        result = get_oscillator(
            indicator_type=indicator_type,
            symbol="IBM",
            interval="daily",
            time_period=14,
        )

        # Verify API was called with correct parameters
        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == expected_function
        params = call_args[0][1]
        assert params["symbol"] == "IBM"
        assert params["interval"] == "daily"
        assert params["time_period"] == 14
        assert params["datatype"] == "csv"

        # Should NOT have series_type
        assert "series_type" not in params

        # Verify result
        assert isinstance(result, str)
        assert expected_function in result

        # Reset mock for next test


class TestSeriesPeriodIndicatorsIntegration:
    """Integration tests for series + period oscillators (RSI, MOM, CMO, ROC, ROCR)."""

    @pytest.mark.parametrize(
        "indicator_type,expected_function",
        [
            ("rsi", "RSI"),
            ("mom", "MOM"),
            ("cmo", "CMO"),
            ("roc", "ROC"),
            ("rocr", "ROCR"),
        ],
    )
    @patch("src.tools.oscillator_unified._make_api_request")
    def test_series_period_request_flow(self, mock_api_request, indicator_type, expected_function):
        """Test complete flow for series + period indicators."""
        from src.tools.oscillator_unified import get_oscillator

        mock_api_request.return_value = (
            f"timestamp,{expected_function}\n2024-01-01,45.5\n2024-01-02,48.2"
        )

        result = get_oscillator(
            indicator_type=indicator_type,
            symbol="AAPL",
            interval="daily",
            time_period=14,
            series_type="close",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == expected_function
        params = call_args[0][1]
        assert params["symbol"] == "AAPL"
        assert params["time_period"] == 14
        assert params["series_type"] == "close"

        assert isinstance(result, str)


class TestMACDIndicatorsIntegration:
    """Integration tests for MACD family oscillators."""

    @patch("src.tools.oscillator_unified._make_api_request")
    def test_macd_request_flow_with_defaults(self, mock_api_request):
        """Test MACD request with default periods."""
        from src.tools.oscillator_unified import get_oscillator

        mock_api_request.return_value = (
            "timestamp,MACD,MACD_Signal,MACD_Hist\n2024-01-01,0.5,0.4,0.1\n2024-01-02,0.6,0.5,0.1"
        )

        result = get_oscillator(
            indicator_type="macd",
            symbol="MSFT",
            interval="daily",
            series_type="close",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "MACD"
        params = call_args[0][1]
        assert params["symbol"] == "MSFT"
        assert params["series_type"] == "close"
        assert params["fastperiod"] == 12  # Default
        assert params["slowperiod"] == 26  # Default
        assert params["signalperiod"] == 9  # Default

        # Should NOT have time_period
        assert "time_period" not in params

        assert isinstance(result, str)

    @patch("src.tools.oscillator_unified._make_api_request")
    def test_macd_request_flow_with_custom_periods(self, mock_api_request):
        """Test MACD request with custom periods."""
        from src.tools.oscillator_unified import get_oscillator

        mock_api_request.return_value = "timestamp,MACD\n2024-01-01,0.8"

        result = get_oscillator(
            indicator_type="macd",
            symbol="GOOGL",
            interval="daily",
            series_type="close",
            fastperiod=8,
            slowperiod=21,
            signalperiod=5,
        )

        call_args = mock_api_request.call_args
        params = call_args[0][1]
        assert params["fastperiod"] == 8
        assert params["slowperiod"] == 21
        assert params["signalperiod"] == 5

        assert isinstance(result, str)

    @patch("src.tools.oscillator_unified._make_api_request")
    def test_macdext_request_flow(self, mock_api_request):
        """Test MACDEXT request with MA types."""
        from src.tools.oscillator_unified import get_oscillator

        mock_api_request.return_value = "timestamp,MACD\n2024-01-01,0.5"

        result = get_oscillator(
            indicator_type="macdext",
            symbol="TSLA",
            interval="daily",
            series_type="close",
            fastmatype=1,  # EMA
            slowmatype=2,  # WMA
            signalmatype=3,  # DEMA
        )

        call_args = mock_api_request.call_args
        assert call_args[0][0] == "MACDEXT"
        params = call_args[0][1]
        assert params["fastmatype"] == 1
        assert params["slowmatype"] == 2
        assert params["signalmatype"] == 3

        assert isinstance(result, str)


class TestAPOPPOIndicatorsIntegration:
    """Integration tests for APO and PPO oscillators."""

    @pytest.mark.parametrize(
        "indicator_type,expected_function",
        [
            ("apo", "APO"),
            ("ppo", "PPO"),
        ],
    )
    @patch("src.tools.oscillator_unified._make_api_request")
    def test_apo_ppo_request_flow(self, mock_api_request, indicator_type, expected_function):
        """Test complete flow for APO/PPO indicators."""
        from src.tools.oscillator_unified import get_oscillator

        mock_api_request.return_value = f"timestamp,{expected_function}\n2024-01-01,1.5"

        result = get_oscillator(
            indicator_type=indicator_type,
            symbol="NVDA",
            interval="daily",
            series_type="close",
            matype=1,  # EMA
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == expected_function
        params = call_args[0][1]
        assert params["series_type"] == "close"
        assert params["fastperiod"] == 12
        assert params["slowperiod"] == 26
        assert params["matype"] == 1

        assert "time_period" not in params
        assert isinstance(result, str)


class TestStochasticIndicatorsIntegration:
    """Integration tests for stochastic oscillators."""

    @patch("src.tools.oscillator_unified._make_api_request")
    def test_stoch_request_flow(self, mock_api_request):
        """Test STOCH request flow."""
        from src.tools.oscillator_unified import get_oscillator

        mock_api_request.return_value = "timestamp,SlowK,SlowD\n2024-01-01,75.5,74.2"

        result = get_oscillator(
            indicator_type="stoch",
            symbol="AMZN",
            interval="daily",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "STOCH"
        params = call_args[0][1]
        assert params["fastkperiod"] == 5
        assert params["slowkperiod"] == 3
        assert params["slowdperiod"] == 3
        assert params["slowkmatype"] == 0
        assert params["slowdmatype"] == 0

        # Should NOT have time_period or series_type
        assert "time_period" not in params
        assert "series_type" not in params
        assert isinstance(result, str)

    @patch("src.tools.oscillator_unified._make_api_request")
    def test_stochf_request_flow(self, mock_api_request):
        """Test STOCHF request flow."""
        from src.tools.oscillator_unified import get_oscillator

        mock_api_request.return_value = "timestamp,FastK,FastD\n2024-01-01,80.5,78.2"

        result = get_oscillator(
            indicator_type="stochf",
            symbol="META",
            interval="daily",
        )

        call_args = mock_api_request.call_args
        assert call_args[0][0] == "STOCHF"
        params = call_args[0][1]
        assert params["fastkperiod"] == 5
        assert params["fastdperiod"] == 3
        assert params["fastdmatype"] == 0

        assert "slowkperiod" not in params
        assert "time_period" not in params
        assert isinstance(result, str)

    @patch("src.tools.oscillator_unified._make_api_request")
    def test_stochrsi_request_flow(self, mock_api_request):
        """Test STOCHRSI request flow."""
        from src.tools.oscillator_unified import get_oscillator

        mock_api_request.return_value = "timestamp,FastK,FastD\n2024-01-01,70.5,68.2"

        result = get_oscillator(
            indicator_type="stochrsi",
            symbol="DIS",
            interval="daily",
            time_period=14,
            series_type="close",
        )

        call_args = mock_api_request.call_args
        assert call_args[0][0] == "STOCHRSI"
        params = call_args[0][1]
        # RSI params
        assert params["time_period"] == 14
        assert params["series_type"] == "close"
        # Stochastic params
        assert params["fastkperiod"] == 5
        assert params["fastdperiod"] == 3
        assert params["fastdmatype"] == 0

        assert isinstance(result, str)


class TestBalanceOfPowerIntegration:
    """Integration tests for BOP (Balance of Power)."""

    @patch("src.tools.oscillator_unified._make_api_request")
    def test_bop_request_flow(self, mock_api_request):
        """Test BOP request flow (no additional params)."""
        from src.tools.oscillator_unified import get_oscillator

        mock_api_request.return_value = "timestamp,BOP\n2024-01-01,0.25\n2024-01-02,0.30"

        result = get_oscillator(
            indicator_type="bop",
            symbol="NFLX",
            interval="daily",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "BOP"
        params = call_args[0][1]
        assert params["symbol"] == "NFLX"
        assert params["interval"] == "daily"

        # Should NOT have any indicator-specific params
        assert "time_period" not in params
        assert "series_type" not in params
        assert "fastperiod" not in params

        assert isinstance(result, str)


class TestIntradayWithMonth:
    """Integration tests for intraday requests with month parameter."""

    @patch("src.tools.oscillator_unified._make_api_request")
    def test_rsi_intraday_with_month(self, mock_api_request):
        """Test RSI intraday request includes month parameter."""
        from src.tools.oscillator_unified import get_oscillator

        mock_api_request.return_value = "timestamp,RSI\n2024-01-15 09:30,55.5"

        result = get_oscillator(
            indicator_type="rsi",
            symbol="IBM",
            interval="5min",
            time_period=14,
            series_type="close",
            month="2024-01",
        )

        call_args = mock_api_request.call_args
        params = call_args[0][1]
        assert params["month"] == "2024-01"
        assert params["interval"] == "5min"

        assert isinstance(result, str)


class TestErrorHandling:
    """Integration tests for error handling."""

    @patch("src.tools.oscillator_unified._make_api_request")
    def test_validation_error_returns_json_error(self, mock_api_request):
        """Test that validation errors return structured JSON error response."""
        from src.tools.oscillator_unified import get_oscillator

        # Missing required parameter (time_period for RSI)
        result = get_oscillator(
            indicator_type="rsi",
            symbol="IBM",
            interval="daily",
            series_type="close",
            # Missing time_period
        )

        # Should return JSON error response
        assert isinstance(result, str)
        error_data = json.loads(result)
        assert "error" in error_data
        assert "validation_errors" in error_data
        assert any("time_period" in str(err) for err in error_data["validation_errors"])

    @patch("src.tools.oscillator_unified._make_api_request")
    def test_invalid_series_type_returns_json_error(self, mock_api_request):
        """Test that invalid series_type for BOP returns structured error."""
        from src.tools.oscillator_unified import get_oscillator

        result = get_oscillator(
            indicator_type="bop",
            symbol="IBM",
            interval="daily",
            series_type="close",  # Not valid for BOP
        )

        assert isinstance(result, str)
        error_data = json.loads(result)
        assert "error" in error_data
        assert "validation_errors" in error_data


class TestComprehensiveCoverage:
    """Comprehensive integration tests for all 17 indicators."""

    @pytest.mark.parametrize(
        "indicator_type,extra_params,expected_function",
        [
            ("macd", {"series_type": "close"}, "MACD"),
            ("macdext", {"series_type": "close"}, "MACDEXT"),
            ("stoch", {}, "STOCH"),
            ("stochf", {}, "STOCHF"),
            ("rsi", {"time_period": 14, "series_type": "close"}, "RSI"),
            ("stochrsi", {"time_period": 14, "series_type": "close"}, "STOCHRSI"),
            ("willr", {"time_period": 14}, "WILLR"),
            ("adx", {"time_period": 14}, "ADX"),
            ("adxr", {"time_period": 14}, "ADXR"),
            ("apo", {"series_type": "close"}, "APO"),
            ("ppo", {"series_type": "close"}, "PPO"),
            ("mom", {"time_period": 10, "series_type": "close"}, "MOM"),
            ("bop", {}, "BOP"),
            ("cci", {"time_period": 20}, "CCI"),
            ("cmo", {"time_period": 14, "series_type": "close"}, "CMO"),
            ("roc", {"time_period": 12, "series_type": "close"}, "ROC"),
            ("rocr", {"time_period": 12, "series_type": "close"}, "ROCR"),
        ],
    )
    @patch("src.tools.oscillator_unified._make_api_request")
    def test_all_17_indicators_end_to_end(
        self, mock_api_request, indicator_type, extra_params, expected_function
    ):
        """Test complete end-to-end flow for all 17 oscillator indicators."""
        from src.tools.oscillator_unified import get_oscillator

        mock_api_request.return_value = f"timestamp,{expected_function}\n2024-01-01,50.0"

        result = get_oscillator(
            indicator_type=indicator_type,
            symbol="TEST",
            interval="daily",
            **extra_params,
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == expected_function

        assert isinstance(result, str)
