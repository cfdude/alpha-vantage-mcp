"""
Unit tests for forex and crypto routing logic.

Tests cover:
- API function name mapping
- Parameter transformation
- Routing validation
- Edge cases and error handling
"""

import pytest

from src.tools.crypto_schema import CryptoRequest
from src.tools.forex_crypto_router import (
    get_crypto_api_function_name,
    get_forex_api_function_name,
    route_crypto_request,
    route_forex_request,
    transform_crypto_params,
    transform_forex_params,
    validate_crypto_routing,
    validate_forex_routing,
)
from src.tools.forex_schema import ForexRequest


class TestForexFunctionMapping:
    """Test forex timeframe to API function mapping."""

    def test_intraday_function_name(self):
        """Test intraday maps to FX_INTRADAY."""
        assert get_forex_api_function_name("intraday") == "FX_INTRADAY"

    def test_daily_function_name(self):
        """Test daily maps to FX_DAILY."""
        assert get_forex_api_function_name("daily") == "FX_DAILY"

    def test_weekly_function_name(self):
        """Test weekly maps to FX_WEEKLY."""
        assert get_forex_api_function_name("weekly") == "FX_WEEKLY"

    def test_monthly_function_name(self):
        """Test monthly maps to FX_MONTHLY."""
        assert get_forex_api_function_name("monthly") == "FX_MONTHLY"

    def test_invalid_timeframe(self):
        """Test invalid timeframe raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_forex_api_function_name("hourly")
        assert "Unknown forex timeframe" in str(exc_info.value)


class TestCryptoFunctionMapping:
    """Test crypto data_type/timeframe to API function mapping."""

    def test_intraday_timeseries_function_name(self):
        """Test intraday timeseries maps to CRYPTO_INTRADAY."""
        assert get_crypto_api_function_name("timeseries", "intraday") == "CRYPTO_INTRADAY"

    def test_daily_timeseries_function_name(self):
        """Test daily timeseries maps to DIGITAL_CURRENCY_DAILY."""
        assert get_crypto_api_function_name("timeseries", "daily") == "DIGITAL_CURRENCY_DAILY"

    def test_weekly_timeseries_function_name(self):
        """Test weekly timeseries maps to DIGITAL_CURRENCY_WEEKLY."""
        assert get_crypto_api_function_name("timeseries", "weekly") == "DIGITAL_CURRENCY_WEEKLY"

    def test_monthly_timeseries_function_name(self):
        """Test monthly timeseries maps to DIGITAL_CURRENCY_MONTHLY."""
        assert get_crypto_api_function_name("timeseries", "monthly") == "DIGITAL_CURRENCY_MONTHLY"

    def test_exchange_rate_function_name(self):
        """Test exchange_rate maps to CURRENCY_EXCHANGE_RATE."""
        assert get_crypto_api_function_name("exchange_rate", None) == "CURRENCY_EXCHANGE_RATE"

    def test_invalid_combination(self):
        """Test invalid data_type/timeframe combination raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_crypto_api_function_name("timeseries", "hourly")
        assert "Unknown crypto data_type/timeframe combination" in str(exc_info.value)


class TestForexParameterTransformation:
    """Test forex parameter transformation."""

    def test_transform_intraday_params(self):
        """Test transformation of intraday forex parameters."""
        request = ForexRequest(
            timeframe="intraday",
            from_symbol="EUR",
            to_symbol="USD",
            interval="5min",
            outputsize="compact",
            datatype="csv",
        )
        params = transform_forex_params(request)

        assert params["from_symbol"] == "EUR"
        assert params["to_symbol"] == "USD"
        assert params["interval"] == "5min"
        assert params["outputsize"] == "compact"
        assert params["datatype"] == "csv"

    def test_transform_daily_params(self):
        """Test transformation of daily forex parameters."""
        request = ForexRequest(
            timeframe="daily",
            from_symbol="GBP",
            to_symbol="USD",
            outputsize="full",
            datatype="json",
        )
        params = transform_forex_params(request)

        assert params["from_symbol"] == "GBP"
        assert params["to_symbol"] == "USD"
        assert params["outputsize"] == "full"
        assert params["datatype"] == "json"
        assert "interval" not in params

    def test_transform_weekly_params(self):
        """Test transformation of weekly forex parameters."""
        request = ForexRequest(
            timeframe="weekly",
            from_symbol="EUR",
            to_symbol="JPY",
        )
        params = transform_forex_params(request)

        assert params["from_symbol"] == "EUR"
        assert params["to_symbol"] == "JPY"
        assert params["datatype"] == "csv"
        assert "interval" not in params
        assert "outputsize" not in params or params["outputsize"] == "compact"

    def test_transform_monthly_params(self):
        """Test transformation of monthly forex parameters."""
        request = ForexRequest(
            timeframe="monthly",
            from_symbol="CAD",
            to_symbol="USD",
        )
        params = transform_forex_params(request)

        assert params["from_symbol"] == "CAD"
        assert params["to_symbol"] == "USD"
        assert "interval" not in params


