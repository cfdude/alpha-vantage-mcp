"""
Unit tests for OscillatorRequest schema validation.

Tests cover:
- Parameter validation for each of 17 indicator types
- Conditional requirements enforcement for all indicator groups
- Invalid parameter combinations
- Edge cases and error messages
- Heavily parameterized tests for efficiency
"""

import pytest
from pydantic import ValidationError

from src.tools.oscillator_schema import OscillatorRequest


class TestSimplePeriodIndicators:
    """Test simple period oscillators (WILLR, ADX, ADXR, CCI) - just time_period."""

    @pytest.mark.parametrize(
        "indicator_type",
        ["willr", "adx", "adxr", "cci"],
    )
    def test_valid_simple_period_request(self, indicator_type):
        """Test valid request for simple period indicators."""
        request = OscillatorRequest(
            indicator_type=indicator_type,
            symbol="IBM",
            interval="daily",
            time_period=14,
        )
        assert request.indicator_type == indicator_type
        assert request.symbol == "IBM"
        assert request.time_period == 14
        assert request.series_type is None  # Should not be set

    @pytest.mark.parametrize(
        "indicator_type",
        ["willr", "adx", "adxr", "cci"],
    )
    def test_simple_period_missing_time_period(self, indicator_type):
        """Test simple period indicators fail without time_period."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="daily",
            )
        errors = exc_info.value.errors()
        assert any("time_period is required" in str(err) for err in errors)

    @pytest.mark.parametrize(
        "indicator_type",
        ["willr", "adx", "adxr", "cci"],
    )
    def test_simple_period_rejects_series_type(self, indicator_type):
        """Test simple period indicators reject series_type."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="daily",
                time_period=14,
                series_type="close",  # Not valid
            )
        errors = exc_info.value.errors()
        assert any("series_type is not valid" in str(err) for err in errors)


class TestSeriesPeriodIndicators:
    """Test series + period oscillators (RSI, MOM, CMO, ROC, ROCR) - time_period + series_type."""

    @pytest.mark.parametrize(
        "indicator_type",
        ["rsi", "mom", "cmo", "roc", "rocr"],
    )
    def test_valid_series_period_request(self, indicator_type):
        """Test valid request for series + period indicators."""
        request = OscillatorRequest(
            indicator_type=indicator_type,
            symbol="AAPL",
            interval="daily",
            time_period=14,
            series_type="close",
        )
        assert request.indicator_type == indicator_type
        assert request.time_period == 14
        assert request.series_type == "close"

    @pytest.mark.parametrize(
        "indicator_type",
        ["rsi", "mom", "cmo", "roc", "rocr"],
    )
    def test_series_period_missing_time_period(self, indicator_type):
        """Test series + period indicators fail without time_period."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type=indicator_type,
                symbol="AAPL",
                interval="daily",
                series_type="close",
            )
        errors = exc_info.value.errors()
        assert any("time_period is required" in str(err) for err in errors)

    @pytest.mark.parametrize(
        "indicator_type",
        ["rsi", "mom", "cmo", "roc", "rocr"],
    )
    def test_series_period_missing_series_type(self, indicator_type):
        """Test series + period indicators fail without series_type."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type=indicator_type,
                symbol="AAPL",
                interval="daily",
                time_period=14,
            )
        errors = exc_info.value.errors()
        assert any("series_type is required" in str(err) for err in errors)


