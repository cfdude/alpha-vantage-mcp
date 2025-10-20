"""
Routing logic for unified cycle (Hilbert Transform) indicator tool.

This module maps indicator_type values to Alpha Vantage API function names
and transforms request parameters into API-compatible format.
"""

from typing import Any

from .cycle_schema import CycleRequest

# Mapping of indicator_type to Alpha Vantage API function names
INDICATOR_TYPE_TO_FUNCTION = {
    "ht_trendline": "HT_TRENDLINE",
    "ht_sine": "HT_SINE",
    "ht_trendmode": "HT_TRENDMODE",
    "ht_dcperiod": "HT_DCPERIOD",
    "ht_dcphase": "HT_DCPHASE",
    "ht_phasor": "HT_PHASOR",
}


def get_api_function_name(indicator_type: str) -> str:
    """
    Get Alpha Vantage API function name for an indicator type.

    Args:
        indicator_type: The indicator type from CycleRequest.

    Returns:
        Alpha Vantage API function name (uppercase).

    Raises:
        ValueError: If indicator_type is not recognized.

    Examples:
        >>> get_api_function_name("ht_trendline")
        'HT_TRENDLINE'
        >>> get_api_function_name("ht_dcperiod")
        'HT_DCPERIOD'
    """
    if indicator_type not in INDICATOR_TYPE_TO_FUNCTION:
        valid_types = ", ".join(INDICATOR_TYPE_TO_FUNCTION.keys())
        raise ValueError(f"Unknown indicator_type '{indicator_type}'. Valid options: {valid_types}")

    return INDICATOR_TYPE_TO_FUNCTION[indicator_type]


def transform_request_params(request: CycleRequest) -> dict[str, Any]:
    """
    Transform CycleRequest into Alpha Vantage API parameters.

    This function:
    1. Extracts parameters needed for Hilbert Transform indicators
    2. All cycle indicators use the same parameters: symbol, interval, series_type

    Args:
        request: Validated CycleRequest instance.

    Returns:
        Dictionary of API parameters ready for _make_api_request.

    Examples:
        >>> request = CycleRequest(
        ...     indicator_type="ht_trendline",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     series_type="close"
        ... )
        >>> params = transform_request_params(request)
        >>> params["symbol"]
        'IBM'
        >>> params["series_type"]
        'close'
    """
    params: dict[str, Any] = {}

    # Common parameters (all cycle indicators use these)
    params["symbol"] = request.symbol
    params["interval"] = request.interval
    params["series_type"] = request.series_type
    params["datatype"] = request.datatype

    # Add optional month parameter (intraday only)
    if request.month and request.interval in ["1min", "5min", "15min", "30min", "60min"]:
        params["month"] = request.month

    return params


def get_output_decision_params(request: CycleRequest) -> dict[str, bool]:
    """
    Extract output decision parameters from request.

    These parameters control whether the output should be written to a file
    or returned inline, and can override the automatic decision made by
    the output helper.

    Args:
        request: CycleRequest instance.

    Returns:
        Dictionary with force_inline and force_file flags.

    Examples:
        >>> request = CycleRequest(
        ...     indicator_type="ht_dcperiod",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     series_type="close",
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


def validate_routing(request: CycleRequest) -> None:
    """
    Validate that the request can be properly routed.

    This is a final safety check before making the API call.
    Should not raise any errors if the CycleRequest validation
    worked correctly, but provides defense-in-depth.

    Args:
        request: CycleRequest instance.

    Raises:
        ValueError: If routing validation fails.

    Examples:
        >>> request = CycleRequest(
        ...     indicator_type="ht_trendline",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     series_type="close"
        ... )
        >>> validate_routing(request)  # No error
    """
    indicator_type = request.indicator_type

    # Verify we can route this indicator type
    if indicator_type not in INDICATOR_TYPE_TO_FUNCTION:
        raise ValueError(f"Cannot route indicator_type '{indicator_type}'")

    # All cycle indicators require series_type (already validated by Pydantic)
    if request.series_type is None:
        raise ValueError(f"Routing failed: {indicator_type} requires series_type parameter")


class RoutingError(Exception):
    """Exception raised when request routing fails."""

    pass


def route_request(request: CycleRequest) -> tuple[str, dict[str, Any]]:
    """
    Route a CycleRequest to the appropriate API function with parameters.

    This is the main entry point for the routing logic. It:
    1. Validates the request can be routed
    2. Gets the API function name
    3. Transforms the parameters

    Args:
        request: Validated CycleRequest instance.

    Returns:
        Tuple of (api_function_name, api_parameters).

    Raises:
        RoutingError: If routing fails for any reason.

    Examples:
        >>> request = CycleRequest(
        ...     indicator_type="ht_trendline",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     series_type="close"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'HT_TRENDLINE'
        >>> params["series_type"]
        'close'

        >>> request = CycleRequest(
        ...     indicator_type="ht_dcperiod",
        ...     symbol="AAPL",
        ...     interval="weekly",
        ...     series_type="high"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'HT_DCPERIOD'
        >>> params["series_type"]
        'high'
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
