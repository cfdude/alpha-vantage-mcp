"""
Routing logic for unified forex and crypto tools.

This module maps timeframe/data_type values to Alpha Vantage API function names
and transforms request parameters into API-compatible format.
"""

from typing import Any

from .crypto_schema import CryptoRequest
from .forex_schema import ForexRequest

# Mapping of forex timeframe to Alpha Vantage API function names
FOREX_TIMEFRAME_TO_FUNCTION = {
    "intraday": "FX_INTRADAY",
    "daily": "FX_DAILY",
    "weekly": "FX_WEEKLY",
    "monthly": "FX_MONTHLY",
}

# Mapping of crypto data_type/timeframe combinations to Alpha Vantage API function names
CRYPTO_DATA_TYPE_TO_FUNCTION = {
    ("timeseries", "intraday"): "CRYPTO_INTRADAY",
    ("timeseries", "daily"): "DIGITAL_CURRENCY_DAILY",
    ("timeseries", "weekly"): "DIGITAL_CURRENCY_WEEKLY",
    ("timeseries", "monthly"): "DIGITAL_CURRENCY_MONTHLY",
    ("exchange_rate", None): "CURRENCY_EXCHANGE_RATE",
}


class RoutingError(Exception):
    """Exception raised when request routing fails."""

    pass


def get_forex_api_function_name(timeframe: str) -> str:
    """
    Get Alpha Vantage API function name for a forex timeframe.

    Args:
        timeframe: The timeframe from ForexRequest.

    Returns:
        Alpha Vantage API function name.

    Raises:
        ValueError: If timeframe is not recognized.

    Examples:
        >>> get_forex_api_function_name("intraday")
        'FX_INTRADAY'
        >>> get_forex_api_function_name("daily")
        'FX_DAILY'
    """
    if timeframe not in FOREX_TIMEFRAME_TO_FUNCTION:
        valid_timeframes = ", ".join(FOREX_TIMEFRAME_TO_FUNCTION.keys())
        raise ValueError(
            f"Unknown forex timeframe '{timeframe}'. Valid options: {valid_timeframes}"
        )

    return FOREX_TIMEFRAME_TO_FUNCTION[timeframe]


def get_crypto_api_function_name(data_type: str, timeframe: str | None) -> str:
    """
    Get Alpha Vantage API function name for crypto data type and timeframe.

    Args:
        data_type: The data_type from CryptoRequest.
        timeframe: The timeframe from CryptoRequest (None for exchange_rate).

    Returns:
        Alpha Vantage API function name.

    Raises:
        ValueError: If data_type/timeframe combination is not recognized.

    Examples:
        >>> get_crypto_api_function_name("timeseries", "daily")
        'DIGITAL_CURRENCY_DAILY'
        >>> get_crypto_api_function_name("exchange_rate", None)
        'CURRENCY_EXCHANGE_RATE'
    """
    key = (data_type, timeframe)
    if key not in CRYPTO_DATA_TYPE_TO_FUNCTION:
        valid_combos = [f"{dt}/{tf}" for dt, tf in CRYPTO_DATA_TYPE_TO_FUNCTION.keys()]
        raise ValueError(
            f"Unknown crypto data_type/timeframe combination '{data_type}/{timeframe}'. "
            f"Valid options: {', '.join(valid_combos)}"
        )

    return CRYPTO_DATA_TYPE_TO_FUNCTION[key]


