"""
Routing logic for unified volume indicator tool.

This module maps indicator_type values to Alpha Vantage API function names
and transforms request parameters into API-compatible format.
"""

from typing import Any

from .volume_schema import VolumeRequest

# Mapping of indicator_type to Alpha Vantage API function names
INDICATOR_TYPE_TO_FUNCTION = {
    "ad": "AD",
    "adosc": "ADOSC",
    "obv": "OBV",
    "mfi": "MFI",
}


def get_api_function_name(indicator_type: str) -> str:
    """
    Get Alpha Vantage API function name for an indicator type.

    Args:
        indicator_type: The indicator type from VolumeRequest.

    Returns:
        Alpha Vantage API function name (uppercase).

    Raises:
        ValueError: If indicator_type is not recognized.

    Examples:
        >>> get_api_function_name("mfi")
        'MFI'
        >>> get_api_function_name("adosc")
        'ADOSC'
    """
    if indicator_type not in INDICATOR_TYPE_TO_FUNCTION:
        valid_types = ", ".join(INDICATOR_TYPE_TO_FUNCTION.keys())
        raise ValueError(f"Unknown indicator_type '{indicator_type}'. Valid options: {valid_types}")

    return INDICATOR_TYPE_TO_FUNCTION[indicator_type]


def transform_request_params(request: VolumeRequest) -> dict[str, Any]:
    """
    Transform VolumeRequest into Alpha Vantage API parameters.

    This function:
    1. Extracts only the parameters needed for the specific indicator_type
    2. Handles different parameter patterns (MFI, ADOSC, AD/OBV)

    Args:
        request: Validated VolumeRequest instance.

    Returns:
        Dictionary of API parameters ready for _make_api_request.

    Examples:
        >>> # MFI
        >>> request = VolumeRequest(
        ...     indicator_type="mfi",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=14
        ... )
        >>> params = transform_request_params(request)
        >>> params["time_period"]
        14

        >>> # ADOSC
        >>> request = VolumeRequest(
        ...     indicator_type="adosc",
        ...     symbol="AAPL",
        ...     interval="daily"
        ... )
        >>> params = transform_request_params(request)
        >>> params["fastperiod"]
        3
        >>> params["slowperiod"]
        10

        >>> # AD (no params)
        >>> request = VolumeRequest(
        ...     indicator_type="ad",
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

    # MFI (time_period)
    if indicator_type == "mfi":
        params["time_period"] = request.time_period

    # ADOSC (fastperiod, slowperiod)
    elif indicator_type == "adosc":
        params["fastperiod"] = request.fastperiod
        params["slowperiod"] = request.slowperiod

    # AD, OBV (no additional params)
    # Already added symbol, interval, datatype above

    # Add optional month parameter (intraday only)
    if request.month and request.interval in ["1min", "5min", "15min", "30min", "60min"]:
        params["month"] = request.month

    return params


def get_output_decision_params(request: VolumeRequest) -> dict[str, bool]:
    """
    Extract output decision parameters from request.

    These parameters control whether the output should be written to a file
    or returned inline, and can override the automatic decision made by
    the output helper.

    Args:
        request: VolumeRequest instance.

    Returns:
        Dictionary with force_inline and force_file flags.

    Examples:
        >>> request = VolumeRequest(
        ...     indicator_type="mfi",
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


def validate_routing(request: VolumeRequest) -> None:
    """
    Validate that the request can be properly routed.

    This is a final safety check before making the API call.
    Should not raise any errors if the VolumeRequest validation
    worked correctly, but provides defense-in-depth.

    Args:
        request: VolumeRequest instance.

    Raises:
        ValueError: If routing validation fails.

    Examples:
        >>> request = VolumeRequest(
        ...     indicator_type="mfi",
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

    # Validate parameter presence (already validated by Pydantic, but double-check)
    if indicator_type == "mfi":
        if request.time_period is None:
            raise ValueError("Routing failed: mfi requires time_period")

    elif indicator_type == "adosc":
        if request.fastperiod is None or request.slowperiod is None:
            raise ValueError("Routing failed: adosc requires fastperiod and slowperiod")

    # AD and OBV have no additional params to validate


class RoutingError(Exception):
    """Exception raised when request routing fails."""

    pass


def route_request(request: VolumeRequest) -> tuple[str, dict[str, Any]]:
    """
    Route a VolumeRequest to the appropriate API function with parameters.

    This is the main entry point for the routing logic. It:
    1. Validates the request can be routed
    2. Gets the API function name
    3. Transforms the parameters

    Args:
        request: Validated VolumeRequest instance.

    Returns:
        Tuple of (api_function_name, api_parameters).

    Raises:
        RoutingError: If routing fails for any reason.

    Examples:
        >>> # MFI
        >>> request = VolumeRequest(
        ...     indicator_type="mfi",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=14
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'MFI'
        >>> params["time_period"]
        14

        >>> # ADOSC
        >>> request = VolumeRequest(
        ...     indicator_type="adosc",
        ...     symbol="AAPL",
        ...     interval="daily"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'ADOSC'
        >>> params["fastperiod"]
        3
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
