"""
Routing logic for unified materials commodity tool.

This module maps commodity_type values to Alpha Vantage API function names
and transforms request parameters into API-compatible format.
"""

from typing import Any

from .materials_commodity_schema import MaterialsCommodityRequest

# Mapping of commodity_type to Alpha Vantage API function names
COMMODITY_TYPE_TO_FUNCTION = {
    "copper": "COPPER",
    "aluminum": "ALUMINUM",
    "wheat": "WHEAT",
    "corn": "CORN",
    "cotton": "COTTON",
    "sugar": "SUGAR",
    "coffee": "COFFEE",
    "all_commodities": "ALL_COMMODITIES",
}


def get_api_function_name(commodity_type: str) -> str:
    """
    Get Alpha Vantage API function name for a commodity type.

    Args:
        commodity_type: The commodity type from MaterialsCommodityRequest.

    Returns:
        Alpha Vantage API function name (uppercase).

    Raises:
        ValueError: If commodity_type is not recognized.

    Examples:
        >>> get_api_function_name("copper")
        'COPPER'
        >>> get_api_function_name("wheat")
        'WHEAT'
        >>> get_api_function_name("all_commodities")
        'ALL_COMMODITIES'
    """
    if commodity_type not in COMMODITY_TYPE_TO_FUNCTION:
        valid_types = ", ".join(COMMODITY_TYPE_TO_FUNCTION.keys())
        raise ValueError(f"Unknown commodity_type '{commodity_type}'. Valid options: {valid_types}")

    return COMMODITY_TYPE_TO_FUNCTION[commodity_type]


def transform_request_params(request: MaterialsCommodityRequest) -> dict[str, Any]:
    """
    Transform MaterialsCommodityRequest into Alpha Vantage API parameters.

    All materials commodities use the same parameters: interval and datatype.

    Args:
        request: Validated MaterialsCommodityRequest instance.

    Returns:
        Dictionary of API parameters ready for _make_api_request.

    Examples:
        >>> # Copper with monthly interval
        >>> request = MaterialsCommodityRequest(
        ...     commodity_type="copper",
        ...     interval="monthly"
        ... )
        >>> params = transform_request_params(request)
        >>> params["interval"]
        'monthly'

        >>> # Wheat with quarterly interval
        >>> request = MaterialsCommodityRequest(
        ...     commodity_type="wheat",
        ...     interval="quarterly"
        ... )
        >>> params = transform_request_params(request)
        >>> params["interval"]
        'quarterly'

        >>> # All commodities with annual interval
        >>> request = MaterialsCommodityRequest(
        ...     commodity_type="all_commodities",
        ...     interval="annual"
        ... )
        >>> params = transform_request_params(request)
        >>> params["interval"]
        'annual'
    """
    params: dict[str, Any] = {
        "interval": request.interval,
        "datatype": request.datatype,
    }

    return params


def get_output_decision_params(request: MaterialsCommodityRequest) -> dict[str, bool]:
    """
    Extract output decision parameters from request.

    These parameters control whether the output should be written to a file
    or returned inline, and can override the automatic decision made by
    the output helper.

    Args:
        request: MaterialsCommodityRequest instance.

    Returns:
        Dictionary with force_inline and force_file flags.

    Examples:
        >>> request = MaterialsCommodityRequest(
        ...     commodity_type="copper",
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


def validate_routing(request: MaterialsCommodityRequest) -> None:
    """
    Validate that the request can be properly routed.

    This is a final safety check before making the API call.
    Should not raise any errors if the MaterialsCommodityRequest validation
    worked correctly, but provides defense-in-depth.

    Args:
        request: MaterialsCommodityRequest instance.

    Raises:
        ValueError: If routing validation fails.

    Examples:
        >>> request = MaterialsCommodityRequest(
        ...     commodity_type="copper",
        ...     interval="monthly"
        ... )
        >>> validate_routing(request)  # No error

        >>> request = MaterialsCommodityRequest(
        ...     commodity_type="wheat",
        ...     interval="quarterly"
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


def route_request(request: MaterialsCommodityRequest) -> tuple[str, dict[str, Any]]:
    """
    Route a MaterialsCommodityRequest to the appropriate API function with parameters.

    This is the main entry point for the routing logic. It:
    1. Validates the request can be routed
    2. Gets the API function name
    3. Transforms the parameters

    Args:
        request: Validated MaterialsCommodityRequest instance.

    Returns:
        Tuple of (api_function_name, api_parameters).

    Raises:
        RoutingError: If routing fails for any reason.

    Examples:
        >>> # Copper with monthly interval
        >>> request = MaterialsCommodityRequest(
        ...     commodity_type="copper",
        ...     interval="monthly"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'COPPER'
        >>> params["interval"]
        'monthly'

        >>> # Wheat with quarterly interval
        >>> request = MaterialsCommodityRequest(
        ...     commodity_type="wheat",
        ...     interval="quarterly"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'WHEAT'
        >>> params["interval"]
        'quarterly'

        >>> # All commodities with annual interval
        >>> request = MaterialsCommodityRequest(
        ...     commodity_type="all_commodities",
        ...     interval="annual"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'ALL_COMMODITIES'
        >>> params["interval"]
        'annual'
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
