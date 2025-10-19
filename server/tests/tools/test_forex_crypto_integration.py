"""
Integration tests for unified forex and crypto tools.

These tests verify the end-to-end flow from tool invocation through
routing to API call (mocked).

NOTE: These tests use sys.modules mocking to avoid import errors
from dependencies that may not be initialized during test collection.
"""

import json
import sys
from unittest.mock import MagicMock

import pytest


# Mock the problematic imports BEFORE importing our module
@pytest.fixture(scope="module", autouse=True)
def mock_dependencies():
    """Mock src.common and dependencies to avoid import errors."""
    # Create mock modules
    mock_utils = MagicMock()
    mock_utils.estimate_tokens = MagicMock()
    mock_utils.upload_to_r2 = MagicMock()

    mock_common = MagicMock()
    mock_common._make_api_request = MagicMock()

    mock_registry = MagicMock()
    mock_registry.tool = lambda func: func  # Decorator passthrough

    # Inject mocks into sys.modules
    sys.modules["src.utils"] = mock_utils
    sys.modules["src.common"] = mock_common
    sys.modules["src.tools.registry"] = mock_registry

    yield

    # Cleanup (optional, but good practice)
    if "src.utils" in sys.modules:
        del sys.modules["src.utils"]
    if "src.common" in sys.modules:
        del sys.modules["src.common"]
    if "src.tools.registry" in sys.modules:
        del sys.modules["src.tools.registry"]


