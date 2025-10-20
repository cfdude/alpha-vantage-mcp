"""
Unified cycle (Hilbert Transform) indicator request schema for Alpha Vantage MCP server.

This module consolidates 6 separate Hilbert Transform indicator API endpoints into a single
GET_CYCLE_INDICATOR tool with parameter validation.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CycleRequest(BaseModel):
    """
    Unified cycle (Hilbert Transform) indicator request schema.

    Consolidates the following Alpha Vantage API endpoints:
    - HT_TRENDLINE (ht_trendline) - Hilbert Transform Instantaneous Trendline
    - HT_SINE (ht_sine) - Hilbert Transform Sine Wave
    - HT_TRENDMODE (ht_trendmode) - Hilbert Transform Trend vs Cycle Mode
    - HT_DCPERIOD (ht_dcperiod) - Hilbert Transform Dominant Cycle Period
    - HT_DCPHASE (ht_dcphase) - Hilbert Transform Dominant Cycle Phase
    - HT_PHASOR (ht_phasor) - Hilbert Transform Phasor Components

    All Hilbert Transform indicators use the same parameters: symbol, interval, series_type.

    Examples:
        >>> # HT_TRENDLINE
        >>> request = CycleRequest(
        ...     indicator_type="ht_trendline",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     series_type="close"
        ... )

        >>> # HT_DCPERIOD
        >>> request = CycleRequest(
        ...     indicator_type="ht_dcperiod",
        ...     symbol="AAPL",
        ...     interval="daily",
        ...     series_type="close"
        ... )
    """

    indicator_type: Literal[
        "ht_trendline", "ht_sine", "ht_trendmode", "ht_dcperiod", "ht_dcphase", "ht_phasor"
    ] = Field(
        description=(
            "Type of Hilbert Transform indicator. Options: "
            "ht_trendline (Instantaneous Trendline), ht_sine (Sine Wave), "
            "ht_trendmode (Trend vs Cycle Mode), ht_dcperiod (Dominant Cycle Period), "
            "ht_dcphase (Dominant Cycle Phase), ht_phasor (Phasor Components)"
        )
    )

    symbol: str = Field(description="Stock ticker symbol (e.g., IBM, AAPL)")

    interval: Literal["1min", "5min", "15min", "30min", "60min", "daily", "weekly", "monthly"] = (
        Field(description="Time interval between consecutive data points")
    )

    series_type: Literal["close", "open", "high", "low"] = Field(
        description="Price type to use for Hilbert Transform calculation"
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

    def model_post_init(self, __context):
        """
        Validate month parameter is only used with intraday intervals.

        Args:
            __context: Pydantic context.

        Raises:
            ValueError: If month is used with non-intraday interval.
        """
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