class TestMACDIndicators:
    """Test MACD family oscillators (MACD, MACDEXT)."""

    def test_valid_macd_request_with_defaults(self):
        """Test MACD with default periods."""
        request = OscillatorRequest(
            indicator_type="macd",
            symbol="MSFT",
            interval="daily",
            series_type="close",
        )
        assert request.indicator_type == "macd"
        assert request.series_type == "close"
        assert request.fastperiod == 12  # Default
        assert request.slowperiod == 26  # Default
        assert request.signalperiod == 9  # Default

    def test_valid_macd_request_with_custom_periods(self):
        """Test MACD with custom periods."""
        request = OscillatorRequest(
            indicator_type="macd",
            symbol="MSFT",
            interval="daily",
            series_type="close",
            fastperiod=8,
            slowperiod=21,
            signalperiod=5,
        )
        assert request.fastperiod == 8
        assert request.slowperiod == 21
        assert request.signalperiod == 5

    def test_macd_missing_series_type(self):
        """Test MACD fails without series_type."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type="macd",
                symbol="MSFT",
                interval="daily",
            )
        errors = exc_info.value.errors()
        assert any("series_type is required" in str(err) for err in errors)

    def test_macd_rejects_time_period(self):
        """Test MACD rejects time_period parameter."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type="macd",
                symbol="MSFT",
                interval="daily",
                series_type="close",
                time_period=14,  # Not valid
            )
        errors = exc_info.value.errors()
        assert any("time_period is not valid" in str(err) for err in errors)

    def test_valid_macdext_request_with_defaults(self):
        """Test MACDEXT with default periods and MA types."""
        request = OscillatorRequest(
            indicator_type="macdext",
            symbol="GOOGL",
            interval="daily",
            series_type="close",
        )
        assert request.indicator_type == "macdext"
        assert request.fastperiod == 12
        assert request.slowperiod == 26
        assert request.signalperiod == 9
        assert request.fastmatype == 0
        assert request.slowmatype == 0
        assert request.signalmatype == 0

    def test_valid_macdext_request_with_custom_params(self):
        """Test MACDEXT with custom periods and MA types."""
        request = OscillatorRequest(
            indicator_type="macdext",
            symbol="GOOGL",
            interval="daily",
            series_type="close",
            fastperiod=8,
            slowperiod=21,
            signalperiod=5,
            fastmatype=1,  # EMA
            slowmatype=2,  # WMA
            signalmatype=3,  # DEMA
        )
        assert request.fastperiod == 8
        assert request.fastmatype == 1
        assert request.slowmatype == 2
        assert request.signalmatype == 3


class TestAPOPPOIndicators:
    """Test APO and PPO oscillators."""

    @pytest.mark.parametrize(
        "indicator_type",
        ["apo", "ppo"],
    )
    def test_valid_apo_ppo_request_with_defaults(self, indicator_type):
        """Test APO/PPO with default periods."""
        request = OscillatorRequest(
            indicator_type=indicator_type,
            symbol="TSLA",
            interval="daily",
            series_type="close",
        )
        assert request.indicator_type == indicator_type
        assert request.series_type == "close"
        assert request.fastperiod == 12
        assert request.slowperiod == 26
        assert request.matype == 0

    @pytest.mark.parametrize(
        "indicator_type",
        ["apo", "ppo"],
    )
    def test_apo_ppo_missing_series_type(self, indicator_type):
        """Test APO/PPO fail without series_type."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type=indicator_type,
                symbol="TSLA",
                interval="daily",
            )
        errors = exc_info.value.errors()
        assert any("series_type is required" in str(err) for err in errors)

    @pytest.mark.parametrize(
        "indicator_type",
        ["apo", "ppo"],
    )
    def test_apo_ppo_rejects_time_period(self, indicator_type):
        """Test APO/PPO reject time_period parameter."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type=indicator_type,
                symbol="TSLA",
                interval="daily",
                series_type="close",
                time_period=14,  # Not valid
            )
        errors = exc_info.value.errors()
        assert any("time_period is not valid" in str(err) for err in errors)


