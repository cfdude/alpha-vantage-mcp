"""
Unit tests for CryptoRequest schema validation.

Tests cover:
- Parameter validation for timeseries and exchange_rate data types
- Conditional requirements enforcement
- Invalid parameter combinations
- Edge cases and error messages
"""

import pytest
from pydantic import ValidationError

from src.tools.crypto_schema import CryptoRequest


class TestIntradayTimeseries:
    """Test intraday timeseries validation."""

    def test_valid_intraday_timeseries(self):
        """Test valid intraday timeseries request."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="intraday",
            symbol="BTC",
            market="USD",
            interval="5min",
            outputsize="compact",
        )
        assert request.data_type == "timeseries"
        assert request.timeframe == "intraday"
        assert request.symbol == "BTC"
        assert request.market == "USD"
        assert request.interval == "5min"
        assert request.outputsize == "compact"

    def test_intraday_timeseries_missing_interval(self):
        """Test intraday timeseries fails without interval."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoRequest(
                data_type="timeseries",
                timeframe="intraday",
                symbol="BTC",
                market="USD",
            )
        errors = exc_info.value.errors()
        assert any("interval is required" in str(err) for err in errors)

    def test_intraday_timeseries_all_intervals(self):
        """Test all valid interval values."""
        intervals = ["1min", "5min", "15min", "30min", "60min"]
        for interval in intervals:
            request = CryptoRequest(
                data_type="timeseries",
                timeframe="intraday",
                symbol="BTC",
                market="USD",
                interval=interval,
            )
            assert request.interval == interval


class TestDailyTimeseries:
    """Test daily timeseries validation."""

    def test_valid_daily_timeseries(self):
        """Test valid daily timeseries request."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="daily",
            symbol="ETH",
            market="USD",
        )
        assert request.data_type == "timeseries"
        assert request.timeframe == "daily"
        assert request.symbol == "ETH"
        assert request.market == "USD"

    def test_daily_timeseries_with_interval_rejected(self):
        """Test daily timeseries rejects interval parameter."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoRequest(
                data_type="timeseries",
                timeframe="daily",
                symbol="BTC",
                market="USD",
                interval="5min",  # Should not be provided for daily
            )
        errors = exc_info.value.errors()
        assert any("not applicable" in str(err) for err in errors)


class TestWeeklyTimeseries:
    """Test weekly timeseries validation."""

    def test_valid_weekly_timeseries(self):
        """Test valid weekly timeseries request."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="weekly",
            symbol="XRP",
            market="EUR",
        )
        assert request.data_type == "timeseries"
        assert request.timeframe == "weekly"
        assert request.symbol == "XRP"
        assert request.market == "EUR"

    def test_weekly_timeseries_with_interval_rejected(self):
        """Test weekly timeseries rejects interval parameter."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoRequest(
                data_type="timeseries",
                timeframe="weekly",
                symbol="BTC",
                market="USD",
                interval="5min",
            )
        errors = exc_info.value.errors()
        assert any("not applicable" in str(err) for err in errors)


class TestMonthlyTimeseries:
    """Test monthly timeseries validation."""

    def test_valid_monthly_timeseries(self):
        """Test valid monthly timeseries request."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="monthly",
            symbol="LTC",
            market="CNY",
        )
        assert request.data_type == "timeseries"
        assert request.timeframe == "monthly"
        assert request.symbol == "LTC"
        assert request.market == "CNY"


class TestTimeseriesRequirements:
    """Test timeseries parameter requirements."""

    def test_timeseries_missing_timeframe(self):
        """Test timeseries fails without timeframe."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoRequest(
                data_type="timeseries",
                symbol="BTC",
                market="USD",
            )
        errors = exc_info.value.errors()
        assert any("timeframe is required" in str(err) for err in errors)

    def test_timeseries_missing_symbol(self):
        """Test timeseries fails without symbol."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoRequest(
                data_type="timeseries",
                timeframe="daily",
                market="USD",
            )
        errors = exc_info.value.errors()
        assert any("symbol is required" in str(err) for err in errors)

    def test_timeseries_missing_market(self):
        """Test timeseries fails without market."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoRequest(
                data_type="timeseries",
                timeframe="daily",
                symbol="BTC",
            )
        errors = exc_info.value.errors()
        assert any("market is required" in str(err) for err in errors)


