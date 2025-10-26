"""
Integration tests for unified forex and crypto tools.

These tests verify the end-to-end flow from tool invocation through
routing to API call (mocked).
"""

import json
from unittest.mock import patch

import pytest


class TestGetForexDataIntegration:
    """Integration tests for get_forex_data tool."""

    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_intraday_forex_flow(self, mock_api_request):
        """Test complete flow for intraday forex request."""
        from src.tools.forex_crypto_unified import get_forex_data

        # Mock the API response
        mock_api_request.return_value = (
            "timestamp,open,high,low,close\n2024-01-01,1.0850,1.0875,1.0840,1.0860"
        )

        # Make request
        result = get_forex_data(
            timeframe="intraday",
            from_symbol="EUR",
            to_symbol="USD",
            interval="5min",
            outputsize="compact",
        )

        # Verify API was called with correct parameters
        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "FX_INTRADAY"
        params = call_args[0][1]
        assert params["from_symbol"] == "EUR"
        assert params["to_symbol"] == "USD"
        assert params["interval"] == "5min"
        assert params["outputsize"] == "compact"

        # Verify result
        assert isinstance(result, str)
        assert "timestamp" in result

    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_daily_forex_flow(self, mock_api_request):
        """Test complete flow for daily forex request."""
        from src.tools.forex_crypto_unified import get_forex_data

        mock_api_request.return_value = (
            "timestamp,open,high,low,close\n2024-01-01,1.2500,1.2550,1.2480,1.2530"
        )

        get_forex_data(
            timeframe="daily",
            from_symbol="GBP",
            to_symbol="USD",
            outputsize="full",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "FX_DAILY"
        params = call_args[0][1]
        assert params["from_symbol"] == "GBP"
        assert params["to_symbol"] == "USD"
        assert params["outputsize"] == "full"

    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_weekly_forex_flow(self, mock_api_request):
        """Test complete flow for weekly forex request."""
        from src.tools.forex_crypto_unified import get_forex_data

        mock_api_request.return_value = (
            "timestamp,open,high,low,close\n2024-01-01,130.50,131.20,129.80,130.90"
        )

        get_forex_data(
            timeframe="weekly",
            from_symbol="EUR",
            to_symbol="JPY",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "FX_WEEKLY"
        params = call_args[0][1]
        assert params["from_symbol"] == "EUR"
        assert params["to_symbol"] == "JPY"

    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_monthly_forex_flow(self, mock_api_request):
        """Test complete flow for monthly forex request."""
        from src.tools.forex_crypto_unified import get_forex_data

        mock_api_request.return_value = (
            "timestamp,open,high,low,close\n2024-01-01,1.3500,1.3600,1.3450,1.3580"
        )

        get_forex_data(
            timeframe="monthly",
            from_symbol="CAD",
            to_symbol="USD",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "FX_MONTHLY"
        params = call_args[0][1]
        assert params["from_symbol"] == "CAD"
        assert params["to_symbol"] == "USD"

    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_forex_validation_error(self, mock_api_request):
        """Test that validation errors are handled properly."""
        from src.tools.forex_crypto_unified import get_forex_data

        # Missing required interval for intraday
        result = get_forex_data(
            timeframe="intraday",
            from_symbol="EUR",
            to_symbol="USD",
            # Missing interval
        )

        # Should return JSON error response
        assert isinstance(result, str)
        error_data = json.loads(result)
        assert error_data["error"] == "Request validation failed"
        assert "validation_errors" in error_data

    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_forex_datatype_json(self, mock_api_request):
        """Test forex with JSON datatype."""
        from src.tools.forex_crypto_unified import get_forex_data

        mock_api_request.return_value = {"Meta Data": {}, "Time Series": {}}

        get_forex_data(
            timeframe="daily",
            from_symbol="EUR",
            to_symbol="USD",
            datatype="json",
        )

        call_args = mock_api_request.call_args
        params = call_args[0][1]
        assert params["datatype"] == "json"


class TestGetCryptoDataIntegration:
    """Integration tests for get_crypto_data tool."""

    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_intraday_timeseries_flow(self, mock_api_request):
        """Test complete flow for intraday crypto timeseries request."""
        from src.tools.forex_crypto_unified import get_crypto_data

        mock_api_request.return_value = (
            "timestamp,open,high,low,close,volume\n2024-01-01,42000,42500,41800,42300,1000"
        )

        result = get_crypto_data(
            data_type="timeseries",
            timeframe="intraday",
            symbol="BTC",
            market="USD",
            interval="5min",
            outputsize="compact",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "CRYPTO_INTRADAY"
        params = call_args[0][1]
        assert params["symbol"] == "BTC"
        assert params["market"] == "USD"
        assert params["interval"] == "5min"
        assert params["outputsize"] == "compact"

        assert isinstance(result, str)
        assert "timestamp" in result

    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_daily_timeseries_flow(self, mock_api_request):
        """Test complete flow for daily crypto timeseries request."""
        from src.tools.forex_crypto_unified import get_crypto_data

        mock_api_request.return_value = (
            "timestamp,open,high,low,close,volume\n2024-01-01,3000,3100,2950,3050,5000"
        )

        get_crypto_data(
            data_type="timeseries",
            timeframe="daily",
            symbol="ETH",
            market="USD",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "DIGITAL_CURRENCY_DAILY"
        params = call_args[0][1]
        assert params["symbol"] == "ETH"
        assert params["market"] == "USD"

    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_weekly_timeseries_flow(self, mock_api_request):
        """Test complete flow for weekly crypto timeseries request."""
        from src.tools.forex_crypto_unified import get_crypto_data

        mock_api_request.return_value = (
            "timestamp,open,high,low,close,volume\n2024-01-01,0.50,0.52,0.48,0.51,10000"
        )

        get_crypto_data(
            data_type="timeseries",
            timeframe="weekly",
            symbol="XRP",
            market="EUR",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "DIGITAL_CURRENCY_WEEKLY"
        params = call_args[0][1]
        assert params["symbol"] == "XRP"
        assert params["market"] == "EUR"

    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_monthly_timeseries_flow(self, mock_api_request):
        """Test complete flow for monthly crypto timeseries request."""
        from src.tools.forex_crypto_unified import get_crypto_data

        mock_api_request.return_value = (
            "timestamp,open,high,low,close,volume\n2024-01-01,80,85,78,83,8000"
        )

        get_crypto_data(
            data_type="timeseries",
            timeframe="monthly",
            symbol="LTC",
            market="CNY",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "DIGITAL_CURRENCY_MONTHLY"
        params = call_args[0][1]
        assert params["symbol"] == "LTC"
        assert params["market"] == "CNY"

    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_exchange_rate_flow(self, mock_api_request):
        """Test complete flow for crypto exchange rate request."""
        from src.tools.forex_crypto_unified import get_crypto_data

        mock_api_request.return_value = "From_Currency,To_Currency,Exchange Rate\nBTC,USD,42500.00"

        result = get_crypto_data(
            data_type="exchange_rate",
            from_currency="BTC",
            to_currency="USD",
        )

        mock_api_request.assert_called_once()
        call_args = mock_api_request.call_args
        assert call_args[0][0] == "CURRENCY_EXCHANGE_RATE"
        params = call_args[0][1]
        assert params["from_currency"] == "BTC"
        assert params["to_currency"] == "USD"

        assert isinstance(result, str)

    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_crypto_validation_error_missing_timeframe(self, mock_api_request):
        """Test that validation errors are handled properly."""
        from src.tools.forex_crypto_unified import get_crypto_data

        # Missing required timeframe for timeseries
        result = get_crypto_data(
            data_type="timeseries",
            symbol="BTC",
            market="USD",
            # Missing timeframe
        )

        assert isinstance(result, str)
        error_data = json.loads(result)
        assert error_data["error"] == "Request validation failed"
        assert "validation_errors" in error_data

    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_crypto_validation_error_missing_interval(self, mock_api_request):
        """Test validation error for missing interval in intraday."""
        from src.tools.forex_crypto_unified import get_crypto_data

        result = get_crypto_data(
            data_type="timeseries",
            timeframe="intraday",
            symbol="BTC",
            market="USD",
            # Missing interval
        )

        assert isinstance(result, str)
        error_data = json.loads(result)
        assert error_data["error"] == "Request validation failed"

    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_crypto_exchange_rate_crypto_to_fiat(self, mock_api_request):
        """Test exchange rate from crypto to fiat."""
        from src.tools.forex_crypto_unified import get_crypto_data

        mock_api_request.return_value = "BTC,USD,42000.00"

        get_crypto_data(
            data_type="exchange_rate",
            from_currency="BTC",
            to_currency="USD",
        )

        call_args = mock_api_request.call_args
        params = call_args[0][1]
        assert params["from_currency"] == "BTC"
        assert params["to_currency"] == "USD"

    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_crypto_exchange_rate_fiat_to_crypto(self, mock_api_request):
        """Test exchange rate from fiat to crypto."""
        from src.tools.forex_crypto_unified import get_crypto_data

        mock_api_request.return_value = "USD,BTC,0.0000238"

        get_crypto_data(
            data_type="exchange_rate",
            from_currency="USD",
            to_currency="BTC",
        )

        call_args = mock_api_request.call_args
        params = call_args[0][1]
        assert params["from_currency"] == "USD"
        assert params["to_currency"] == "BTC"

    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_crypto_datatype_json(self, mock_api_request):
        """Test crypto with JSON datatype."""
        from src.tools.forex_crypto_unified import get_crypto_data

        mock_api_request.return_value = {"Meta Data": {}, "Time Series": {}}

        get_crypto_data(
            data_type="timeseries",
            timeframe="daily",
            symbol="BTC",
            market="USD",
            datatype="json",
        )

        call_args = mock_api_request.call_args
        params = call_args[0][1]
        assert params["datatype"] == "json"


class TestParameterizedIntegration:
    """Parameterized integration tests."""

    @pytest.mark.parametrize(
        "timeframe,expected_function",
        [
            ("intraday", "FX_INTRADAY"),
            ("daily", "FX_DAILY"),
            ("weekly", "FX_WEEKLY"),
            ("monthly", "FX_MONTHLY"),
        ],
    )
    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_all_forex_timeframes_integration(self, mock_api_request, timeframe, expected_function):
        """Test all forex timeframes integrate correctly."""
        from src.tools.forex_crypto_unified import get_forex_data

        mock_api_request.return_value = "timestamp,open,high,low,close\n"

        params = {
            "timeframe": timeframe,
            "from_symbol": "EUR",
            "to_symbol": "USD",
        }
        if timeframe == "intraday":
            params["interval"] = "5min"

        get_forex_data(**params)

        call_args = mock_api_request.call_args
        assert call_args[0][0] == expected_function

    @pytest.mark.parametrize(
        "data_type,timeframe,expected_function",
        [
            ("timeseries", "intraday", "CRYPTO_INTRADAY"),
            ("timeseries", "daily", "DIGITAL_CURRENCY_DAILY"),
            ("timeseries", "weekly", "DIGITAL_CURRENCY_WEEKLY"),
            ("timeseries", "monthly", "DIGITAL_CURRENCY_MONTHLY"),
            ("exchange_rate", None, "CURRENCY_EXCHANGE_RATE"),
        ],
    )
    @patch("src.tools.forex_crypto_unified._make_api_request")
    def test_all_crypto_types_integration(
        self, mock_api_request, data_type, timeframe, expected_function
    ):
        """Test all crypto data types integrate correctly."""
        from src.tools.forex_crypto_unified import get_crypto_data

        mock_api_request.return_value = "data"

        params = {"data_type": data_type}
        if data_type == "timeseries":
            params["timeframe"] = timeframe
            params["symbol"] = "BTC"
            params["market"] = "USD"
            if timeframe == "intraday":
                params["interval"] = "5min"
        else:
            params["from_currency"] = "BTC"
            params["to_currency"] = "USD"

        get_crypto_data(**params)

        call_args = mock_api_request.call_args
        assert call_args[0][0] == expected_function
