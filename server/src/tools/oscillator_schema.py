"""
Unified oscillator/momentum indicator request schema for Alpha Vantage MCP server.

This module consolidates 17 separate oscillator and momentum indicator API endpoints into a single
GET_OSCILLATOR tool with conditional parameter validation based on indicator_type.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class OscillatorRequest(BaseModel):
    """
    Unified oscillator/momentum indicator request schema.

    Consolidates the following Alpha Vantage API endpoints:
    - MACD (macd) - Moving Average Convergence Divergence
    - MACDEXT (macdext) - MACD with Controllable MA Type
    - STOCH (stoch) - Stochastic Oscillator
    - STOCHF (stochf) - Stochastic Fast
    - RSI (rsi) - Relative Strength Index
    - STOCHRSI (stochrsi) - Stochastic RSI
    - WILLR (willr) - Williams' %R
    - ADX (adx) - Average Directional Index
    - ADXR (adxr) - ADX Rating
    - APO (apo) - Absolute Price Oscillator
    - PPO (ppo) - Percentage Price Oscillator
    - MOM (mom) - Momentum
    - BOP (bop) - Balance of Power
    - CCI (cci) - Commodity Channel Index
    - CMO (cmo) - Chande Momentum Oscillator
    - ROC (roc) - Rate of Change
    - ROCR (rocr) - Rate of Change Ratio

    Examples:
        >>> # RSI (simple: time_period + series_type)
        >>> request = OscillatorRequest(
        ...     indicator_type="rsi",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=14,
        ...     series_type="close"
        ... )

        >>> # MACD (fast/slow periods)
        >>> request = OscillatorRequest(
        ...     indicator_type="macd",
        ...     symbol="AAPL",
        ...     interval="daily",
        ...     series_type="close",
        ...     fastperiod=12,
        ...     slowperiod=26,
        ...     signalperiod=9
        ... )

        >>> # STOCH (stochastic parameters)
        >>> request = OscillatorRequest(
        ...     indicator_type="stoch",
        ...     symbol="MSFT",
        ...     interval="daily",
        ...     fastkperiod=5,
        ...     slowkperiod=3,
        ...     slowdperiod=3
        ... )

        >>> # BOP (no additional parameters)
        >>> request = OscillatorRequest(
        ...     indicator_type="bop",
        ...     symbol="GOOGL",
        ...     interval="daily"
        ... )
    """

    indicator_type: Literal[
        "macd",
        "macdext",
        "stoch",
        "stochf",
        "rsi",
        "stochrsi",
        "willr",
        "adx",
        "adxr",
        "apo",
        "ppo",
        "mom",
        "bop",
        "cci",
        "cmo",
        "roc",
        "rocr",
    ] = Field(
        description=(
            "Type of oscillator/momentum indicator. Options: "
            "macd (MACD), macdext (MACD Extended), stoch (Stochastic), "
            "stochf (Stochastic Fast), rsi (RSI), stochrsi (Stochastic RSI), "
            "willr (Williams %R), adx (ADX), adxr (ADX Rating), "
            "apo (Absolute Price Oscillator), ppo (Percentage Price Oscillator), "
            "mom (Momentum), bop (Balance of Power), cci (Commodity Channel Index), "
            "cmo (Chande Momentum Oscillator), roc (Rate of Change), "
            "rocr (Rate of Change Ratio)"
        )
    )

    symbol: str = Field(description="Stock ticker symbol (e.g., IBM, AAPL)")

    interval: Literal["1min", "5min", "15min", "30min", "60min", "daily", "weekly", "monthly"] = (
        Field(description="Time interval between consecutive data points")
    )

    # Single time period (for simple indicators)
    time_period: int | None = Field(
        None,
        ge=1,
        description=(
            "Number of data points used to calculate each indicator value. "
            "Required for: rsi, willr, adx, adxr, cci, mom, cmo, roc, rocr, stochrsi. "
            "Not used for: macd, macdext, stoch, stochf, apo, ppo, bop."
        ),
    )

    # Series type (for price-based indicators)
    series_type: Literal["close", "open", "high", "low"] | None = Field(
        None,
        description=(
            "Price type to use for calculation. "
            "Required for: macd, macdext, rsi, apo, ppo, mom, cmo, roc, rocr, stochrsi. "
            "Not used for: stoch, stochf, willr, adx, adxr, bop, cci."
        ),
    )

    # MACD family parameters
    fastperiod: int | None = Field(
        None,
        ge=1,
        description=(
            "Fast period for moving average calculation. "
            "Used with: macd (default: 12), macdext (default: 12), apo (default: 12), ppo (default: 12)."
        ),
    )

    slowperiod: int | None = Field(
        None,
        ge=1,
        description=(
            "Slow period for moving average calculation. "
            "Used with: macd (default: 26), macdext (default: 26), apo (default: 26), ppo (default: 26)."
        ),
    )

    signalperiod: int | None = Field(
        None,
        ge=1,
        description=(
            "Signal period for MACD calculation. "
            "Used with: macd (default: 9), macdext (default: 9)."
        ),
    )

    # Stochastic parameters
    fastkperiod: int | None = Field(
        None,
        ge=1,
        description=(
            "Fast K period for stochastic calculation. "
            "Used with: stoch (default: 5), stochf (default: 5), stochrsi."
        ),
    )

    slowkperiod: int | None = Field(
        None,
        ge=1,
        description=("Slow K period for stochastic calculation. Used with: stoch (default: 3)."),
    )

    slowdperiod: int | None = Field(
        None,
        ge=1,
        description=("Slow D period for stochastic calculation. Used with: stoch (default: 3)."),
    )

    fastdperiod: int | None = Field(
        None,
        ge=1,
        description=(
            "Fast D period for stochastic calculation. Used with: stochf (default: 3), stochrsi."
        ),
    )

    # MA type parameters (0-8: SMA, EMA, WMA, DEMA, TEMA, TRIMA, T3, KAMA, MAMA)
    matype: int | None = Field(
        None,
        ge=0,
        le=8,
        description=(
            "Moving average type (0=SMA, 1=EMA, 2=WMA, 3=DEMA, 4=TEMA, 5=TRIMA, 6=T3, 7=KAMA, 8=MAMA). "
            "Used with: apo (default: 0), ppo (default: 0)."
        ),
    )

    fastmatype: int | None = Field(
        None,
        ge=0,
        le=8,
        description=(
            "Fast moving average type. Used with: macdext (default: 0), stochrsi (default: 0)."
        ),
    )

    slowmatype: int | None = Field(
        None,
        ge=0,
        le=8,
        description=("Slow moving average type. Used with: macdext (default: 0)."),
    )

    signalmatype: int | None = Field(
        None,
        ge=0,
        le=8,
        description=("Signal moving average type. Used with: macdext (default: 0)."),
    )

    slowkmatype: int | None = Field(
        None,
        ge=0,
        le=8,
        description=("Slow K moving average type. Used with: stoch (default: 0)."),
    )

    slowdmatype: int | None = Field(
        None,
        ge=0,
        le=8,
        description=("Slow D moving average type. Used with: stoch (default: 0)."),
    )

    fastdmatype: int | None = Field(
        None,
        ge=0,
        le=8,
        description=(
            "Fast D moving average type. Used with: stochf (default: 0), stochrsi (default: 0)."
        ),
    )

    # Month parameter (intraday only)
    month: str | None = Field(
        None,
        description=(
            "Query specific month of intraday data in YYYY-MM format (e.g., '2009-01'). "
            "Only applicable for intraday intervals (1min-60min). "
            "Supports months from 2000-01 onwards."
        ),
    )

    datatype: Literal["json", "csv"] = Field(
        "csv", description="Output format. Options: 'json' or 'csv'. Default: 'csv'."
    )

    # Output control overrides
    force_inline: bool = Field(
        False,
        description=(
            "Force inline output regardless of size. Overrides automatic file/inline decision. "
            "Use with caution for large datasets."
        ),
    )

    force_file: bool = Field(
        False,
        description=(
            "Force file output regardless of size. Overrides automatic file/inline decision. "
            "Useful for ensuring data is saved to disk."
        ),
    )

    @field_validator("month")
    @classmethod
    def validate_month_format(cls, v: str | None) -> str | None:
        """
        Validate month parameter format.

        Args:
            v: Month string to validate.

        Returns:
            Validated month string.

        Raises:
            ValueError: If month format is invalid.
        """
        if v is None:
            return v

        if not isinstance(v, str):
            raise ValueError("month must be a string in YYYY-MM format")

        parts = v.split("-")
        if len(parts) != 2:
            raise ValueError("month must be in YYYY-MM format (e.g., '2009-01')")

        year_str, month_str = parts

        # Validate year (must be >= 2000)
        try:
            year = int(year_str)
            if year < 2000:
                raise ValueError("month year must be 2000 or later")
        except ValueError as e:
            raise ValueError(f"Invalid year in month parameter: {e}") from e

        # Validate month (01-12)
        try:
            month_num = int(month_str)
            if month_num < 1 or month_num > 12:
                raise ValueError("month must be between 01 and 12")
        except ValueError as e:
            raise ValueError(f"Invalid month in month parameter: {e}") from e

        return v

    @model_validator(mode="after")
    def validate_indicator_params(self):
        """
        Validate that required parameters are provided based on indicator_type.

        This validator enforces conditional parameter requirements for 17 different oscillator types.

        Returns:
            Validated model instance.

        Raises:
            ValueError: If required parameters are missing or invalid parameters are provided.
        """
        indicator_type = self.indicator_type

        # Group indicators by parameter requirements
        # Group 1: Simple period indicators (just time_period)
        simple_period = ["willr", "adx", "adxr", "cci"]

        # Group 2: Series + period indicators (time_period + series_type)
        series_period = ["rsi", "mom", "cmo", "roc", "rocr"]

        # Group 3: MACD family (series_type + fast/slow/signal periods)
        macd_indicators = ["macd"]

        # Group 4: MACD Extended (+ MA types)
        macdext_indicators = ["macdext"]

        # Group 5: APO/PPO (series_type + fast/slow + matype)
        apo_ppo_indicators = ["apo", "ppo"]

        # Group 6: Stochastic (fast/slow K/D periods + MA types)
        stoch_indicators = ["stoch"]

        # Group 7: Stochastic Fast (fastk + fastd periods + MA type)
        stochf_indicators = ["stochf"]

        # Group 8: Stochastic RSI (time_period + series_type + stoch params)
        stochrsi_indicators = ["stochrsi"]

        # Group 9: Balance of Power (no additional params)
        no_params = ["bop"]

        # ========== Group 1: Simple Period ==========
        if indicator_type in simple_period:
            # Require: time_period
            if self.time_period is None:
                raise ValueError(
                    f"time_period is required for indicator_type='{indicator_type}'. "
                    "Provide a positive integer (e.g., time_period=14)"
                )

            # Reject: series_type and all optional params
            if self.series_type is not None:
                raise ValueError(
                    f"series_type is not valid for indicator_type='{indicator_type}'. "
                    f"{indicator_type.upper()} uses OHLC data automatically."
                )

        # ========== Group 2: Series + Period ==========
        elif indicator_type in series_period:
            # Require: time_period, series_type
            if self.time_period is None:
                raise ValueError(
                    f"time_period is required for indicator_type='{indicator_type}'. "
                    "Provide a positive integer (e.g., time_period=14)"
                )

            if self.series_type is None:
                raise ValueError(
                    f"series_type is required for indicator_type='{indicator_type}'. "
                    "Valid options: close, open, high, low"
                )

        # ========== Group 3: MACD ==========
        elif indicator_type in macd_indicators:
            # Require: series_type
            if self.series_type is None:
                raise ValueError(
                    "series_type is required for indicator_type='macd'. "
                    "Valid options: close, open, high, low"
                )

            # Set defaults for optional periods
            if self.fastperiod is None:
                self.fastperiod = 12
            if self.slowperiod is None:
                self.slowperiod = 26
            if self.signalperiod is None:
                self.signalperiod = 9

            # Reject: time_period
            if self.time_period is not None:
                raise ValueError(
                    "time_period is not valid for indicator_type='macd'. "
                    "Use fastperiod, slowperiod, and signalperiod instead."
                )

        # ========== Group 4: MACD Extended ==========
        elif indicator_type in macdext_indicators:
            # Require: series_type
            if self.series_type is None:
                raise ValueError(
                    "series_type is required for indicator_type='macdext'. "
                    "Valid options: close, open, high, low"
                )

            # Set defaults for optional periods and MA types
            if self.fastperiod is None:
                self.fastperiod = 12
            if self.slowperiod is None:
                self.slowperiod = 26
            if self.signalperiod is None:
                self.signalperiod = 9
            if self.fastmatype is None:
                self.fastmatype = 0
            if self.slowmatype is None:
                self.slowmatype = 0
            if self.signalmatype is None:
                self.signalmatype = 0

            # Reject: time_period
            if self.time_period is not None:
                raise ValueError(
                    "time_period is not valid for indicator_type='macdext'. "
                    "Use fastperiod, slowperiod, and signalperiod instead."
                )

        # ========== Group 5: APO/PPO ==========
        elif indicator_type in apo_ppo_indicators:
            # Require: series_type
            if self.series_type is None:
                raise ValueError(
                    f"series_type is required for indicator_type='{indicator_type}'. "
                    "Valid options: close, open, high, low"
                )

            # Set defaults for optional periods and MA type
            if self.fastperiod is None:
                self.fastperiod = 12
            if self.slowperiod is None:
                self.slowperiod = 26
            if self.matype is None:
                self.matype = 0

            # Reject: time_period
            if self.time_period is not None:
                raise ValueError(
                    f"time_period is not valid for indicator_type='{indicator_type}'. "
                    "Use fastperiod and slowperiod instead."
                )

        # ========== Group 6: Stochastic ==========
        elif indicator_type in stoch_indicators:
            # Set defaults for optional periods and MA types
            if self.fastkperiod is None:
                self.fastkperiod = 5
            if self.slowkperiod is None:
                self.slowkperiod = 3
            if self.slowdperiod is None:
                self.slowdperiod = 3
            if self.slowkmatype is None:
                self.slowkmatype = 0
            if self.slowdmatype is None:
                self.slowdmatype = 0

            # Reject: time_period, series_type
            if self.time_period is not None:
                raise ValueError(
                    "time_period is not valid for indicator_type='stoch'. "
                    "Use fastkperiod, slowkperiod, and slowdperiod instead."
                )
            if self.series_type is not None:
                raise ValueError(
                    "series_type is not valid for indicator_type='stoch'. "
                    "STOCH uses OHLC data automatically."
                )

        # ========== Group 7: Stochastic Fast ==========
        elif indicator_type in stochf_indicators:
            # Set defaults for optional periods and MA type
            if self.fastkperiod is None:
                self.fastkperiod = 5
            if self.fastdperiod is None:
                self.fastdperiod = 3
            if self.fastdmatype is None:
                self.fastdmatype = 0

            # Reject: time_period, series_type
            if self.time_period is not None:
                raise ValueError(
                    "time_period is not valid for indicator_type='stochf'. "
                    "Use fastkperiod and fastdperiod instead."
                )
            if self.series_type is not None:
                raise ValueError(
                    "series_type is not valid for indicator_type='stochf'. "
                    "STOCHF uses OHLC data automatically."
                )

        # ========== Group 8: Stochastic RSI ==========
        elif indicator_type in stochrsi_indicators:
            # Require: time_period, series_type
            if self.time_period is None:
                raise ValueError(
                    "time_period is required for indicator_type='stochrsi'. "
                    "Provide a positive integer (e.g., time_period=14)"
                )

            if self.series_type is None:
                raise ValueError(
                    "series_type is required for indicator_type='stochrsi'. "
                    "Valid options: close, open, high, low"
                )

            # Set defaults for optional stochastic parameters
            if self.fastkperiod is None:
                self.fastkperiod = 5
            if self.fastdperiod is None:
                self.fastdperiod = 3
            if self.fastdmatype is None:
                self.fastdmatype = 0

        # ========== Group 9: Balance of Power (no params) ==========
        elif indicator_type in no_params:
            # Reject all optional parameters
            if self.time_period is not None:
                raise ValueError(
                    "time_period is not valid for indicator_type='bop'. "
                    "BOP uses OHLC data automatically without additional parameters."
                )
            if self.series_type is not None:
                raise ValueError(
                    "series_type is not valid for indicator_type='bop'. "
                    "BOP uses OHLC data automatically without additional parameters."
                )

        # Validate month parameter (only applicable to intraday intervals)
        if self.month is not None:
            intraday_intervals = ["1min", "5min", "15min", "30min", "60min"]
            if self.interval not in intraday_intervals:
                raise ValueError(
                    f"month parameter is only applicable for intraday intervals ({', '.join(intraday_intervals)}). "
                    f"Got interval='{self.interval}'"
                )

        # Validate that force_inline and force_file are mutually exclusive
        if self.force_inline and self.force_file:
            raise ValueError("force_inline and force_file are mutually exclusive")

        return self
