"""
Routing logic for unified moving average tool.

This module maps indicator_type values to Alpha Vantage API function names
and transforms request parameters into API-compatible format.
"""

from typing import Any

from .moving_average_schema import MovingAverageRequest

# Mapping of indicator_type to Alpha Vantage API function names
INDICATOR_TYPE_TO_FUNCTION = {
    "sma": "SMA",
    "ema": "EMA",
    "wma": "WMA",
    "dema": "DEMA",
    "tema": "TEMA",
    "trima": "TRIMA",
    "kama": "KAMA",
    "mama": "MAMA",
    "t3": "T3",
    "vwap": "VWAP",
}


def get_api_function_name(indicator_type: str) -> str:
    """
    Get Alpha Vantage API function name for an indicator type.

    Args:
        indicator_type: The indicator type from MovingAverageRequest.

    Returns:
        Alpha Vantage API function name (uppercase).

    Raises:
        ValueError: If indicator_type is not recognized.

    Examples:
        >>> get_api_function_name("sma")
        'SMA'
        >>> get_api_function_name("mama")
        'MAMA'
        >>> get_api_function_name("vwap")
        'VWAP'
    """
    if indicator_type not in INDICATOR_TYPE_TO_FUNCTION:
        valid_types = ", ".join(INDICATOR_TYPE_TO_FUNCTION.keys())
        raise ValueError(f"Unknown indicator_type '{indicator_type}'. Valid options: {valid_types}")

    return INDICATOR_TYPE_TO_FUNCTION[indicator_type]


def transform_request_params(request: MovingAverageRequest) -> dict[str, Any]:
    """
    Transform MovingAverageRequest into Alpha Vantage API parameters.

    This function:
    1. Extracts only the parameters needed for the specific indicator_type
    2. Converts boolean values to lowercase strings for API
    3. Handles special cases for MAMA (fastlimit/slowlimit) and VWAP (no time_period/series_type)

    Args:
        request: Validated MovingAverageRequest instance.

    Returns:
        Dictionary of API parameters ready for _make_api_request.

    Examples:
        >>> # Standard indicator (SMA)
        >>> request = MovingAverageRequest(
        ...     indicator_type="sma",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=60,
        ...     series_type="close"
        ... )
        >>> params = transform_request_params(request)
        >>> params["symbol"]
        'IBM'
        >>> params["time_period"]
        60
        >>> params["series_type"]
        'close'

        >>> # MAMA (no time_period)
        >>> request = MovingAverageRequest(
        ...     indicator_type="mama",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     series_type="close",
        ...     fastlimit=0.01,
        ...     slowlimit=0.01
        ... )
        >>> params = transform_request_params(request)
        >>> params["fastlimit"]
        0.01
        >>> "time_period" in params
        False

        >>> # VWAP (no time_period or series_type)
        >>> request = MovingAverageRequest(
        ...     indicator_type="vwap",
        ...     symbol="IBM",
        ...     interval="5min"
        ... )
        >>> params = transform_request_params(request)
        >>> "time_period" in params
        False
        >>> "series_type" in params
        False
    """
    indicator_type = request.indicator_type
    params: dict[str, Any] = {}

    # Common parameters (all indicators need these)
    params["symbol"] = request.symbol
    params["interval"] = request.interval
    params["datatype"] = request.datatype

    # Standard indicators (SMA, EMA, WMA, DEMA, TEMA, TRIMA, KAMA, T3)
    standard_indicators = ["sma", "ema", "wma", "dema", "tema", "trima", "kama", "t3"]

    if indicator_type in standard_indicators:
        # Standard indicators use time_period and series_type
        params["time_period"] = request.time_period
        params["series_type"] = request.series_type

    elif indicator_type == "mama":
        # MAMA uses series_type, fastlimit, and slowlimit (no time_period)
        params["series_type"] = request.series_type
        params["fastlimit"] = request.fastlimit
        params["slowlimit"] = request.slowlimit

    elif indicator_type == "vwap":
        # VWAP only uses symbol, interval, and datatype (already added above)
        # No time_period, series_type, or MAMA-specific params
        pass

    # Add optional month parameter (intraday only)
    if request.month and request.interval in ["1min", "5min", "15min", "30min", "60min"]:
        params["month"] = request.month

    return params