class TestCryptoParameterTransformation:
    """Test crypto parameter transformation."""

    def test_transform_intraday_timeseries_params(self):
        """Test transformation of intraday timeseries parameters."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="intraday",
            symbol="BTC",
            market="USD",
            interval="5min",
            outputsize="compact",
        )
        params = transform_crypto_params(request)

        assert params["symbol"] == "BTC"
        assert params["market"] == "USD"
        assert params["interval"] == "5min"
        assert params["outputsize"] == "compact"
        assert params["datatype"] == "csv"

    def test_transform_daily_timeseries_params(self):
        """Test transformation of daily timeseries parameters."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="daily",
            symbol="ETH",
            market="USD",
            datatype="json",
        )
        params = transform_crypto_params(request)

        assert params["symbol"] == "ETH"
        assert params["market"] == "USD"
        assert params["datatype"] == "json"
        assert "interval" not in params

    def test_transform_weekly_timeseries_params(self):
        """Test transformation of weekly timeseries parameters."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="weekly",
            symbol="XRP",
            market="EUR",
        )
        params = transform_crypto_params(request)

        assert params["symbol"] == "XRP"
        assert params["market"] == "EUR"
        assert "interval" not in params

    def test_transform_exchange_rate_params(self):
        """Test transformation of exchange rate parameters."""
        request = CryptoRequest(
            data_type="exchange_rate",
            from_currency="BTC",
            to_currency="USD",
        )
        params = transform_crypto_params(request)

        assert params["from_currency"] == "BTC"
        assert params["to_currency"] == "USD"
        assert params["datatype"] == "csv"
        assert "symbol" not in params
        assert "market" not in params


class TestForexRoutingValidation:
    """Test forex routing validation."""

    def test_valid_intraday_routing(self):
        """Test valid intraday request passes routing validation."""
        request = ForexRequest(
            timeframe="intraday",
            from_symbol="EUR",
            to_symbol="USD",
            interval="5min",
        )
        # Should not raise any exception
        validate_forex_routing(request)

    def test_valid_daily_routing(self):
        """Test valid daily request passes routing validation."""
        request = ForexRequest(
            timeframe="daily",
            from_symbol="EUR",
            to_symbol="USD",
        )
        # Should not raise any exception
        validate_forex_routing(request)


class TestCryptoRoutingValidation:
    """Test crypto routing validation."""

    def test_valid_intraday_timeseries_routing(self):
        """Test valid intraday timeseries passes routing validation."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="intraday",
            symbol="BTC",
            market="USD",
            interval="5min",
        )
        # Should not raise any exception
        validate_crypto_routing(request)

    def test_valid_daily_timeseries_routing(self):
        """Test valid daily timeseries passes routing validation."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="daily",
            symbol="ETH",
            market="USD",
        )
        # Should not raise any exception
        validate_crypto_routing(request)

    def test_valid_exchange_rate_routing(self):
        """Test valid exchange rate passes routing validation."""
        request = CryptoRequest(
            data_type="exchange_rate",
            from_currency="BTC",
            to_currency="USD",
        )
        # Should not raise any exception
        validate_crypto_routing(request)


class TestForexRouteRequest:
    """Test complete forex request routing."""

    def test_route_intraday_request(self):
        """Test routing intraday forex request."""
        request = ForexRequest(
            timeframe="intraday",
            from_symbol="EUR",
            to_symbol="USD",
            interval="5min",
            outputsize="compact",
        )
        function_name, params = route_forex_request(request)

        assert function_name == "FX_INTRADAY"
        assert params["from_symbol"] == "EUR"
        assert params["to_symbol"] == "USD"
        assert params["interval"] == "5min"
        assert params["outputsize"] == "compact"

    def test_route_daily_request(self):
        """Test routing daily forex request."""
        request = ForexRequest(
            timeframe="daily",
            from_symbol="GBP",
            to_symbol="USD",
            outputsize="full",
        )
        function_name, params = route_forex_request(request)

        assert function_name == "FX_DAILY"
        assert params["from_symbol"] == "GBP"
        assert params["to_symbol"] == "USD"
        assert params["outputsize"] == "full"

    def test_route_weekly_request(self):
        """Test routing weekly forex request."""
        request = ForexRequest(
            timeframe="weekly",
            from_symbol="EUR",
            to_symbol="JPY",
        )
        function_name, params = route_forex_request(request)

        assert function_name == "FX_WEEKLY"
        assert params["from_symbol"] == "EUR"
        assert params["to_symbol"] == "JPY"

    def test_route_monthly_request(self):
        """Test routing monthly forex request."""
        request = ForexRequest(
            timeframe="monthly",
            from_symbol="CAD",
            to_symbol="USD",
        )
        function_name, params = route_forex_request(request)

        assert function_name == "FX_MONTHLY"
        assert params["from_symbol"] == "CAD"
        assert params["to_symbol"] == "USD"


class TestCryptoRouteRequest:
    """Test complete crypto request routing."""

    def test_route_intraday_timeseries_request(self):
        """Test routing intraday timeseries request."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="intraday",
            symbol="BTC",
            market="USD",
            interval="5min",
            outputsize="compact",
        )
        function_name, params = route_crypto_request(request)

        assert function_name == "CRYPTO_INTRADAY"
        assert params["symbol"] == "BTC"
        assert params["market"] == "USD"
        assert params["interval"] == "5min"
        assert params["outputsize"] == "compact"

    def test_route_daily_timeseries_request(self):
        """Test routing daily timeseries request."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="daily",
            symbol="ETH",
            market="USD",
        )
        function_name, params = route_crypto_request(request)

        assert function_name == "DIGITAL_CURRENCY_DAILY"
        assert params["symbol"] == "ETH"
        assert params["market"] == "USD"

    def test_route_weekly_timeseries_request(self):
        """Test routing weekly timeseries request."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="weekly",
            symbol="XRP",
            market="EUR",
        )
        function_name, params = route_crypto_request(request)

        assert function_name == "DIGITAL_CURRENCY_WEEKLY"
        assert params["symbol"] == "XRP"
        assert params["market"] == "EUR"

    def test_route_monthly_timeseries_request(self):
        """Test routing monthly timeseries request."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="monthly",
            symbol="LTC",
            market="CNY",
        )
        function_name, params = route_crypto_request(request)

        assert function_name == "DIGITAL_CURRENCY_MONTHLY"
        assert params["symbol"] == "LTC"
        assert params["market"] == "CNY"

    def test_route_exchange_rate_request(self):
        """Test routing exchange rate request."""
        request = CryptoRequest(
            data_type="exchange_rate",
            from_currency="BTC",
            to_currency="USD",
        )
        function_name, params = route_crypto_request(request)

        assert function_name == "CURRENCY_EXCHANGE_RATE"
        assert params["from_currency"] == "BTC"
        assert params["to_currency"] == "USD"


class TestParameterizedRouting:
    """Parameterized tests for routing logic."""

    @pytest.mark.parametrize(
        "timeframe,expected_function",
        [
            ("intraday", "FX_INTRADAY"),
            ("daily", "FX_DAILY"),
            ("weekly", "FX_WEEKLY"),
            ("monthly", "FX_MONTHLY"),
        ],
    )
    def test_all_forex_timeframes_route_correctly(self, timeframe, expected_function):
        """Test all forex timeframes route to correct function."""
        params = {
            "timeframe": timeframe,
            "from_symbol": "EUR",
            "to_symbol": "USD",
        }
        if timeframe == "intraday":
            params["interval"] = "5min"

        request = ForexRequest(**params)
        function_name, _ = route_forex_request(request)
        assert function_name == expected_function

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
    def test_all_crypto_types_route_correctly(self, data_type, timeframe, expected_function):
        """Test all crypto data types route to correct function."""
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

        request = CryptoRequest(**params)
        function_name, _ = route_crypto_request(request)
        assert function_name == expected_function
