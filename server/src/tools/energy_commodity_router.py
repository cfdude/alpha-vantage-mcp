"""
Routing logic for unified energy commodity tool.

This module maps commodity_type values to Alpha Vantage API function names
and transforms request parameters into API-compatible format.
"""

from typing import Any

from .energy_commodity_schema import EnergyCommodityRequest

# Mapping of commodity_type to Alpha Vantage API function names
COMMODITY_TYPE_TO_FUNCTION = {
    "wti": "WTI",
    "brent": "BRENT",
    "natural_gas": "NATURAL_GAS",
}


def get_api_function_name(commodity_type: str) -> str:
    """
    Get Alpha Vantage API function name for a commodity type.

    Args:
        commodity_type: The commodity type from EnergyCommodityRequest.

    Returns:
        Alpha Vantage API function name (uppercase).

    Raises:
        ValueError: If commodity_type is not recognized.

    Examples:
        >>> get_api_function_name("wti")
        'WTI'
        >>> get_api_function_name("brent")
        'BRENT'
        >>> get_api_function_name("natural_gas")
        'NATURAL_GAS'
    """
    if commodity_type not in COMMODITY_TYPE_TO_FUNCTION:
        valid_types = ", ".join(COMMODITY_TYPE_TO_FUNCTION.keys())
        raise ValueError(f"Unknown commodity_type '{commodity_type}'. Valid options: {valid_types}")

    return COMMODITY_TYPE_TO_FUNCTION[commodity_type]


def transform_request_params(request: EnergyCommodityRequest) -> dict[str, Any]:
    """
    Transform EnergyCommodityRequest into Alpha Vantage API parameters.

    All energy commodities use the same parameters: interval and datatype.

    Args:
        request: Validated EnergyCommodityRequest instance.

    Returns:
        Dictionary of API parameters ready for _make_api_request.

    Examples:
        >>> # WTI with daily interval
        >>> request = EnergyCommodityRequest(
        ...     commodity_type="wti",
        ...     interval="daily"
        ... )
        >>> params = transform_request_params(request)
        >>> params["interval"]
        'daily'

        >>> # Brent with weekly interval
        >>> request = EnergyCommodityRequest(
        ...     commodity_type="brent",
        ...     interval="weekly"
        ... )
        >>> params = transform_request_params(request)
        >>> params["interval"]
        'weekly'

        >>> # Natural gas with default monthly interval
        >>> request = EnergyCommodityRequest(
        ...     commodity_type="natural_gas"
        ... )
        >>> params = transform_request_params(request)
        >>> params["interval"]
        'monthly'
    """
    params: dict[str, Any] = {
        "interval": request.interval,
        "datatype": request.datatype,
    }

    return params


def get_output_decision_params(request: EnergyCommodityRequest) -> dict[str, bool]:
    """
    Extract output decision parameters from request.

    These parameters control whether the output should be written to a file
    or returned inline, and can override the automatic decision made by
    the output helper.

    Args:
        request: EnergyCommodityRequest instance.

    Returns:
        Dictionary with force_inline and force_file flags.

    Examples:
        >>> request = EnergyCommodityRequest(
        ...     commodity_type="wti",
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


def validate_routing(request: EnergyCommodityRequest) -> None:
    """
    Validate that the request can be properly routed.

    This is a final safety check before making the API call.
    Should not raise any errors if the EnergyCommodityRequest validation
    worked correctly, but provides defense-in-depth.

    Args:
        request: EnergyCommodityRequest instance.

    Raises:
        ValueError: If routing validation fails.

    Examples:
        >>> request = EnergyCommodityRequest(
        ...     commodity_type="wti",
        ...     interval="daily"
        ... )
        >>> validate_routing(request)  # No error

        >>> request = EnergyCommodityRequest(
        ...     commodity_type="brent",
        ...     interval="weekly"
        ... )
        >>> validate_routing(request)  # No error
    """
    commodity_type = request.commodity_type

    # Verify we can route this commodity type
    if commodity_type not in COMMODITY_TYPE_TO_FUNCTION:
        raise ValueError(f"Cannot route commodity_type '{commodity_type}'")


class RoutingError(Exception):
    """Exception raised when request routing fails."""

    pass


def route_request(request: EnergyCommodityRequest) -> tuple[str, dict[str, Any]]:
    """
    Route an EnergyCommodityRequest to the appropriate API function with parameters.

    This is the main entry point for the routing logic. It:
    1. Validates the request can be routed
    2. Gets the API function name
    3. Transforms the parameters

    Args:
        request: Validated EnergyCommodityRequest instance.

    Returns:
        Tuple of (api_function_name, api_parameters).

    Raises:
        RoutingError: If routing fails for any reason.

    Examples:
        >>> # WTI with daily interval
        >>> request = EnergyCommodityRequest(
        ...     commodity_type="wti",
        ...     interval="daily"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'WTI'
        >>> params["interval"]
        'daily'

        >>> # Brent with weekly interval
        >>> request = EnergyCommodityRequest(
        ...     commodity_type="brent",
        ...     interval="weekly"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'BRENT'
        >>> params["interval"]
        'weekly'

        >>> # Natural gas with monthly interval
        >>> request = EnergyCommodityRequest(
        ...     commodity_type="natural_gas",
        ...     interval="monthly"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'NATURAL_GAS'
        >>> params["interval"]
        'monthly'
    """
    try:
        # Validate routing
        validate_routing(request)

        # Get API function name
        function_name = get_api_function_name(request.commodity_type)

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
