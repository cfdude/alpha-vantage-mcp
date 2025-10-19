"""
Unified forex and crypto tools for Alpha Vantage MCP server.

This module consolidates 9 separate currency/crypto API endpoints into 2 tools:
- GET_FOREX_DATA: consolidates 4 forex endpoints
- GET_CRYPTO_DATA: consolidates 5 crypto/currency endpoints

Consolidates:
Forex:
- FX_INTRADAY
- FX_DAILY
- FX_WEEKLY
- FX_MONTHLY

Crypto:
- CRYPTO_INTRADAY
- DIGITAL_CURRENCY_DAILY
- DIGITAL_CURRENCY_WEEKLY
- DIGITAL_CURRENCY_MONTHLY
- CURRENCY_EXCHANGE_RATE
"""

import json

from pydantic import ValidationError

from src.common import _make_api_request
from src.tools.registry import tool

from .crypto_schema import CryptoRequest
from .forex_crypto_router import (
    RoutingError,
    route_crypto_request,
    route_forex_request,
)
from .forex_schema import ForexRequest


def _create_error_response(error: Exception, request_data: dict) -> dict:
    """
    Create a standardized error response.

    Args:
        error: The exception that occurred.
        request_data: The original request data.

    Returns:
        Dictionary with error information.
    """
    if isinstance(error, ValidationError):
        # Pydantic validation error - extract field-specific errors
        errors = []
        for err in error.errors():
            field = " -> ".join(str(loc) for loc in err["loc"])
            message = err["msg"]
            errors.append(f"{field}: {message}")

        return {
            "error": "Request validation failed",
            "validation_errors": errors,
            "details": (
                "The request parameters do not meet the requirements. "
                "Please check the parameter descriptions and try again."
            ),
            "request_data": request_data,
        }

    elif isinstance(error, RoutingError):
        # Routing error - problem with timeframe/data_type or parameter routing
        return {
            "error": "Request routing failed",
            "message": str(error),
            "details": (
                "The request could not be routed to an API endpoint. "
                "This may indicate a configuration issue or unsupported parameter combination."
            ),
            "request_data": request_data,
        }

    else:
        # Generic error
        return {
            "error": type(error).__name__,
            "message": str(error),
            "details": "An unexpected error occurred while processing your request.",
            "request_data": request_data,
        }


@tool
def get_forex_data(
    timeframe: str,
    from_symbol: str,
    to_symbol: str,
    interval: str | None = None,
    outputsize: str = "compact",
    datatype: str = "csv",
    force_inline: bool = False,
    force_file: bool = False,
) -> dict | str:
    """
    Unified forex exchange rate data retrieval for all forex timeframes.

    This tool consolidates 4 separate forex APIs into a single endpoint with
    conditional parameter validation based on timeframe. It automatically handles
    large responses using the output helper from Sprint 1.

    Args:
        timeframe: Time period for forex data. Options:
            - 'intraday': Intraday exchange rates (1min to 60min intervals)
            - 'daily': Daily exchange rates (OHLC)
            - 'weekly': Weekly exchange rates (OHLC)
            - 'monthly': Monthly exchange rates (OHLC)

        from_symbol: Source currency code (3-letter forex symbol).
            Examples: 'EUR', 'USD', 'GBP', 'JPY', 'CAD', 'AUD'

        to_symbol: Destination currency code (3-letter forex symbol).
            Examples: 'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD'

        interval: Time interval for intraday data. Required when timeframe='intraday'.
            Options: '1min', '5min', '15min', '30min', '60min'

        outputsize: Output size. Options: 'compact' (latest 100 points), 'full' (complete history).
            Default: 'compact'. Applies to intraday and daily timeframes.

        datatype: Output format. Options: 'json', 'csv'. Default: 'csv'.

        force_inline: Force inline output regardless of size (default: False).
            Overrides automatic file/inline decision.

        force_file: Force file output regardless of size (default: False).
            Overrides automatic file/inline decision.

    Returns:
        Forex exchange rate data in requested format (dict for JSON, str for CSV).
        For large responses, may return a file reference instead of inline data.

    Raises:
        ValidationError: If request parameters are invalid for the specified timeframe.
        RoutingError: If request cannot be routed to an API endpoint.

    Examples:
        # Get intraday EUR/USD exchange rate
        >>> result = get_forex_data(
        ...     timeframe="intraday",
        ...     from_symbol="EUR",
        ...     to_symbol="USD",
        ...     interval="5min",
        ...     outputsize="compact"
        ... )

        # Get daily GBP/USD exchange rate (full history)
        >>> result = get_forex_data(
        ...     timeframe="daily",
        ...     from_symbol="GBP",
        ...     to_symbol="USD",
        ...     outputsize="full"
        ... )

        # Get weekly EUR/JPY exchange rate
        >>> result = get_forex_data(
        ...     timeframe="weekly",
        ...     from_symbol="EUR",
        ...     to_symbol="JPY"
        ... )

    Context Window Reduction:
        This single tool replaces 4 individual forex tools, reducing context window usage.
    """
    # Collect all input parameters
    request_data = {
        "timeframe": timeframe,
        "from_symbol": from_symbol,
        "to_symbol": to_symbol,
        "interval": interval,
        "outputsize": outputsize,
        "datatype": datatype,
        "force_inline": force_inline,
        "force_file": force_file,
    }

    try:
        # Step 1: Validate and parse request using Pydantic schema
        request = ForexRequest(**request_data)

        # Step 2: Route request to appropriate API function
        function_name, api_params = route_forex_request(request)

        # Step 3: Make API request
        response = _make_api_request(function_name, api_params)

        # Step 4: Handle output decision (file vs inline)
        # NOTE: Sprint 1 output helper integration would go here
        # For now, we return the response as-is since _make_api_request
        # already handles large responses with R2 upload
        # TODO: Integrate with OutputHandler for file-based output when needed

        return response

    except ValidationError as e:
        # Validation failed - return structured error
        error_response = _create_error_response(e, request_data)
        return json.dumps(error_response, indent=2)

    except RoutingError as e:
        # Routing failed - return structured error
        error_response = _create_error_response(e, request_data)
        return json.dumps(error_response, indent=2)

    except Exception as e:
        # Unexpected error - return generic error
        error_response = _create_error_response(e, request_data)
        return json.dumps(error_response, indent=2)


