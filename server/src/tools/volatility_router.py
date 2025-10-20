"""
Routing logic for unified volatility indicator tool.

This module maps indicator_type values to Alpha Vantage API function names
and transforms request parameters into API-compatible format.
"""

from typing import Any

from .volatility_schema import VolatilityRequest

# Mapping of indicator_type to Alpha Vantage API function names
INDICATOR_TYPE_TO_FUNCTION = {
    "bbands": "BBANDS",
    "trange": "TRANGE",
    "atr": "ATR",
    "natr": "NATR",
    "midpoint": "MIDPOINT",
    "midprice": "MIDPRICE",
    "sar": "SAR",
}


def get_api_function_name(indicator_type: str) -> str:
    """
    Get Alpha Vantage API function name for an indicator type.

    Args:
        indicator_type: The indicator type from VolatilityRequest.

    Returns:
        Alpha Vantage API function name (uppercase).

    Raises:
        ValueError: If indicator_type is not recognized.

    Examples:
        >>> get_api_function_name("bbands")
        'BBANDS'
        >>> get_api_function_name("sar")
        'SAR'
    """
    if indicator_type not in INDICATOR_TYPE_TO_FUNCTION:
        valid_types = ", ".join(INDICATOR_TYPE_TO_FUNCTION.keys())
        raise ValueError(f"Unknown indicator_type '{indicator_type}'. Valid options: {valid_types}")

    return INDICATOR_TYPE_TO_FUNCTION[indicator_type]


def transform_request_params(request: VolatilityRequest) -> dict[str, Any]:
    """
    Transform VolatilityRequest into Alpha Vantage API parameters.

    This function:
    1. Extracts only the parameters needed for the specific indicator_type
    2. Handles complex parameter patterns (BBANDS, SAR, simple time_period indicators)

    Args:
        request: Validated VolatilityRequest instance.

    Returns:
        Dictionary of API parameters ready for _make_api_request.

    Examples:
        >>> # BBANDS (complex)
        >>> request = VolatilityRequest(
        ...     indicator_type="bbands",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=20,
        ...     series_type="close"
        ... )
        >>> params = transform_request_params(request)
        >>> params["time_period"]
        20
        >>> params["nbdevup"]
        2

        >>> # SAR (unique)
        >>> request = VolatilityRequest(
        ...     indicator_type="sar",
        ...     symbol="AAPL",
        ...     interval="daily"
        ... )
        >>> params = transform_request_params(request)
        >>> params["acceleration"]
        0.01
        >>> "time_period" in params
        False

        >>> # TRANGE (no params)
        >>> request = VolatilityRequest(
        ...     indicator_type="trange",
        ...     symbol="MSFT",
        ...     interval="daily"
        ... )
        >>> params = transform_request_params(request)
        >>> "time_period" in params
        False
    """
    indicator_type = request.indicator_type
    params: dict[str, Any] = {}

    # Common parameters (all indicators need these)
    params["symbol"] = request.symbol
    params["interval"] = request.interval
    params["datatype"] = request.datatype

    # BBANDS (time_period, series_type, nbdevup, nbdevdn, matype)
    if indicator_type == "bbands":
        params["time_period"] = request.time_period
        params["series_type"] = request.series_type
        params["nbdevup"] = request.nbdevup
        params["nbdevdn"] = request.nbdevdn
        params["matype"] = request.matype

    # ATR, NATR, MIDPRICE (just time_period)
    elif indicator_type in ["atr", "natr", "midprice"]:
        params["time_period"] = request.time_period

    # MIDPOINT (time_period + series_type)
    elif indicator_type == "midpoint":
        params["time_period"] = request.time_period
        params["series_type"] = request.series_type

    # SAR (acceleration + maximum, no time_period)
    elif indicator_type == "sar":
        params["acceleration"] = request.acceleration
        params["maximum"] = request.maximum

    # TRANGE (no additional params)
    # Already added symbol, interval, datatype above

    # Add optional month parameter (intraday only)
    if request.month and request.interval in ["1min", "5min", "15min", "30min", "60min"]:
        params["month"] = request.month

    return params


def get_output_decision_params(request: VolatilityRequest) -> dict[str, bool]:
    """
    Extract output decision parameters from request.

    These parameters control whether the output should be written to a file
    or returned inline, and can override the automatic decision made by
    the output helper.

    Args:
        request: VolatilityRequest instance.

    Returns:
        Dictionary with force_inline and force_file flags.

    Examples:
        >>> request = VolatilityRequest(
        ...     indicator_type="atr",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=14,
        ...     force_file=True
        ... )
        >>> params = get_output_decision_params(request)
        >>> params["force_file"]
        True
    """
    return {
        "force_inline": request.force_inline,
        "force_file": request.force_file,
    }


def validate_routing(request: VolatilityRequest) -> None:
    """
    Validate that the request can be properly routed.

    This is a final safety check before making the API call.
    Should not raise any errors if the VolatilityRequest validation
    worked correctly, but provides defense-in-depth.

    Args:
        request: VolatilityRequest instance.

    Raises:
        ValueError: If routing validation fails.

    Examples:
        >>> request = VolatilityRequest(
        ...     indicator_type="bbands",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=20,
        ...     series_type="close"
        ... )
        >>> validate_routing(request)  # No error
    """
    indicator_type = request.indicator_type

    # Verify we can route this indicator type
    if indicator_type not in INDICATOR_TYPE_TO_FUNCTION:
        raise ValueError(f"Cannot route indicator_type '{indicator_type}'")

    # Validate parameter presence (already validated by Pydantic, but double-check)
    if indicator_type == "bbands":
        if request.time_period is None or request.series_type is None:
            raise ValueError("Routing failed: bbands requires time_period and series_type")

    elif indicator_type in ["atr", "natr", "midprice"]:
        if request.time_period is None:
            raise ValueError(f"Routing failed: {indicator_type} requires time_period")

    elif indicator_type == "midpoint":
        if request.time_period is None or request.series_type is None:
            raise ValueError("Routing failed: midpoint requires time_period and series_type")

    elif indicator_type == "sar":
        if request.acceleration is None or request.maximum is None:
            raise ValueError("Routing failed: sar requires acceleration and maximum")

    # TRANGE has no additional params to validate


class RoutingError(Exception):
    """Exception raised when request routing fails."""

    pass


def route_request(request: VolatilityRequest) -> tuple[str, dict[str, Any]]:
    """
    Route a VolatilityRequest to the appropriate API function with parameters.

    This is the main entry point for the routing logic. It:
    1. Validates the request can be routed
    2. Gets the API function name
    3. Transforms the parameters

    Args:
        request: Validated VolatilityRequest instance.

    Returns:
        Tuple of (api_function_name, api_parameters).

    Raises:
        RoutingError: If routing fails for any reason.

    Examples:
        >>> # BBANDS
        >>> request = VolatilityRequest(
        ...     indicator_type="bbands",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=20,
        ...     series_type="close"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'BBANDS'
        >>> params["nbdevup"]
        2

        >>> # SAR
        >>> request = VolatilityRequest(
        ...     indicator_type="sar",
        ...     symbol="AAPL",
        ...     interval="daily"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'SAR'
        >>> params["acceleration"]
        0.01
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
