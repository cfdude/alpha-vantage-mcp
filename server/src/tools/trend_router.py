"""
Routing logic for unified trend indicator tool.

This module maps indicator_type values to Alpha Vantage API function names
and transforms request parameters into API-compatible format.
"""

from typing import Any

from .trend_schema import TrendRequest

# Mapping of indicator_type to Alpha Vantage API function names
INDICATOR_TYPE_TO_FUNCTION = {
    "aroon": "AROON",
    "aroonosc": "AROONOSC",
    "dx": "DX",
    "minus_di": "MINUS_DI",
    "plus_di": "PLUS_DI",
    "minus_dm": "MINUS_DM",
    "plus_dm": "PLUS_DM",
}


def get_api_function_name(indicator_type: str) -> str:
    """
    Get Alpha Vantage API function name for an indicator type.

    Args:
        indicator_type: The indicator type from TrendRequest.

    Returns:
        Alpha Vantage API function name (uppercase).

    Raises:
        ValueError: If indicator_type is not recognized.

    Examples:
        >>> get_api_function_name("aroon")
        'AROON'
        >>> get_api_function_name("dx")
        'DX'
    """
    if indicator_type not in INDICATOR_TYPE_TO_FUNCTION:
        valid_types = ", ".join(INDICATOR_TYPE_TO_FUNCTION.keys())
        raise ValueError(f"Unknown indicator_type '{indicator_type}'. Valid options: {valid_types}")

    return INDICATOR_TYPE_TO_FUNCTION[indicator_type]


def transform_request_params(request: TrendRequest) -> dict[str, Any]:
    """
    Transform TrendRequest into Alpha Vantage API parameters.

    This function:
    1. Extracts parameters needed for the specific indicator_type
    2. All trend indicators use the same parameters: symbol, interval, time_period

    Args:
        request: Validated TrendRequest instance.

    Returns:
        Dictionary of API parameters ready for _make_api_request.

    Examples:
        >>> request = TrendRequest(
        ...     indicator_type="aroon",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=14
        ... )
        >>> params = transform_request_params(request)
        >>> params["symbol"]
        'IBM'
        >>> params["time_period"]
        14
    """
    params: dict[str, Any] = {}

    # Common parameters (all trend indicators use these)
    params["symbol"] = request.symbol
    params["interval"] = request.interval
    params["time_period"] = request.time_period
    params["datatype"] = request.datatype

    # Add optional month parameter (intraday only)
    if request.month and request.interval in ["1min", "5min", "15min", "30min", "60min"]:
        params["month"] = request.month

    return params


def get_output_decision_params(request: TrendRequest) -> dict[str, bool]:
    """
    Extract output decision parameters from request.

    These parameters control whether the output should be written to a file
    or returned inline, and can override the automatic decision made by
    the output helper.

    Args:
        request: TrendRequest instance.

    Returns:
        Dictionary with force_inline and force_file flags.

    Examples:
        >>> request = TrendRequest(
        ...     indicator_type="dx",
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


def validate_routing(request: TrendRequest) -> None:
    """
    Validate that the request can be properly routed.

    This is a final safety check before making the API call.
    Should not raise any errors if the TrendRequest validation
    worked correctly, but provides defense-in-depth.

    Args:
        request: TrendRequest instance.

    Raises:
        ValueError: If routing validation fails.

    Examples:
        >>> request = TrendRequest(
        ...     indicator_type="aroon",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=14
        ... )
        >>> validate_routing(request)  # No error
    """
    indicator_type = request.indicator_type

    # Verify we can route this indicator type
    if indicator_type not in INDICATOR_TYPE_TO_FUNCTION:
        raise ValueError(f"Cannot route indicator_type '{indicator_type}'")

    # All trend indicators require time_period (already validated by Pydantic)
    if request.time_period is None:
        raise ValueError(f"Routing failed: {indicator_type} requires time_period parameter")


class RoutingError(Exception):
    """Exception raised when request routing fails."""

    pass


def route_request(request: TrendRequest) -> tuple[str, dict[str, Any]]:
    """
    Route a TrendRequest to the appropriate API function with parameters.

    This is the main entry point for the routing logic. It:
    1. Validates the request can be routed
    2. Gets the API function name
    3. Transforms the parameters

    Args:
        request: Validated TrendRequest instance.

    Returns:
        Tuple of (api_function_name, api_parameters).

    Raises:
        RoutingError: If routing fails for any reason.

    Examples:
        >>> request = TrendRequest(
        ...     indicator_type="aroon",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=14
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'AROON'
        >>> params["time_period"]
        14
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
