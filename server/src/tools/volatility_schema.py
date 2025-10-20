"""
Unified volatility indicator request schema for Alpha Vantage MCP server.

This module consolidates 7 separate volatility indicator API endpoints into a single
GET_VOLATILITY_INDICATOR tool with conditional parameter validation based on indicator_type.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class VolatilityRequest(BaseModel):
    """
    Unified volatility indicator request schema.

    Consolidates the following Alpha Vantage API endpoints:
    - BBANDS (bbands) - Bollinger Bands
    - TRANGE (trange) - True Range
    - ATR (atr) - Average True Range
    - NATR (natr) - Normalized Average True Range
    - MIDPOINT (midpoint) - Midpoint
    - MIDPRICE (midprice) - Midpoint Price
    - SAR (sar) - Parabolic SAR

    Examples:
        >>> # BBANDS (most complex: time_period, series_type, nbdevup, nbdevdn, matype)
        >>> request = VolatilityRequest(
        ...     indicator_type="bbands",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=20,
        ...     series_type="close",
        ...     nbdevup=2,
        ...     nbdevdn=2,
        ...     matype=0
        ... )

        >>> # ATR (simple: just time_period)
        >>> request = VolatilityRequest(
        ...     indicator_type="atr",
        ...     symbol="AAPL",
        ...     interval="daily",
        ...     time_period=14
        ... )

        >>> # SAR (unique: acceleration + maximum)
        >>> request = VolatilityRequest(
        ...     indicator_type="sar",
        ...     symbol="MSFT",
        ...     interval="daily",
        ...     acceleration=0.02,
        ...     maximum=0.20
        ... )

        >>> # TRANGE (no additional params)
        >>> request = VolatilityRequest(
        ...     indicator_type="trange",
        ...     symbol="GOOGL",
        ...     interval="daily"
        ... )
    """

    indicator_type: Literal["bbands", "trange", "atr", "natr", "midpoint", "midprice", "sar"] = (
        Field(
            description=(
                "Type of volatility indicator. Options: "
                "bbands (Bollinger Bands), trange (True Range), atr (Average True Range), "
                "natr (Normalized ATR), midpoint (Midpoint), midprice (Midpoint Price), "
                "sar (Parabolic SAR)"
            )
        )
    )

    symbol: str = Field(description="Stock ticker symbol (e.g., IBM, AAPL)")

    interval: Literal["1min", "5min", "15min", "30min", "60min", "daily", "weekly", "monthly"] = (
        Field(description="Time interval between consecutive data points")
    )

    # Common parameters
    time_period: int | None = Field(
        None,
        ge=1,
        description=(
            "Number of data points used to calculate each indicator value. "
            "Required for: bbands, atr, natr, midpoint, midprice. "
            "Not used for: trange, sar."
        ),
    )

    series_type: Literal["close", "open", "high", "low"] | None = Field(
        None,
        description=(
            "Price type to use for calculation. "
            "Required for: bbands, midpoint. "
            "Not used for: trange, atr, natr, midprice, sar."
        ),
    )

    # BBANDS-specific parameters
    nbdevup: int | None = Field(
        None,
        ge=1,
        description=(
            "Standard deviation multiplier for upper band (BBANDS only). "
            "Default: 2. Must be positive integer."
        ),
    )

    nbdevdn: int | None = Field(
        None,
        ge=1,
        description=(
            "Standard deviation multiplier for lower band (BBANDS only). "
            "Default: 2. Must be positive integer."
        ),
    )

    matype: int | None = Field(
        None,
        ge=0,
        le=8,
        description=(
            "Moving average type for BBANDS (0=SMA, 1=EMA, 2=WMA, 3=DEMA, 4=TEMA, "
            "5=TRIMA, 6=T3, 7=KAMA, 8=MAMA). Default: 0."
        ),
    )

    # SAR-specific parameters
    acceleration: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Acceleration factor for SAR (0.0-1.0). "
            "Default: 0.01. Only used with indicator_type='sar'."
        ),
    )

    maximum: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Maximum acceleration factor for SAR (0.0-1.0). "
            "Default: 0.20. Only used with indicator_type='sar'."
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

        This validator enforces conditional parameter requirements:
        - BBANDS: Requires time_period, series_type. Optional: nbdevup, nbdevdn, matype (with defaults)
        - ATR, NATR, MIDPRICE: Require time_period only
        - MIDPOINT: Requires time_period, series_type
        - SAR: Requires acceleration, maximum (with defaults). No time_period/series_type
        - TRANGE: No additional params beyond symbol/interval

        Returns:
            Validated model instance.

        Raises:
            ValueError: If required parameters are missing or invalid parameters are provided.
        """
        indicator_type = self.indicator_type

        # ========== BBANDS ==========
        if indicator_type == "bbands":
            # Require time_period and series_type
            if self.time_period is None:
                raise ValueError(
                    "time_period is required for indicator_type='bbands'. "
                    "Provide a positive integer (e.g., time_period=20)"
                )

            if self.series_type is None:
                raise ValueError(
                    "series_type is required for indicator_type='bbands'. "
                    "Valid options: close, open, high, low"
                )

            # Set defaults for optional BBANDS parameters
            if self.nbdevup is None:
                self.nbdevup = 2
            if self.nbdevdn is None:
                self.nbdevdn = 2
            if self.matype is None:
                self.matype = 0

            # Reject SAR parameters
            if self.acceleration is not None or self.maximum is not None:
                raise ValueError(
                    "acceleration and maximum are not valid for indicator_type='bbands'. "
                    "These parameters are only used with indicator_type='sar'."
                )

        # ========== ATR, NATR, MIDPRICE ==========
        elif indicator_type in ["atr", "natr", "midprice"]:
            # Require time_period
            if self.time_period is None:
                raise ValueError(
                    f"time_period is required for indicator_type='{indicator_type}'. "
                    "Provide a positive integer (e.g., time_period=14)"
                )

            # Reject series_type
            if self.series_type is not None:
                raise ValueError(
                    f"series_type is not valid for indicator_type='{indicator_type}'. "
                    f"{indicator_type.upper()} uses OHLC data automatically."
                )

            # Reject BBANDS parameters
            if self.nbdevup is not None or self.nbdevdn is not None or self.matype is not None:
                raise ValueError(
                    f"nbdevup, nbdevdn, and matype are not valid for indicator_type='{indicator_type}'. "
                    "These parameters are only used with indicator_type='bbands'."
                )

            # Reject SAR parameters
            if self.acceleration is not None or self.maximum is not None:
                raise ValueError(
                    f"acceleration and maximum are not valid for indicator_type='{indicator_type}'. "
                    "These parameters are only used with indicator_type='sar'."
                )

        # ========== MIDPOINT ==========
        elif indicator_type == "midpoint":
            # Require time_period and series_type
            if self.time_period is None:
                raise ValueError(
                    "time_period is required for indicator_type='midpoint'. "
                    "Provide a positive integer (e.g., time_period=14)"
                )

            if self.series_type is None:
                raise ValueError(
                    "series_type is required for indicator_type='midpoint'. "
                    "Valid options: close, open, high, low"
                )

            # Reject BBANDS parameters
            if self.nbdevup is not None or self.nbdevdn is not None or self.matype is not None:
                raise ValueError(
                    "nbdevup, nbdevdn, and matype are not valid for indicator_type='midpoint'. "
                    "These parameters are only used with indicator_type='bbands'."
                )

            # Reject SAR parameters
            if self.acceleration is not None or self.maximum is not None:
                raise ValueError(
                    "acceleration and maximum are not valid for indicator_type='midpoint'. "
                    "These parameters are only used with indicator_type='sar'."
                )

        # ========== SAR ==========
        elif indicator_type == "sar":
            # Set defaults for acceleration and maximum
            if self.acceleration is None:
                self.acceleration = 0.01
            if self.maximum is None:
                self.maximum = 0.20

            # Reject time_period and series_type
            if self.time_period is not None:
                raise ValueError(
                    "time_period is not valid for indicator_type='sar'. "
                    "SAR uses acceleration and maximum parameters instead."
                )

            if self.series_type is not None:
                raise ValueError(
                    "series_type is not valid for indicator_type='sar'. "
                    "SAR uses OHLC data automatically."
                )

            # Reject BBANDS parameters
            if self.nbdevup is not None or self.nbdevdn is not None or self.matype is not None:
                raise ValueError(
                    "nbdevup, nbdevdn, and matype are not valid for indicator_type='sar'. "
                    "These parameters are only used with indicator_type='bbands'."
                )

        # ========== TRANGE ==========
        elif indicator_type == "trange":
            # Reject all optional parameters
            if self.time_period is not None:
                raise ValueError(
                    "time_period is not valid for indicator_type='trange'. "
                    "TRANGE uses OHLC data automatically without additional parameters."
                )

            if self.series_type is not None:
                raise ValueError(
                    "series_type is not valid for indicator_type='trange'. "
                    "TRANGE uses OHLC data automatically without additional parameters."
                )

            if self.nbdevup is not None or self.nbdevdn is not None or self.matype is not None:
                raise ValueError(
                    "nbdevup, nbdevdn, and matype are not valid for indicator_type='trange'. "
                    "These parameters are only used with indicator_type='bbands'."
                )

            if self.acceleration is not None or self.maximum is not None:
                raise ValueError(
                    "acceleration and maximum are not valid for indicator_type='trange'. "
                    "These parameters are only used with indicator_type='sar'."
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
