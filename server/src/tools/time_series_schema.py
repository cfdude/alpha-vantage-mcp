"""
Unified time series request schema for Alpha Vantage MCP server.

This module consolidates 11 separate time series API endpoints into a single
GET_TIME_SERIES tool with conditional parameter validation based on series_type.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class TimeSeriesRequest(BaseModel):
    """
    Unified time series request schema.

    Consolidates the following Alpha Vantage API endpoints:
    - TIME_SERIES_INTRADAY (intraday)
    - TIME_SERIES_DAILY (daily)
    - TIME_SERIES_DAILY_ADJUSTED (daily_adjusted)
    - TIME_SERIES_WEEKLY (weekly)
    - TIME_SERIES_WEEKLY_ADJUSTED (weekly_adjusted)
    - TIME_SERIES_MONTHLY (monthly)
    - TIME_SERIES_MONTHLY_ADJUSTED (monthly_adjusted)
    - GLOBAL_QUOTE (quote)
    - REALTIME_BULK_QUOTES (bulk_quotes)
    - SYMBOL_SEARCH (search)
    - MARKET_STATUS (market_status)

    Examples:
        >>> # Intraday data
        >>> request = TimeSeriesRequest(
        ...     series_type="intraday",
        ...     symbol="IBM",
        ...     interval="5min",
        ...     outputsize="compact"
        ... )

        >>> # Daily adjusted data
        >>> request = TimeSeriesRequest(
        ...     series_type="daily_adjusted",
        ...     symbol="AAPL",
        ...     outputsize="full"
        ... )

        >>> # Bulk quotes
        >>> request = TimeSeriesRequest(
        ...     series_type="bulk_quotes",
        ...     symbols="AAPL,MSFT,GOOGL"
        ... )

        >>> # Market status (no symbol required)
        >>> request = TimeSeriesRequest(series_type="market_status")
    """

    series_type: Literal[
        "intraday",
        "daily",
        "daily_adjusted",
        "weekly",
        "weekly_adjusted",
        "monthly",
        "monthly_adjusted",
        "quote",
        "bulk_quotes",
        "search",
        "market_status",
    ] = Field(
        description=(
            "Type of time series data to retrieve. Options: "
            "intraday (1min-60min bars), daily (raw daily), daily_adjusted (split/dividend adjusted), "
            "weekly (last day of week), weekly_adjusted (adjusted weekly), monthly (last day of month), "
            "monthly_adjusted (adjusted monthly), quote (latest price), bulk_quotes (up to 100 symbols), "
            "search (symbol lookup), market_status (market open/closed status)"
        )
    )

    symbol: str | None = Field(
        None,
        description=(
            "Ticker symbol (e.g., IBM, AAPL). Required for all series types except "
            "'bulk_quotes', 'search', and 'market_status'. For bulk_quotes, use 'symbols' instead."
        ),
    )

    # Intraday-specific parameters
    interval: Literal["1min", "5min", "15min", "30min", "60min"] | None = Field(
        None, description="Time interval for intraday data. Required when series_type='intraday'."
    )

    adjusted: bool | None = Field(
        True,
        description=(
            "Return adjusted intraday data (split/dividend adjusted). "
            "Only applicable for series_type='intraday'. Default: True."
        ),
    )

    extended_hours: bool | None = Field(
        True,
        description=(
            "Include extended trading hours (pre-market/after-hours). "
            "Only applicable for series_type='intraday'. Default: True."
        ),
    )

    month: str | None = Field(
        None,
        description=(
            "Query specific month of intraday data in YYYY-MM format (e.g., '2024-01'). "
            "Only applicable for series_type='intraday'. Supports months from 2000-01 onwards."
        ),
    )

    # General parameters
    outputsize: Literal["compact", "full"] | None = Field(
        "compact",
        description=(
            "Output size. 'compact' returns latest 100 data points, 'full' returns complete history "
            "(20+ years for daily/weekly/monthly, 30 days for intraday). Default: 'compact'."
        ),
    )

    datatype: Literal["json", "csv"] | None = Field(
        "csv", description="Output format. Options: 'json' or 'csv'. Default: 'csv'."
    )

    # Bulk quotes parameter
    symbols: str | None = Field(
        None,
        description=(
            "Comma-separated list of ticker symbols (e.g., 'AAPL,MSFT,GOOGL'). "
            "Required when series_type='bulk_quotes'. Maximum 100 symbols."
        ),
    )

    # Search parameter
    keywords: str | None = Field(
        None,
        description=(
            "Search keywords for symbol lookup (e.g., 'microsoft', 'tesla'). "
            "Required when series_type='search'."
        ),
    )

    # Entitlement parameter (for premium features)
    entitlement: Literal["delayed", "realtime"] | None = Field(
        None,
        description=(
            "Data entitlement level. 'delayed' for 15-minute delayed data, "
            "'realtime' for real-time data. Optional - depends on API key permissions."
        ),
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
            raise ValueError("month must be in YYYY-MM format (e.g., '2024-01')")

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

    @field_validator("symbols")
    @classmethod
    def validate_symbols_count(cls, v: str | None) -> str | None:
        """
        Validate that bulk quotes doesn't exceed 100 symbols.

        Args:
            v: Comma-separated symbol list.

        Returns:
            Validated symbols string.

        Raises:
            ValueError: If more than 100 symbols provided.
        """
        if v is None:
            return v

        symbol_list = [s.strip() for s in v.split(",") if s.strip()]

        if len(symbol_list) > 100:
            raise ValueError(
                f"bulk_quotes supports maximum 100 symbols, got {len(symbol_list)}. "
                "Split your request into multiple calls."
            )

        if len(symbol_list) == 0:
            raise ValueError("symbols parameter cannot be empty")

        return v

    @model_validator(mode="after")
    def validate_series_type_requirements(self):
        """
        Validate that required parameters are provided based on series_type.

        This validator enforces conditional parameter requirements:
        - intraday: requires symbol and interval
        - daily/weekly/monthly (all variants): requires symbol
        - quote: requires symbol
        - bulk_quotes: requires symbols (not symbol)
        - search: requires keywords
        - market_status: no requirements

        Returns:
            Validated model instance.

        Raises:
            ValueError: If required parameters are missing for the series_type.
        """
        series_type = self.series_type

        # Intraday: requires symbol and interval
        if series_type == "intraday":
            if not self.symbol:
                raise ValueError("symbol is required when series_type='intraday'")
            if not self.interval:
                raise ValueError("interval is required when series_type='intraday'")

        # Daily/weekly/monthly (all variants): requires symbol
        elif series_type in [
            "daily",
            "daily_adjusted",
            "weekly",
            "weekly_adjusted",
            "monthly",
            "monthly_adjusted",
        ]:
            if not self.symbol:
                raise ValueError(f"symbol is required when series_type='{series_type}'")

        # Quote: requires symbol
        elif series_type == "quote":
            if not self.symbol:
                raise ValueError("symbol is required when series_type='quote'")

        # Bulk quotes: requires symbols (not symbol)
        elif series_type == "bulk_quotes":
            if self.symbol:
                raise ValueError(
                    "Use 'symbols' (not 'symbol') parameter for series_type='bulk_quotes'. "
                    "Example: symbols='AAPL,MSFT,GOOGL'"
                )
            if not self.symbols:
                raise ValueError(
                    "symbols parameter is required when series_type='bulk_quotes'. "
                    "Provide comma-separated list of symbols (e.g., 'AAPL,MSFT,GOOGL')."
                )

        # Search: requires keywords
        elif series_type == "search":
            if not self.keywords:
                raise ValueError(
                    "keywords parameter is required when series_type='search'. "
                    "Example: keywords='microsoft'"
                )

        # Market status: no requirements (but symbol/symbols/keywords should not be provided)
        elif series_type == "market_status":
            if self.symbol or self.symbols or self.keywords:
                raise ValueError(
                    "series_type='market_status' does not require symbol, symbols, or keywords"
                )

        # Validate that force_inline and force_file are mutually exclusive
        if self.force_inline and self.force_file:
            raise ValueError("force_inline and force_file are mutually exclusive")

        return self
