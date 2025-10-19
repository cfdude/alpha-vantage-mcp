"""
Unified crypto request schema for Alpha Vantage MCP server.

This module consolidates 5 separate crypto/digital currency API endpoints into a single
GET_CRYPTO_DATA tool with conditional parameter validation based on data_type.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CryptoRequest(BaseModel):
    """
    Unified crypto request schema.

    Consolidates the following Alpha Vantage API endpoints:
    - CRYPTO_INTRADAY (timeseries/intraday)
    - DIGITAL_CURRENCY_DAILY (timeseries/daily)
    - DIGITAL_CURRENCY_WEEKLY (timeseries/weekly)
    - DIGITAL_CURRENCY_MONTHLY (timeseries/monthly)
    - CURRENCY_EXCHANGE_RATE (exchange_rate)

    Examples:
        >>> # Intraday crypto data
        >>> request = CryptoRequest(
        ...     data_type="timeseries",
        ...     timeframe="intraday",
        ...     symbol="BTC",
        ...     market="USD",
        ...     interval="5min",
        ...     outputsize="compact"
        ... )

        >>> # Daily crypto data
        >>> request = CryptoRequest(
        ...     data_type="timeseries",
        ...     timeframe="daily",
        ...     symbol="ETH",
        ...     market="USD"
        ... )

        >>> # Currency exchange rate
        >>> request = CryptoRequest(
        ...     data_type="exchange_rate",
        ...     from_currency="BTC",
        ...     to_currency="USD"
        ... )
    """

    data_type: Literal["timeseries", "exchange_rate"] = Field(
        description=(
            "Type of crypto data to retrieve. Options: "
            "'timeseries' (historical OHLCV data), "
            "'exchange_rate' (current exchange rate between two currencies)"
        )
    )

    # For timeseries
    timeframe: Literal["intraday", "daily", "weekly", "monthly"] | None = Field(
        None,
        description=(
            "Timeframe for timeseries data. Required when data_type='timeseries'. "
            "Options: intraday (1min-60min), daily, weekly, monthly"
        ),
    )

    # Symbol/market for timeseries
    symbol: str | None = Field(
        None,
        description=(
            "Cryptocurrency symbol (e.g., BTC, ETH, XRP). "
            "Required when data_type='timeseries'. "
            "Can be any digital currency from Alpha Vantage's crypto list."
        ),
    )

    market: str | None = Field(
        None,
        description=(
            "Market/exchange currency (e.g., USD, EUR, CNY). "
            "Required when data_type='timeseries'. "
            "The market in which the crypto is traded."
        ),
    )

    # For exchange rate
    from_currency: str | None = Field(
        None,
        description=(
            "Source currency for exchange rate (e.g., BTC, USD, EUR). "
            "Required when data_type='exchange_rate'. "
            "Can be either a digital or physical currency."
        ),
    )

    to_currency: str | None = Field(
        None,
        description=(
            "Destination currency for exchange rate (e.g., USD, BTC, EUR). "
            "Required when data_type='exchange_rate'. "
            "Can be either a digital or physical currency."
        ),
    )

    # Intraday-specific parameter
    interval: Literal["1min", "5min", "15min", "30min", "60min"] | None = Field(
        None,
        description=(
            "Time interval for intraday timeseries data. "
            "Required when data_type='timeseries' and timeframe='intraday'. "
            "Options: 1min, 5min, 15min, 30min, 60min"
        ),
    )

    # Timeseries parameter (intraday only)
    outputsize: Literal["compact", "full"] | None = Field(
        "compact",
        description=(
            "Output size for intraday timeseries. "
            "'compact' returns latest 100 data points, 'full' returns complete history. "
            "Only applicable when data_type='timeseries' and timeframe='intraday'. "
            "Default: 'compact'."
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
    def validate_data_type_params(self):
        """
        Validate that required parameters are provided based on data_type.

        This validator enforces conditional parameter requirements:
        - timeseries: requires timeframe, symbol, and market
          - If timeframe='intraday': also requires interval
        - exchange_rate: requires from_currency and to_currency

        Returns:
            Validated model instance.

        Raises:
            ValueError: If required parameters are missing for the data_type.
        """
        data_type = self.data_type

        if data_type == "timeseries":
            # Timeseries requires: timeframe, symbol, market
            if not self.timeframe:
                raise ValueError(
                    "timeframe is required when data_type='timeseries'. "
                    "Valid options: intraday, daily, weekly, monthly"
                )

            if not self.symbol:
                raise ValueError(
                    "symbol is required when data_type='timeseries'. "
                    "Example: symbol='BTC' or symbol='ETH'"
                )

            if not self.market:
                raise ValueError(
                    "market is required when data_type='timeseries'. "
                    "Example: market='USD' or market='EUR'"
                )

            # Intraday timeseries requires interval
            if self.timeframe == "intraday" and not self.interval:
                raise ValueError(
                    "interval is required when data_type='timeseries' and timeframe='intraday'. "
                    "Valid options: 1min, 5min, 15min, 30min, 60min"
                )

            # Non-intraday timeseries should not have interval
            if self.timeframe != "intraday" and self.interval:
                raise ValueError(
                    f"interval parameter is not applicable for timeframe='{self.timeframe}'. "
                    "The interval parameter is only used with timeframe='intraday'."
                )

            # Exchange rate parameters should not be provided for timeseries
            if self.from_currency or self.to_currency:
                raise ValueError(
                    "from_currency and to_currency are only applicable for data_type='exchange_rate'. "
                    "For timeseries data, use 'symbol' and 'market' parameters instead."
                )

        elif data_type == "exchange_rate":
            # Exchange rate requires: from_currency and to_currency
            if not self.from_currency:
                raise ValueError(
                    "from_currency is required when data_type='exchange_rate'. "
                    "Example: from_currency='BTC' or from_currency='USD'"
                )

            if not self.to_currency:
                raise ValueError(
                    "to_currency is required when data_type='exchange_rate'. "
                    "Example: to_currency='USD' or to_currency='EUR'"
                )

            # Timeseries parameters should not be provided for exchange_rate
            if self.timeframe:
                raise ValueError(
                    "timeframe parameter is not applicable for data_type='exchange_rate'. "
                    "Use data_type='timeseries' if you need historical data."
                )

            if self.symbol or self.market:
                raise ValueError(
                    "symbol and market parameters are only applicable for data_type='timeseries'. "
                    "For exchange rates, use 'from_currency' and 'to_currency' parameters instead."
                )

            if self.interval:
                raise ValueError(
                    "interval parameter is not applicable for data_type='exchange_rate'. "
                    "Exchange rates provide real-time spot prices, not time series."
                )

        # Validate that force_inline and force_file are mutually exclusive
        if self.force_inline and self.force_file:
            raise ValueError("force_inline and force_file are mutually exclusive")

        return self