def transform_forex_params(request: ForexRequest) -> dict[str, Any]:
    """
    Transform ForexRequest into Alpha Vantage API parameters.

    This function:
    1. Extracts only the parameters needed for the specific timeframe
    2. Converts parameter names to Alpha Vantage API format

    Args:
        request: Validated ForexRequest instance.

    Returns:
        Dictionary of API parameters ready for _make_api_request.

    Examples:
        >>> request = ForexRequest(
        ...     timeframe="intraday",
        ...     from_symbol="EUR",
        ...     to_symbol="USD",
        ...     interval="5min",
        ...     outputsize="compact"
        ... )
        >>> params = transform_forex_params(request)
        >>> params["from_symbol"]
        'EUR'
        >>> params["to_symbol"]
        'USD'
        >>> params["interval"]
        '5min'
    """
    timeframe = request.timeframe
    params: dict[str, Any] = {}

    # Common parameters (always included)
    params["from_symbol"] = request.from_symbol
    params["to_symbol"] = request.to_symbol
    params["datatype"] = request.datatype

    # Timeframe-specific parameter extraction
    if timeframe == "intraday":
        # Intraday requires: from_symbol, to_symbol, interval
        # Optional: outputsize
        params["interval"] = request.interval
        params["outputsize"] = request.outputsize

    elif timeframe == "daily":
        # Daily optional: outputsize
        params["outputsize"] = request.outputsize

    # Weekly and Monthly have no additional parameters beyond from_symbol, to_symbol, datatype

    return params


def transform_crypto_params(request: CryptoRequest) -> dict[str, Any]:
    """
    Transform CryptoRequest into Alpha Vantage API parameters.

    This function:
    1. Extracts only the parameters needed for the specific data_type/timeframe
    2. Converts parameter names to Alpha Vantage API format

    Args:
        request: Validated CryptoRequest instance.

    Returns:
        Dictionary of API parameters ready for _make_api_request.

    Examples:
        >>> request = CryptoRequest(
        ...     data_type="timeseries",
        ...     timeframe="intraday",
        ...     symbol="BTC",
        ...     market="USD",
        ...     interval="5min",
        ...     outputsize="compact"
        ... )
        >>> params = transform_crypto_params(request)
        >>> params["symbol"]
        'BTC'
        >>> params["market"]
        'USD'
        >>> params["interval"]
        '5min'
    """
    data_type = request.data_type
    params: dict[str, Any] = {}

    # Common parameter (always included)
    params["datatype"] = request.datatype

    # Data type specific parameter extraction
    if data_type == "timeseries":
        timeframe = request.timeframe

        # All timeseries require: symbol, market
        params["symbol"] = request.symbol
        params["market"] = request.market

        if timeframe == "intraday":
            # Intraday additionally requires: interval, outputsize
            params["interval"] = request.interval
            params["outputsize"] = request.outputsize

        # Daily/weekly/monthly have no additional parameters beyond symbol, market, datatype

    elif data_type == "exchange_rate":
        # Exchange rate requires: from_currency, to_currency
        params["from_currency"] = request.from_currency
        params["to_currency"] = request.to_currency

    return params


def validate_forex_routing(request: ForexRequest) -> None:
    """
    Validate that the forex request can be properly routed.

    This is a final safety check before making the API call.
    Should not raise any errors if the ForexRequest validation
    worked correctly, but provides defense-in-depth.

    Args:
        request: ForexRequest instance.

    Raises:
        ValueError: If routing validation fails.

    Examples:
        >>> request = ForexRequest(
        ...     timeframe="intraday",
        ...     from_symbol="EUR",
        ...     to_symbol="USD",
        ...     interval="5min"
        ... )
        >>> validate_forex_routing(request)  # No error
    """
    timeframe = request.timeframe

    # Verify we can route this timeframe
    if timeframe not in FOREX_TIMEFRAME_TO_FUNCTION:
        raise ValueError(f"Cannot route forex timeframe '{timeframe}'")

    # These validations should already be caught by Pydantic,
    # but we double-check for safety
    if timeframe == "intraday" and not request.interval:
        raise ValueError("Routing failed: intraday forex requires interval parameter")

    if not request.from_symbol or not request.to_symbol:
        raise ValueError("Routing failed: forex requires from_symbol and to_symbol parameters")