class TestStochasticIndicators:
    """Test stochastic oscillators (STOCH, STOCHF, STOCHRSI)."""

    def test_valid_stoch_request_with_defaults(self):
        """Test STOCH with default periods."""
        request = OscillatorRequest(
            indicator_type="stoch",
            symbol="NVDA",
            interval="daily",
        )
        assert request.indicator_type == "stoch"
        assert request.fastkperiod == 5
        assert request.slowkperiod == 3
        assert request.slowdperiod == 3
        assert request.slowkmatype == 0
        assert request.slowdmatype == 0

    def test_valid_stoch_request_with_custom_params(self):
        """Test STOCH with custom periods and MA types."""
        request = OscillatorRequest(
            indicator_type="stoch",
            symbol="NVDA",
            interval="daily",
            fastkperiod=14,
            slowkperiod=5,
            slowdperiod=5,
            slowkmatype=1,  # EMA
            slowdmatype=2,  # WMA
        )
        assert request.fastkperiod == 14
        assert request.slowkperiod == 5
        assert request.slowdperiod == 5
        assert request.slowkmatype == 1
        assert request.slowdmatype == 2

    def test_stoch_rejects_time_period(self):
        """Test STOCH rejects time_period parameter."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type="stoch",
                symbol="NVDA",
                interval="daily",
                time_period=14,  # Not valid
            )
        errors = exc_info.value.errors()
        assert any("time_period is not valid" in str(err) for err in errors)

    def test_stoch_rejects_series_type(self):
        """Test STOCH rejects series_type parameter."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type="stoch",
                symbol="NVDA",
                interval="daily",
                series_type="close",  # Not valid
            )
        errors = exc_info.value.errors()
        assert any("series_type is not valid" in str(err) for err in errors)

    def test_valid_stochf_request_with_defaults(self):
        """Test STOCHF with default periods."""
        request = OscillatorRequest(
            indicator_type="stochf",
            symbol="AMZN",
            interval="daily",
        )
        assert request.indicator_type == "stochf"
        assert request.fastkperiod == 5
        assert request.fastdperiod == 3
        assert request.fastdmatype == 0

    def test_stochf_rejects_time_period(self):
        """Test STOCHF rejects time_period parameter."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type="stochf",
                symbol="AMZN",
                interval="daily",
                time_period=14,  # Not valid
            )
        errors = exc_info.value.errors()
        assert any("time_period is not valid" in str(err) for err in errors)

    def test_stochf_rejects_series_type(self):
        """Test STOCHF rejects series_type parameter."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type="stochf",
                symbol="AMZN",
                interval="daily",
                series_type="close",  # Not valid
            )
        errors = exc_info.value.errors()
        assert any("series_type is not valid" in str(err) for err in errors)

    def test_valid_stochrsi_request_with_defaults(self):
        """Test STOCHRSI with default stochastic periods."""
        request = OscillatorRequest(
            indicator_type="stochrsi",
            symbol="META",
            interval="daily",
            time_period=14,
            series_type="close",
        )
        assert request.indicator_type == "stochrsi"
        assert request.time_period == 14
        assert request.series_type == "close"
        assert request.fastkperiod == 5
        assert request.fastdperiod == 3
        assert request.fastdmatype == 0

    def test_stochrsi_missing_time_period(self):
        """Test STOCHRSI fails without time_period."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type="stochrsi",
                symbol="META",
                interval="daily",
                series_type="close",
            )
        errors = exc_info.value.errors()
        assert any("time_period is required" in str(err) for err in errors)

    def test_stochrsi_missing_series_type(self):
        """Test STOCHRSI fails without series_type."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type="stochrsi",
                symbol="META",
                interval="daily",
                time_period=14,
            )
        errors = exc_info.value.errors()
        assert any("series_type is required" in str(err) for err in errors)


class TestBalanceOfPowerIndicator:
    """Test BOP (Balance of Power) - no additional parameters."""

    def test_valid_bop_request(self):
        """Test BOP with only required base parameters."""
        request = OscillatorRequest(
            indicator_type="bop",
            symbol="DIS",
            interval="daily",
        )
        assert request.indicator_type == "bop"
        assert request.symbol == "DIS"
        assert request.interval == "daily"
        assert request.time_period is None
        assert request.series_type is None

    def test_bop_rejects_time_period(self):
        """Test BOP rejects time_period parameter."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type="bop",
                symbol="DIS",
                interval="daily",
                time_period=14,  # Not valid
            )
        errors = exc_info.value.errors()
        assert any("time_period is not valid" in str(err) for err in errors)

    def test_bop_rejects_series_type(self):
        """Test BOP rejects series_type parameter."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type="bop",
                symbol="DIS",
                interval="daily",
                series_type="close",  # Not valid
            )
        errors = exc_info.value.errors()
        assert any("series_type is not valid" in str(err) for err in errors)