class TestExchangeRate:
    """Test exchange_rate data type validation."""

    def test_valid_exchange_rate_crypto_to_fiat(self):
        """Test valid crypto to fiat exchange rate."""
        request = CryptoRequest(
            data_type="exchange_rate",
            from_currency="BTC",
            to_currency="USD",
        )
        assert request.data_type == "exchange_rate"
        assert request.from_currency == "BTC"
        assert request.to_currency == "USD"

    def test_valid_exchange_rate_fiat_to_crypto(self):
        """Test valid fiat to crypto exchange rate."""
        request = CryptoRequest(
            data_type="exchange_rate",
            from_currency="USD",
            to_currency="BTC",
        )
        assert request.from_currency == "USD"
        assert request.to_currency == "BTC"

    def test_valid_exchange_rate_crypto_to_crypto(self):
        """Test valid crypto to crypto exchange rate."""
        request = CryptoRequest(
            data_type="exchange_rate",
            from_currency="BTC",
            to_currency="ETH",
        )
        assert request.from_currency == "BTC"
        assert request.to_currency == "ETH"

    def test_exchange_rate_missing_from_currency(self):
        """Test exchange_rate fails without from_currency."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoRequest(
                data_type="exchange_rate",
                to_currency="USD",
            )
        errors = exc_info.value.errors()
        assert any("from_currency is required" in str(err) for err in errors)

    def test_exchange_rate_missing_to_currency(self):
        """Test exchange_rate fails without to_currency."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoRequest(
                data_type="exchange_rate",
                from_currency="BTC",
            )
        errors = exc_info.value.errors()
        assert any("to_currency is required" in str(err) for err in errors)

    def test_exchange_rate_with_timeframe_rejected(self):
        """Test exchange_rate rejects timeframe parameter."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoRequest(
                data_type="exchange_rate",
                from_currency="BTC",
                to_currency="USD",
                timeframe="daily",  # Should not be provided
            )
        errors = exc_info.value.errors()
        assert any("not applicable" in str(err) for err in errors)

    def test_exchange_rate_with_symbol_rejected(self):
        """Test exchange_rate rejects symbol/market parameters."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoRequest(
                data_type="exchange_rate",
                from_currency="BTC",
                to_currency="USD",
                symbol="BTC",  # Should not be provided
                market="USD",
            )
        errors = exc_info.value.errors()
        assert any("only applicable for data_type='timeseries'" in str(err) for err in errors)

    def test_exchange_rate_with_interval_rejected(self):
        """Test exchange_rate rejects interval parameter."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoRequest(
                data_type="exchange_rate",
                from_currency="BTC",
                to_currency="USD",
                interval="5min",
            )
        errors = exc_info.value.errors()
        assert any("not applicable" in str(err) for err in errors)


class TestOutputControls:
    """Test output control parameters."""

    def test_force_inline(self):
        """Test force_inline parameter."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="daily",
            symbol="BTC",
            market="USD",
            force_inline=True,
        )
        assert request.force_inline is True
        assert request.force_file is False

    def test_force_file(self):
        """Test force_file parameter."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="daily",
            symbol="BTC",
            market="USD",
            force_file=True,
        )
        assert request.force_file is True
        assert request.force_inline is False

    def test_force_inline_and_force_file_mutually_exclusive(self):
        """Test that force_inline and force_file cannot both be True."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoRequest(
                data_type="timeseries",
                timeframe="daily",
                symbol="BTC",
                market="USD",
                force_inline=True,
                force_file=True,
            )
        errors = exc_info.value.errors()
        assert any("mutually exclusive" in str(err) for err in errors)


class TestDatatype:
    """Test datatype parameter."""

    def test_datatype_json(self):
        """Test datatype=json."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="daily",
            symbol="BTC",
            market="USD",
            datatype="json",
        )
        assert request.datatype == "json"

    def test_datatype_csv_default(self):
        """Test datatype=csv (default)."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="daily",
            symbol="BTC",
            market="USD",
        )
        assert request.datatype == "csv"


class TestParameterizedValidation:
    """Parameterized tests for all data types and timeframes."""

    @pytest.mark.parametrize(
        "data_type,timeframe,required_params",
        [
            (
                "timeseries",
                "intraday",
                {"symbol": "BTC", "market": "USD", "interval": "5min"},
            ),
            ("timeseries", "daily", {"symbol": "ETH", "market": "USD"}),
            ("timeseries", "weekly", {"symbol": "XRP", "market": "EUR"}),
            ("timeseries", "monthly", {"symbol": "LTC", "market": "CNY"}),
            ("exchange_rate", None, {"from_currency": "BTC", "to_currency": "USD"}),
        ],
    )
    def test_all_data_types_valid(self, data_type, timeframe, required_params):
        """Test all data types and timeframes with valid parameters."""
        all_params = {"data_type": data_type}
        if timeframe:
            all_params["timeframe"] = timeframe
        all_params.update(required_params)
        request = CryptoRequest(**all_params)
        assert request.data_type == data_type

    @pytest.mark.parametrize(
        "symbol,market",
        [
            ("BTC", "USD"),
            ("ETH", "EUR"),
            ("XRP", "CNY"),
            ("LTC", "JPY"),
            ("ADA", "GBP"),
        ],
    )
    def test_various_crypto_pairs(self, symbol, market):
        """Test various crypto/market pairs."""
        request = CryptoRequest(
            data_type="timeseries",
            timeframe="daily",
            symbol=symbol,
            market=market,
        )
        assert request.symbol == symbol
        assert request.market == market


class TestCrossValidation:
    """Test cross-validation between parameters."""

    def test_timeseries_cannot_use_exchange_rate_params(self):
        """Test timeseries rejects exchange rate parameters."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoRequest(
                data_type="timeseries",
                timeframe="daily",
                symbol="BTC",
                market="USD",
                from_currency="BTC",  # Wrong for timeseries
            )
        errors = exc_info.value.errors()
        assert any("only applicable for data_type='exchange_rate'" in str(err) for err in errors)

    def test_exchange_rate_cannot_use_timeseries_params(self):
        """Test exchange_rate rejects timeseries parameters."""
        with pytest.raises(ValidationError) as exc_info:
            CryptoRequest(
                data_type="exchange_rate",
                from_currency="BTC",
                to_currency="USD",
                symbol="BTC",  # Wrong for exchange_rate
            )
        errors = exc_info.value.errors()
        assert any("only applicable for data_type='timeseries'" in str(err) for err in errors)