def validate_crypto_routing(request: CryptoRequest) -> None:
    """
    Validate that the crypto request can be properly routed.

    This is a final safety check before making the API call.
    Should not raise any errors if the CryptoRequest validation
    worked correctly, but provides defense-in-depth.

    Args:
        request: CryptoRequest instance.

    Raises:
        ValueError: If routing validation fails.

    Examples:
        >>> request = CryptoRequest(
        ...     data_type="timeseries",
        ...     timeframe="daily",
        ...     symbol="BTC",
        ...     market="USD"
        ... )
        >>> validate_crypto_routing(request)  # No error
    """
    data_type = request.data_type
    timeframe = request.timeframe

    # Verify we can route this data_type/timeframe combination
    key = (data_type, timeframe)
    if key not in CRYPTO_DATA_TYPE_TO_FUNCTION:
        raise ValueError(f"Cannot route crypto data_type/timeframe combination: {key}")

    # These validations should already be caught by Pydantic,
    # but we double-check for safety
    if data_type == "timeseries":
        if not request.symbol or not request.market:
            raise ValueError(
                "Routing failed: timeseries crypto requires symbol and market parameters"
            )

        if timeframe == "intraday" and not request.interval:
            raise ValueError(
                "Routing failed: intraday crypto timeseries requires interval parameter"
            )

    elif data_type == "exchange_rate":
        if not request.from_currency or not request.to_currency:
            raise ValueError(
                "Routing failed: exchange_rate requires from_currency and to_currency parameters"
            )


def route_forex_request(request: ForexRequest) -> tuple[str, dict[str, Any]]:
    """
    Route a ForexRequest to the appropriate API function with parameters.

    This is the main entry point for forex routing logic. It:
    1. Validates the request can be routed
    2. Gets the API function name
    3. Transforms the parameters

    Args:
        request: Validated ForexRequest instance.

    Returns:
        Tuple of (api_function_name, api_parameters).

    Raises:
        RoutingError: If routing fails for any reason.

    Examples:
        >>> request = ForexRequest(
        ...     timeframe="daily",
        ...     from_symbol="EUR",
        ...     to_symbol="USD",
        ...     outputsize="full"
        ... )
        >>> function_name, params = route_forex_request(request)
        >>> function_name
        'FX_DAILY'
        >>> params["from_symbol"]
        'EUR'
        >>> params["outputsize"]
        'full'
    """
    try:
        # Validate routing
        validate_forex_routing(request)

        # Get API function name
        function_name = get_forex_api_function_name(request.timeframe)

        # Transform parameters
        params = transform_forex_params(request)

        return function_name, params

    except ValueError as e:
        raise RoutingError(f"Failed to route forex request: {e}") from e
    except Exception as e:
        raise RoutingError(
            f"Unexpected error during forex routing: {e}. "
            "Please report this issue with your request details."
        ) from e


def route_crypto_request(request: CryptoRequest) -> tuple[str, dict[str, Any]]:
    """
    Route a CryptoRequest to the appropriate API function with parameters.

    This is the main entry point for crypto routing logic. It:
    1. Validates the request can be routed
    2. Gets the API function name
    3. Transforms the parameters

    Args:
        request: Validated CryptoRequest instance.

    Returns:
        Tuple of (api_function_name, api_parameters).

    Raises:
        RoutingError: If routing fails for any reason.

    Examples:
        >>> request = CryptoRequest(
        ...     data_type="timeseries",
        ...     timeframe="daily",
        ...     symbol="BTC",
        ...     market="USD"
        ... )
        >>> function_name, params = route_crypto_request(request)
        >>> function_name
        'DIGITAL_CURRENCY_DAILY'
        >>> params["symbol"]
        'BTC'
        >>> params["market"]
        'USD'

        >>> request = CryptoRequest(
        ...     data_type="exchange_rate",
        ...     from_currency="BTC",
        ...     to_currency="USD"
        ... )
        >>> function_name, params = route_crypto_request(request)
        >>> function_name
        'CURRENCY_EXCHANGE_RATE'
        >>> params["from_currency"]
        'BTC'
    """
    try:
        # Validate routing
        validate_crypto_routing(request)

        # Get API function name
        function_name = get_crypto_api_function_name(request.data_type, request.timeframe)

        # Transform parameters
        params = transform_crypto_params(request)

        return function_name, params

    except ValueError as e:
        raise RoutingError(f"Failed to route crypto request: {e}") from e
    except Exception as e:
        raise RoutingError(
            f"Unexpected error during crypto routing: {e}. "
            "Please report this issue with your request details."
        ) from e
