"""
Unified forex request schema for Alpha Vantage MCP server.

This module consolidates 4 separate forex API endpoints into a single
GET_FOREX_DATA tool with conditional parameter validation based on timeframe.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ForexRequest(BaseModel):
    """
    Unified forex request schema.

    Consolidates the following Alpha Vantage API endpoints:
    - FX_INTRADAY (intraday)
    - FX_DAILY (daily)
    - FX_WEEKLY (weekly)
    - FX_MONTHLY (monthly)

    Examples:
        >>> # Intraday forex data
        >>> request = ForexRequest(
        ...     timeframe="intraday",
        ...     from_symbol="EUR",
        ...     to_symbol="USD",
        ...     interval="5min",
        ...     outputsize="compact"
        ... )

        >>> # Daily forex data
        >>> request = ForexRequest(
        ...     timeframe="daily",
        ...     from_symbol="GBP",
        ...     to_symbol="USD",
        ...     outputsize="full"
        ... )

        >>> # Weekly forex data
        >>> request = ForexRequest(
        ...     timeframe="weekly",
        ...     from_symbol="EUR",
        ...     to_symbol="JPY"
        ... )
    """

    timeframe: Literal["intraday", "daily", "weekly", "monthly"] = Field(
        description=(
            "Timeframe for forex data. Options: "
            "intraday (1min-60min intervals), daily (daily OHLC), "
            "weekly (weekly OHLC), monthly (monthly OHLC)"
        )
    )

    from_symbol: str = Field(
        description=(
            "Source currency code (3-letter forex symbol). "
            "Examples: EUR, USD, GBP, JPY, CAD, AUD"
        )
    )

    to_symbol: str = Field(
        description=(
            "Destination currency code (3-letter forex symbol). "
            "Examples: USD, EUR, GBP, JPY, CAD, AUD"
        )
    )

    # Intraday-specific parameter
    interval: Literal["1min", "5min", "15min", "30min", "60min"] | None = Field(
        None,
        description=(
            "Time interval for intraday data. Required when timeframe='intraday'. "
            "Options: 1min, 5min, 15min, 30min, 60min"
        ),
    )

    # Intraday and Daily parameter
    outputsize: Literal["compact", "full"] | None = Field(
        "compact",
        description=(
            "Output size. 'compact' returns latest 100 data points, "
            "'full' returns complete available history. "
            "Applicable to intraday and daily timeframes. Default: 'compact'."
        ),
    )

    datatype: Literal["json", "csv"] | None = Field(
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

    @model_validator(mode="after")
    def validate_timeframe_params(self):
        """
        Validate that required parameters are provided based on timeframe.

        This validator enforces conditional parameter requirements:
        - intraday: requires interval parameter
        - daily/weekly/monthly: no additional requirements beyond from_symbol/to_symbol

        Returns:
            Validated model instance.

        Raises:
            ValueError: If required parameters are missing for the timeframe.
        """
        timeframe = self.timeframe

        # Intraday: requires interval
        if timeframe == "intraday":
            if not self.interval:
                raise ValueError(
                    "interval is required when timeframe='intraday'. "
                    "Valid options: 1min, 5min, 15min, 30min, 60min"
                )

        # Daily/weekly/monthly: interval should not be provided
        elif timeframe in ["daily", "weekly", "monthly"]:
            if self.interval:
                raise ValueError(
                    f"interval parameter is not applicable for timeframe='{timeframe}'. "
                    "The interval parameter is only used with timeframe='intraday'."
                )

        # Validate that force_inline and force_file are mutually exclusive
        if self.force_inline and self.force_file:
            raise ValueError("force_inline and force_file are mutually exclusive")

        return self
