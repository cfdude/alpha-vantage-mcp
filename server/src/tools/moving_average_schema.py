"""
Unified moving average request schema for Alpha Vantage MCP server.

This module consolidates 10 separate moving average indicator API endpoints into a single
GET_MOVING_AVERAGE tool with conditional parameter validation based on indicator_type.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class MovingAverageRequest(BaseModel):
    """
    Unified moving average request schema.

    Consolidates the following Alpha Vantage API endpoints:
    - SMA (sma) - Simple Moving Average
    - EMA (ema) - Exponential Moving Average
    - WMA (wma) - Weighted Moving Average
    - DEMA (dema) - Double Exponential Moving Average
    - TEMA (tema) - Triple Exponential Moving Average
    - TRIMA (trima) - Triangular Moving Average
    - KAMA (kama) - Kaufman Adaptive Moving Average
    - MAMA (mama) - MESA Adaptive Moving Average
    - T3 (t3) - Triple Exponential Moving Average T3
    - VWAP (vwap) - Volume Weighted Average Price

    Examples:
        >>> # Standard moving average (SMA, EMA, WMA, etc.)
        >>> request = MovingAverageRequest(
        ...     indicator_type="sma",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=60,
        ...     series_type="close"
        ... )

        >>> # MAMA (uses fastlimit/slowlimit instead of time_period)
        >>> request = MovingAverageRequest(
        ...     indicator_type="mama",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     series_type="close",
        ...     fastlimit=0.01,
        ...     slowlimit=0.01
        ... )

        >>> # VWAP (intraday only, no time_period or series_type)
        >>> request = MovingAverageRequest(
        ...     indicator_type="vwap",
        ...     symbol="IBM",
        ...     interval="5min"
        ... )
    """

    indicator_type: Literal[
        "sma", "ema", "wma", "dema", "tema", "trima", "kama", "mama", "t3", "vwap"
    ] = Field(
        description=(
            "Type of moving average indicator. Options: "
            "sma (Simple), ema (Exponential), wma (Weighted), "
            "dema (Double Exponential), tema (Triple Exponential), "
            "trima (Triangular), kama (Kaufman Adaptive), "
            "mama (MESA Adaptive), t3 (Triple Exponential T3), "
            "vwap (Volume Weighted Average Price)"
        )
    )

    symbol: str = Field(description="Stock ticker symbol (e.g., IBM, AAPL)")

    interval: Literal["1min", "5min", "15min", "30min", "60min", "daily", "weekly", "monthly"] = (
        Field(description="Time interval between consecutive data points")
    )

    # Standard parameters (most indicators use these)
    time_period: int | None = Field(
        None,
        ge=1,
        description=(
            "Number of data points used to calculate each moving average value. "
            "Required for: sma, ema, wma, dema, tema, trima, kama, t3. "
            "Not used for: mama, vwap."
        ),
    )

    series_type: Literal["close", "open", "high", "low"] | None = Field(
        None,
        description=(
            "Price type to use for calculation. "
            "Required for: sma, ema, wma, dema, tema, trima, kama, mama, t3. "
            "Not used for: vwap."
        ),
    )

    # MAMA-specific parameters
    fastlimit: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Fast limit for MAMA indicator (0.0-1.0). "
            "Only used with indicator_type='mama'. Default: 0.01."
        ),
    )

    slowlimit: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Slow limit for MAMA indicator (0.0-1.0). "
            "Only used with indicator_type='mama'. Default: 0.01."
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
            month = int(month_str)
            if month < 1 or month > 12:
                raise ValueError("month must be between 01 and 12")
        except ValueError as e:
            raise ValueError(f"Invalid month in month parameter: {e}") from e

        return v

    @model_validator(mode="after")
    def validate_indicator_params(self):
        """
        Validate that required parameters are provided based on indicator_type.

        This validator enforces conditional parameter requirements:
        - Standard indicators (sma, ema, wma, dema, tema, trima, kama, t3):
          * Require: time_period, series_type
          * Reject: fastlimit, slowlimit
        - MAMA:
          * Require: series_type, fastlimit, slowlimit (with defaults)
          * Reject: time_period
        - VWAP:
          * Require: intraday interval only
          * Reject: time_period, series_type, fastlimit, slowlimit

        Returns:
            Validated model instance.

        Raises:
            ValueError: If required parameters are missing or invalid parameters are provided.
        """
        indicator_type = self.indicator_type
        standard_indicators = ["sma", "ema", "wma", "dema", "tema", "trima", "kama", "t3"]

        # Standard indicators validation
        if indicator_type in standard_indicators:
            # Require time_period and series_type
            if self.time_period is None:
                raise ValueError(
                    f"time_period is required for indicator_type='{indicator_type}'. "
                    "Provide a positive integer (e.g., time_period=60)"
                )

            if self.series_type is None:
                raise ValueError(
                    f"series_type is required for indicator_type='{indicator_type}'. "
                    "Valid options: close, open, high, low"
                )

            # Reject MAMA/VWAP-specific parameters
            if self.fastlimit is not None or self.slowlimit is not None:
                raise ValueError(
                    f"fastlimit and slowlimit are not valid for indicator_type='{indicator_type}'. "
                    "These parameters are only used with indicator_type='mama'."
                )

        # MAMA validation
        elif indicator_type == "mama":
            # Require series_type
            if self.series_type is None:
                raise ValueError(
                    "series_type is required for indicator_type='mama'. "
                    "Valid options: close, open, high, low"
                )

            # Set default values for fastlimit/slowlimit if not provided
            if self.fastlimit is None:
                self.fastlimit = 0.01  # Default

            if self.slowlimit is None:
                self.slowlimit = 0.01  # Default

            # Reject time_period
            if self.time_period is not None:
                raise ValueError(
                    "time_period is not valid for indicator_type='mama'. "
                    "Use fastlimit and slowlimit parameters instead."
                )

        # VWAP validation
        elif indicator_type == "vwap":
            # Require intraday interval
            intraday_intervals = ["1min", "5min", "15min", "30min", "60min"]
            if self.interval not in intraday_intervals:
                raise ValueError(
                    "indicator_type='vwap' only supports intraday intervals. "
                    f"Valid options: {', '.join(intraday_intervals)}. "
                    f"Got: {self.interval}"
                )

            # Reject time_period
            if self.time_period is not None:
                raise ValueError(
                    "time_period is not valid for indicator_type='vwap'. "
                    "VWAP is calculated from intraday OHLCV data without a time period parameter."
                )

            # Reject series_type
            if self.series_type is not None:
                raise ValueError(
                    "series_type is not valid for indicator_type='vwap'. "
                    "VWAP is calculated from price and volume data automatically."
                )

            # Reject fastlimit/slowlimit
            if self.fastlimit is not None or self.slowlimit is not None:
                raise ValueError(
                    "fastlimit and slowlimit are not valid for indicator_type='vwap'. "
                    "These parameters are only used with indicator_type='mama'."
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