def get_output_decision_params(request: MovingAverageRequest) -> dict[str, bool]:
    """
    Extract output decision parameters from request.

    These parameters control whether the output should be written to a file
    or returned inline, and can override the automatic decision made by
    the output helper.

    Args:
        request: MovingAverageRequest instance.

    Returns:
        Dictionary with force_inline and force_file flags.

    Examples:
        >>> request = MovingAverageRequest(
        ...     indicator_type="sma",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=60,
        ...     series_type="close",
        ...     force_file=True
        ... )
        >>> params = get_output_decision_params(request)
        >>> params["force_file"]
        True
        >>> params["force_inline"]
        False
    """
    return {
        "force_inline": request.force_inline,
        "force_file": request.force_file,
    }


def validate_routing(request: MovingAverageRequest) -> None:
    """
    Validate that the request can be properly routed.

    This is a final safety check before making the API call.
    Should not raise any errors if the MovingAverageRequest validation
    worked correctly, but provides defense-in-depth.

    Args:
        request: MovingAverageRequest instance.

    Raises:
        ValueError: If routing validation fails.

    Examples:
        >>> request = MovingAverageRequest(
        ...     indicator_type="sma",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=60,
        ...     series_type="close"
        ... )
        >>> validate_routing(request)  # No error
    """
    indicator_type = request.indicator_type

    # Verify we can route this indicator type
    if indicator_type not in INDICATOR_TYPE_TO_FUNCTION:
        raise ValueError(f"Cannot route indicator_type '{indicator_type}'")

    # These validations should already be caught by Pydantic,
    # but we double-check for safety
    standard_indicators = ["sma", "ema", "wma", "dema", "tema", "trima", "kama", "t3"]

    if indicator_type in standard_indicators:
        if request.time_period is None:
            raise ValueError(f"Routing failed: {indicator_type} requires time_period parameter")
        if request.series_type is None:
            raise ValueError(f"Routing failed: {indicator_type} requires series_type parameter")

    elif indicator_type == "mama":
        if request.series_type is None:
            raise ValueError("Routing failed: mama requires series_type parameter")
        if request.fastlimit is None or request.slowlimit is None:
            raise ValueError("Routing failed: mama requires fastlimit and slowlimit parameters")

    elif indicator_type == "vwap":
        intraday_intervals = ["1min", "5min", "15min", "30min", "60min"]
        if request.interval not in intraday_intervals:
            raise ValueError(
                f"Routing failed: vwap requires intraday interval, got '{request.interval}'"
            )


class RoutingError(Exception):
    """Exception raised when request routing fails."""

    pass


def route_request(request: MovingAverageRequest) -> tuple[str, dict[str, Any]]:
    """
    Route a MovingAverageRequest to the appropriate API function with parameters.

    This is the main entry point for the routing logic. It:
    1. Validates the request can be routed
    2. Gets the API function name
    3. Transforms the parameters

    Args:
        request: Validated MovingAverageRequest instance.

    Returns:
        Tuple of (api_function_name, api_parameters).

    Raises:
        RoutingError: If routing fails for any reason.

    Examples:
        >>> request = MovingAverageRequest(
        ...     indicator_type="ema",
        ...     symbol="AAPL",
        ...     interval="daily",
        ...     time_period=200,
        ...     series_type="close"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'EMA'
        >>> params["symbol"]
        'AAPL'
        >>> params["time_period"]
        200

        >>> # MAMA example
        >>> request = MovingAverageRequest(
        ...     indicator_type="mama",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     series_type="close"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'MAMA'
        >>> params["fastlimit"]
        0.01
        >>> params["slowlimit"]
        0.01

        >>> # VWAP example
        >>> request = MovingAverageRequest(
        ...     indicator_type="vwap",
        ...     symbol="MSFT",
        ...     interval="5min"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'VWAP'
        >>> "time_period" in params
        False
        >>> "series_type" in params
        False
    """
    try:
        # Validate routing
        validate_routing(request)

        # Get API function name
        function_name = get_api_function_name(request.indicator_type)

        # Transform parameters
        params = transform_request_params(request)

        return function_name, params

    except ValueError as e:
        raise RoutingError(f"Failed to route request: {e}") from e
    except Exception as e:
        raise RoutingError(
            f"Unexpected error during routing: {e}. "
            "Please report this issue with your request details."
        ) from e