@tool
def get_crypto_data(
    data_type: str,
    timeframe: str | None = None,
    symbol: str | None = None,
    market: str | None = None,
    from_currency: str | None = None,
    to_currency: str | None = None,
    interval: str | None = None,
    outputsize: str = "compact",
    datatype: str = "csv",
    force_inline: bool = False,
    force_file: bool = False,
) -> dict | str:
    """
    Unified cryptocurrency data retrieval including time series and exchange rates.

    This tool consolidates 5 separate crypto APIs into a single endpoint with
    conditional parameter validation based on data_type. It automatically handles
    large responses using the output helper from Sprint 1.

    Args:
        data_type: Type of crypto data to retrieve. Options:
            - 'timeseries': Historical OHLCV time series data
            - 'exchange_rate': Current exchange rate between two currencies

        timeframe: Timeframe for timeseries data. Required when data_type='timeseries'. Options:
            - 'intraday': Intraday crypto data (1min to 60min intervals)
            - 'daily': Daily crypto time series
            - 'weekly': Weekly crypto time series
            - 'monthly': Monthly crypto time series

        symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH', 'XRP').
            Required when data_type='timeseries'.

        market: Market/exchange currency (e.g., 'USD', 'EUR', 'CNY').
            Required when data_type='timeseries'.

        from_currency: Source currency for exchange rate (e.g., 'BTC', 'USD', 'EUR').
            Required when data_type='exchange_rate'. Can be digital or physical currency.

        to_currency: Destination currency for exchange rate (e.g., 'USD', 'BTC', 'EUR').
            Required when data_type='exchange_rate'. Can be digital or physical currency.

        interval: Time interval for intraday timeseries data.
            Required when data_type='timeseries' and timeframe='intraday'.
            Options: '1min', '5min', '15min', '30min', '60min'

        outputsize: Output size for intraday timeseries.
            'compact' returns latest 100 data points, 'full' returns complete history.
            Only applicable when data_type='timeseries' and timeframe='intraday'.
            Default: 'compact'.

        datatype: Output format. Options: 'json', 'csv'. Default: 'csv'.

        force_inline: Force inline output regardless of size (default: False).
            Overrides automatic file/inline decision.

        force_file: Force file output regardless of size (default: False).
            Overrides automatic file/inline decision.

    Returns:
        Cryptocurrency data in requested format (dict for JSON, str for CSV).
        For large responses, may return a file reference instead of inline data.

    Raises:
        ValidationError: If request parameters are invalid for the specified data_type.
        RoutingError: If request cannot be routed to an API endpoint.

    Examples:
        # Get intraday BTC/USD crypto data
        >>> result = get_crypto_data(
        ...     data_type="timeseries",
        ...     timeframe="intraday",
        ...     symbol="BTC",
        ...     market="USD",
        ...     interval="5min",
        ...     outputsize="compact"
        ... )

        # Get daily ETH/USD crypto data
        >>> result = get_crypto_data(
        ...     data_type="timeseries",
        ...     timeframe="daily",
        ...     symbol="ETH",
        ...     market="USD"
        ... )

        # Get BTC to USD exchange rate
        >>> result = get_crypto_data(
        ...     data_type="exchange_rate",
        ...     from_currency="BTC",
        ...     to_currency="USD"
        ... )

        # Get USD to BTC exchange rate (physical to digital)
        >>> result = get_crypto_data(
        ...     data_type="exchange_rate",
        ...     from_currency="USD",
        ...     to_currency="BTC"
        ... )

    Context Window Reduction:
        This single tool replaces 5 individual crypto tools, reducing context window usage.
    """
    # Collect all input parameters
    request_data = {
        "data_type": data_type,
        "timeframe": timeframe,
        "symbol": symbol,
        "market": market,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "interval": interval,
        "outputsize": outputsize,
        "datatype": datatype,
        "force_inline": force_inline,
        "force_file": force_file,
    }

    try:
        # Step 1: Validate and parse request using Pydantic schema
        request = CryptoRequest(**request_data)

        # Step 2: Route request to appropriate API function
        function_name, api_params = route_crypto_request(request)

        # Step 3: Make API request
        response = _make_api_request(function_name, api_params)

        # Step 4: Handle output decision (file vs inline)
        # NOTE: Sprint 1 output helper integration would go here
        # For now, we return the response as-is since _make_api_request
        # already handles large responses with R2 upload
        # TODO: Integrate with OutputHandler for file-based output when needed

        return response

    except ValidationError as e:
        # Validation failed - return structured error
        error_response = _create_error_response(e, request_data)
        return json.dumps(error_response, indent=2)

    except RoutingError as e:
        # Routing failed - return structured error
        error_response = _create_error_response(e, request_data)
        return json.dumps(error_response, indent=2)

    except Exception as e:
        # Unexpected error - return generic error
        error_response = _create_error_response(e, request_data)
        return json.dumps(error_response, indent=2)