class TestMonthParameter:
    """Test month parameter validation (intraday only)."""

    @pytest.mark.parametrize(
        "indicator_type,extra_params",
        [
            ("rsi", {"time_period": 14, "series_type": "close"}),
            ("macd", {"series_type": "close"}),
            ("stoch", {}),
            ("bop", {}),
        ],
    )
    def test_valid_month_with_intraday_interval(self, indicator_type, extra_params):
        """Test month parameter works with intraday intervals."""
        request = OscillatorRequest(
            indicator_type=indicator_type,
            symbol="IBM",
            interval="5min",
            month="2024-01",
            **extra_params,
        )
        assert request.month == "2024-01"

    @pytest.mark.parametrize(
        "indicator_type,extra_params",
        [
            ("rsi", {"time_period": 14, "series_type": "close"}),
            ("macd", {"series_type": "close"}),
        ],
    )
    def test_month_rejects_non_intraday_interval(self, indicator_type, extra_params):
        """Test month parameter is rejected for non-intraday intervals."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type=indicator_type,
                symbol="IBM",
                interval="daily",
                month="2024-01",  # Not valid for daily
                **extra_params,
            )
        errors = exc_info.value.errors()
        assert any("only applicable for intraday intervals" in str(err) for err in errors)

    @pytest.mark.parametrize(
        "invalid_month",
        ["2024", "01-2024", "2024/01", "202401", "1999-12"],  # Too early
    )
    def test_invalid_month_format(self, invalid_month):
        """Test month parameter validates format."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type="rsi",
                symbol="IBM",
                interval="5min",
                time_period=14,
                series_type="close",
                month=invalid_month,
            )
        # Should fail validation
        assert exc_info.value is not None


class TestOutputControlParameters:
    """Test force_inline and force_file parameters."""

    def test_force_inline_and_force_file_are_mutually_exclusive(self):
        """Test that force_inline and force_file cannot both be True."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type="rsi",
                symbol="IBM",
                interval="daily",
                time_period=14,
                series_type="close",
                force_inline=True,
                force_file=True,  # Conflict
            )
        errors = exc_info.value.errors()
        assert any("mutually exclusive" in str(err) for err in errors)

    def test_force_inline_works(self):
        """Test force_inline flag works."""
        request = OscillatorRequest(
            indicator_type="rsi",
            symbol="IBM",
            interval="daily",
            time_period=14,
            series_type="close",
            force_inline=True,
        )
        assert request.force_inline is True
        assert request.force_file is False

    def test_force_file_works(self):
        """Test force_file flag works."""
        request = OscillatorRequest(
            indicator_type="macd",
            symbol="AAPL",
            interval="daily",
            series_type="close",
            force_file=True,
        )
        assert request.force_file is True
        assert request.force_inline is False


class TestMATypeParameters:
    """Test MA type parameter validation (0-8 range)."""

    @pytest.mark.parametrize(
        "matype_value",
        [0, 1, 2, 3, 4, 5, 6, 7, 8],  # All valid MA types
    )
    def test_valid_matype_values(self, matype_value):
        """Test all valid MA type values (0-8)."""
        request = OscillatorRequest(
            indicator_type="apo",
            symbol="IBM",
            interval="daily",
            series_type="close",
            matype=matype_value,
        )
        assert request.matype == matype_value

    @pytest.mark.parametrize(
        "invalid_matype",
        [-1, 9, 10, 100],
    )
    def test_invalid_matype_values(self, invalid_matype):
        """Test invalid MA type values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            OscillatorRequest(
                indicator_type="apo",
                symbol="IBM",
                interval="daily",
                series_type="close",
                matype=invalid_matype,
            )
        # Should fail Pydantic's ge/le validation
        assert exc_info.value is not None


class TestComprehensiveCoverage:
    """Comprehensive tests ensuring all 17 indicators are covered."""

    @pytest.mark.parametrize(
        "indicator_type,required_params",
        [
            ("macd", {"series_type": "close"}),
            ("macdext", {"series_type": "close"}),
            ("stoch", {}),
            ("stochf", {}),
            ("rsi", {"time_period": 14, "series_type": "close"}),
            ("stochrsi", {"time_period": 14, "series_type": "close"}),
            ("willr", {"time_period": 14}),
            ("adx", {"time_period": 14}),
            ("adxr", {"time_period": 14}),
            ("apo", {"series_type": "close"}),
            ("ppo", {"series_type": "close"}),
            ("mom", {"time_period": 10, "series_type": "close"}),
            ("bop", {}),
            ("cci", {"time_period": 20}),
            ("cmo", {"time_period": 14, "series_type": "close"}),
            ("roc", {"time_period": 12, "series_type": "close"}),
            ("rocr", {"time_period": 12, "series_type": "close"}),
        ],
    )
    def test_all_17_indicators_minimal_valid_request(self, indicator_type, required_params):
        """Test that all 17 oscillator indicators can be created with minimal params."""
        request = OscillatorRequest(
            indicator_type=indicator_type,
            symbol="TEST",
            interval="daily",
            **required_params,
        )
        assert request.indicator_type == indicator_type
        assert request.symbol == "TEST"
