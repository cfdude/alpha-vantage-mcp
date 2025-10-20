"""
Unified volume indicator request schema for Alpha Vantage MCP server.

This module consolidates 4 separate volume indicator API endpoints into a single
GET_VOLUME_INDICATOR tool with conditional parameter validation based on indicator_type.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class VolumeRequest(BaseModel):
    """
    Unified volume indicator request schema.

    Consolidates the following Alpha Vantage API endpoints:
    - AD (ad) - Chaikin A/D Line
    - ADOSC (adosc) - Chaikin A/D Oscillator
    - OBV (obv) - On Balance Volume
    - MFI (mfi) - Money Flow Index

    Examples:
        >>> # MFI (requires time_period)
        >>> request = VolumeRequest(
        ...     indicator_type="mfi",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=14
        ... )

        >>> # ADOSC (requires fastperiod, slowperiod)
        >>> request = VolumeRequest(
        ...     indicator_type="adosc",
        ...     symbol="AAPL",
        ...     interval="daily",
        ...     fastperiod=3,
        ...     slowperiod=10
        ... )

        >>> # AD (no additional params)
        >>> request = VolumeRequest(
        ...     indicator_type="ad",
        ...     symbol="MSFT",
        ...     interval="daily"
        ... )

        >>> # OBV (no additional params)
        >>> request = VolumeRequest(
        ...     indicator_type="obv",
        ...     symbol="GOOGL",
        ...     interval="daily"
        ... )
    """

    indicator_type: Literal["ad", "adosc", "obv", "mfi"] = Field(
        description=(
            "Type of volume indicator. Options: "
            "ad (Chaikin A/D Line), adosc (Chaikin A/D Oscillator), "
            "obv (On Balance Volume), mfi (Money Flow Index)"
        )
    )

    symbol: str = Field(description="Stock ticker symbol (e.g., IBM, AAPL)")

    interval: Literal["1min", "5min", "15min", "30min", "60min", "daily", "weekly", "monthly"] = (
        Field(description="Time interval between consecutive data points")
    )

    # MFI parameter
    time_period: int | None = Field(
        None,
        ge=1,
        description=(
            "Number of data points used to calculate MFI. "
            "Required for: mfi. "
            "Not used for: ad, adosc, obv."
        ),
    )

    # ADOSC parameters
    fastperiod: int | None = Field(
        None,
        ge=1,
        description=("Fast period for ADOSC EMA calculation. " "Used with: adosc (default: 3)."),
    )

    slowperiod: int | None = Field(
        None,
        ge=1,
        description=("Slow period for ADOSC EMA calculation. " "Used with: adosc (default: 10)."),
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
        - MFI: Requires time_period
        - ADOSC: Requires fastperiod, slowperiod (with defaults)
        - AD, OBV: No additional params beyond symbol/interval

        Returns:
            Validated model instance.

        Raises:
            ValueError: If required parameters are missing or invalid parameters are provided.
        """
        indicator_type = self.indicator_type

        # ========== MFI ==========
        if indicator_type == "mfi":
            # Require time_period
            if self.time_period is None:
                raise ValueError(
                    "time_period is required for indicator_type='mfi'. "
                    "Provide a positive integer (e.g., time_period=14)"
                )

            # Reject ADOSC parameters
            if self.fastperiod is not None or self.slowperiod is not None:
                raise ValueError(
                    "fastperiod and slowperiod are not valid for indicator_type='mfi'. "
                    "These parameters are only used with indicator_type='adosc'."
                )

        # ========== ADOSC ==========
        elif indicator_type == "adosc":
            # Set defaults for optional periods
            if self.fastperiod is None:
                self.fastperiod = 3
            if self.slowperiod is None:
                self.slowperiod = 10

            # Reject time_period
            if self.time_period is not None:
                raise ValueError(
                    "time_period is not valid for indicator_type='adosc'. "
                    "Use fastperiod and slowperiod instead."
                )

        # ========== AD, OBV ==========
        elif indicator_type in ["ad", "obv"]:
            # Reject all optional parameters
            if self.time_period is not None:
                raise ValueError(
                    f"time_period is not valid for indicator_type='{indicator_type}'. "
                    f"{indicator_type.upper()} uses OHLCV data automatically without additional parameters."
                )

            if self.fastperiod is not None or self.slowperiod is not None:
                raise ValueError(
                    f"fastperiod and slowperiod are not valid for indicator_type='{indicator_type}'. "
                    "These parameters are only used with indicator_type='adosc'."
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