class TestGetForexDataIntegration:
    """Integration tests for get_forex_data tool."""

    def test_intraday_forex_flow(self):
        """Test complete flow for intraday forex request."""
        # Import after mocks are in place
        from src.tools.forex_crypto_unified import _make_api_request, get_forex_data

        # Mock the API response
        _make_api_request.return_value = (
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
        _make_api_request.assert_called_once()
        call_args = _make_api_request.call_args
        assert call_args[0][0] == "FX_INTRADAY"
        params = call_args[0][1]
        assert params["from_symbol"] == "EUR"
        assert params["to_symbol"] == "USD"
        assert params["interval"] == "5min"
        assert params["outputsize"] == "compact"

        # Verify result
        assert isinstance(result, str)
        assert "timestamp" in result

        # Reset mock for next test
        _make_api_request.reset_mock()

    def test_daily_forex_flow(self):
        """Test complete flow for daily forex request."""
        from src.tools.forex_crypto_unified import _make_api_request, get_forex_data

        _make_api_request.return_value = (
            "timestamp,open,high,low,close\n2024-01-01,1.2500,1.2550,1.2480,1.2530"
        )

        get_forex_data(
            timeframe="daily",
            from_symbol="GBP",
            to_symbol="USD",
            outputsize="full",
        )

        _make_api_request.assert_called_once()
        call_args = _make_api_request.call_args
        assert call_args[0][0] == "FX_DAILY"
        params = call_args[0][1]
        assert params["from_symbol"] == "GBP"
        assert params["to_symbol"] == "USD"
        assert params["outputsize"] == "full"

        _make_api_request.reset_mock()

    def test_weekly_forex_flow(self):
        """Test complete flow for weekly forex request."""
        from src.tools.forex_crypto_unified import _make_api_request, get_forex_data

        _make_api_request.return_value = (
            "timestamp,open,high,low,close\n2024-01-01,130.50,131.20,129.80,130.90"
        )

        get_forex_data(
            timeframe="weekly",
            from_symbol="EUR",
            to_symbol="JPY",
        )

        _make_api_request.assert_called_once()
        call_args = _make_api_request.call_args
        assert call_args[0][0] == "FX_WEEKLY"
        params = call_args[0][1]
        assert params["from_symbol"] == "EUR"
        assert params["to_symbol"] == "JPY"

        _make_api_request.reset_mock()

    def test_monthly_forex_flow(self):
        """Test complete flow for monthly forex request."""
        from src.tools.forex_crypto_unified import _make_api_request, get_forex_data

        _make_api_request.return_value = (
            "timestamp,open,high,low,close\n2024-01-01,1.3500,1.3600,1.3450,1.3580"
        )

        get_forex_data(
            timeframe="monthly",
            from_symbol="CAD",
            to_symbol="USD",
        )

        _make_api_request.assert_called_once()
        call_args = _make_api_request.call_args
        assert call_args[0][0] == "FX_MONTHLY"
        params = call_args[0][1]
        assert params["from_symbol"] == "CAD"
        assert params["to_symbol"] == "USD"

        _make_api_request.reset_mock()

    def test_forex_validation_error(self):
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

    def test_forex_datatype_json(self):
        """Test forex with JSON datatype."""
        from src.tools.forex_crypto_unified import _make_api_request, get_forex_data

        _make_api_request.return_value = {"Meta Data": {}, "Time Series": {}}

        get_forex_data(
            timeframe="daily",
            from_symbol="EUR",
            to_symbol="USD",
            datatype="json",
        )

        call_args = _make_api_request.call_args
        params = call_args[0][1]
        assert params["datatype"] == "json"

        _make_api_request.reset_mock()


class TestGetCryptoDataIntegration:
    """Integration tests for get_crypto_data tool."""

    def test_intraday_timeseries_flow(self):
        """Test complete flow for intraday crypto timeseries request."""
        from src.tools.forex_crypto_unified import _make_api_request, get_crypto_data

        _make_api_request.return_value = (
            "timestamp,open,high,low,close,volume\n" "2024-01-01,42000,42500,41800,42300,1000"
        )

        result = get_crypto_data(
            data_type="timeseries",
            timeframe="intraday",
            symbol="BTC",
            market="USD",
            interval="5min",
            outputsize="compact",
        )

        _make_api_request.assert_called_once()
        call_args = _make_api_request.call_args
        assert call_args[0][0] == "CRYPTO_INTRADAY"
        params = call_args[0][1]
        assert params["symbol"] == "BTC"
        assert params["market"] == "USD"
        assert params["interval"] == "5min"
        assert params["outputsize"] == "compact"

        assert isinstance(result, str)
        assert "timestamp" in result

        _make_api_request.reset_mock()

    def test_daily_timeseries_flow(self):
        """Test complete flow for daily crypto timeseries request."""
        from src.tools.forex_crypto_unified import _make_api_request, get_crypto_data

        _make_api_request.return_value = (
            "timestamp,open,high,low,close,volume\n" "2024-01-01,3000,3100,2950,3050,5000"
        )

        get_crypto_data(
            data_type="timeseries",
            timeframe="daily",
            symbol="ETH",
            market="USD",
        )

        _make_api_request.assert_called_once()
        call_args = _make_api_request.call_args
        assert call_args[0][0] == "DIGITAL_CURRENCY_DAILY"
        params = call_args[0][1]
        assert params["symbol"] == "ETH"
        assert params["market"] == "USD"

        _make_api_request.reset_mock()

    def test_weekly_timeseries_flow(self):
        """Test complete flow for weekly crypto timeseries request."""
        from src.tools.forex_crypto_unified import _make_api_request, get_crypto_data

        _make_api_request.return_value = (
            "timestamp,open,high,low,close,volume\n" "2024-01-01,0.50,0.52,0.48,0.51,10000"
        )

        get_crypto_data(
            data_type="timeseries",
            timeframe="weekly",
            symbol="XRP",
            market="EUR",
        )

        _make_api_request.assert_called_once()
        call_args = _make_api_request.call_args
        assert call_args[0][0] == "DIGITAL_CURRENCY_WEEKLY"
        params = call_args[0][1]
        assert params["symbol"] == "XRP"
        assert params["market"] == "EUR"

        _make_api_request.reset_mock()

    def test_monthly_timeseries_flow(self):
        """Test complete flow for monthly crypto timeseries request."""
        from src.tools.forex_crypto_unified import _make_api_request, get_crypto_data

        _make_api_request.return_value = (
            "timestamp,open,high,low,close,volume\n" "2024-01-01,80,85,78,83,8000"
        )

        get_crypto_data(
            data_type="timeseries",
            timeframe="monthly",
            symbol="LTC",
            market="CNY",
        )

        _make_api_request.assert_called_once()
        call_args = _make_api_request.call_args
        assert call_args[0][0] == "DIGITAL_CURRENCY_MONTHLY"
        params = call_args[0][1]
        assert params["symbol"] == "LTC"
        assert params["market"] == "CNY"

        _make_api_request.reset_mock()

    def test_exchange_rate_flow(self):
        """Test complete flow for crypto exchange rate request."""
        from src.tools.forex_crypto_unified import _make_api_request, get_crypto_data

        _make_api_request.return_value = "From_Currency,To_Currency,Exchange Rate\nBTC,USD,42500.00"

        result = get_crypto_data(
            data_type="exchange_rate",
            from_currency="BTC",
            to_currency="USD",
        )

        _make_api_request.assert_called_once()
        call_args = _make_api_request.call_args
        assert call_args[0][0] == "CURRENCY_EXCHANGE_RATE"
        params = call_args[0][1]
        assert params["from_currency"] == "BTC"
        assert params["to_currency"] == "USD"

        assert isinstance(result, str)

        _make_api_request.reset_mock()

    def test_crypto_validation_error_missing_timeframe(self):
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

    def test_crypto_validation_error_missing_interval(self):
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

    def test_crypto_exchange_rate_crypto_to_fiat(self):
        """Test exchange rate from crypto to fiat."""
        from src.tools.forex_crypto_unified import _make_api_request, get_crypto_data

        _make_api_request.return_value = "BTC,USD,42000.00"

        get_crypto_data(
            data_type="exchange_rate",
            from_currency="BTC",
            to_currency="USD",
        )

        call_args = _make_api_request.call_args
        params = call_args[0][1]
        assert params["from_currency"] == "BTC"
        assert params["to_currency"] == "USD"

        _make_api_request.reset_mock()

    def test_crypto_exchange_rate_fiat_to_crypto(self):
        """Test exchange rate from fiat to crypto."""
        from src.tools.forex_crypto_unified import _make_api_request, get_crypto_data

        _make_api_request.return_value = "USD,BTC,0.0000238"

        get_crypto_data(
            data_type="exchange_rate",
            from_currency="USD",
            to_currency="BTC",
        )

        call_args = _make_api_request.call_args
        params = call_args[0][1]
        assert params["from_currency"] == "USD"
        assert params["to_currency"] == "BTC"

        _make_api_request.reset_mock()

    def test_crypto_datatype_json(self):
        """Test crypto with JSON datatype."""
        from src.tools.forex_crypto_unified import _make_api_request, get_crypto_data

        _make_api_request.return_value = {"Meta Data": {}, "Time Series": {}}

        get_crypto_data(
            data_type="timeseries",
            timeframe="daily",
            symbol="BTC",
            market="USD",
            datatype="json",
        )

        call_args = _make_api_request.call_args
        params = call_args[0][1]
        assert params["datatype"] == "json"

        _make_api_request.reset_mock()


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
    def test_all_forex_timeframes_integration(self, timeframe, expected_function):
        """Test all forex timeframes integrate correctly."""
        from src.tools.forex_crypto_unified import _make_api_request, get_forex_data

        _make_api_request.return_value = "timestamp,open,high,low,close\n"

        params = {
            "timeframe": timeframe,
            "from_symbol": "EUR",
            "to_symbol": "USD",
        }
        if timeframe == "intraday":
            params["interval"] = "5min"

        get_forex_data(**params)

        call_args = _make_api_request.call_args
        assert call_args[0][0] == expected_function

        _make_api_request.reset_mock()

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
    def test_all_crypto_types_integration(self, data_type, timeframe, expected_function):
        """Test all crypto data types integrate correctly."""
        from src.tools.forex_crypto_unified import _make_api_request, get_crypto_data

        _make_api_request.return_value = "data"

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

        call_args = _make_api_request.call_args
        assert call_args[0][0] == expected_function

        _make_api_request.reset_mock()
