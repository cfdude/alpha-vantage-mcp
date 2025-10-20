"""
Routing logic for unified economic indicators tool.

This module maps indicator_type values to Alpha Vantage API function names
and transforms request parameters into API-compatible format.
"""

from typing import Any

from .economic_indicators_schema import EconomicIndicatorRequest

# Mapping of indicator_type to Alpha Vantage API function names
INDICATOR_TYPE_TO_FUNCTION = {
    "real_gdp": "REAL_GDP",
    "real_gdp_per_capita": "REAL_GDP_PER_CAPITA",
    "treasury_yield": "TREASURY_YIELD",
    "federal_funds_rate": "FEDERAL_FUNDS_RATE",
    "cpi": "CPI",
    "inflation": "INFLATION",
    "retail_sales": "RETAIL_SALES",
    "durables": "DURABLES",
    "unemployment": "UNEMPLOYMENT",
    "nonfarm_payroll": "NONFARM_PAYROLL",
}


def get_api_function_name(indicator_type: str) -> str:
    """
    Get Alpha Vantage API function name for an indicator type.

    Args:
        indicator_type: The indicator type from EconomicIndicatorRequest.

    Returns:
        Alpha Vantage API function name (uppercase).

    Raises:
        ValueError: If indicator_type is not recognized.

    Examples:
        >>> get_api_function_name("real_gdp")
        'REAL_GDP'
        >>> get_api_function_name("treasury_yield")
        'TREASURY_YIELD'
        >>> get_api_function_name("inflation")
        'INFLATION'
    """
    if indicator_type not in INDICATOR_TYPE_TO_FUNCTION:
        valid_types = ", ".join(INDICATOR_TYPE_TO_FUNCTION.keys())
        raise ValueError(f"Unknown indicator_type '{indicator_type}'. Valid options: {valid_types}")

    return INDICATOR_TYPE_TO_FUNCTION[indicator_type]


def transform_request_params(request: EconomicIndicatorRequest) -> dict[str, Any]:
    """
    Transform EconomicIndicatorRequest into Alpha Vantage API parameters.

    This function extracts the parameters needed for the API call based on
    indicator type. Different indicators require different parameters:

    - All indicators: datatype
    - Some indicators: interval (real_gdp, treasury_yield, federal_funds_rate, cpi)
    - treasury_yield only: maturity
    - Fixed interval indicators: datatype only

    Args:
        request: Validated EconomicIndicatorRequest instance.

    Returns:
        Dictionary of API parameters ready for _make_api_request.

    Examples:
        >>> # Real GDP with interval
        >>> request = EconomicIndicatorRequest(
        ...     indicator_type="real_gdp",
        ...     interval="quarterly"
        ... )
        >>> params = transform_request_params(request)
        >>> params["interval"]
        'quarterly'

        >>> # Treasury yield with interval and maturity
        >>> request = EconomicIndicatorRequest(
        ...     indicator_type="treasury_yield",
        ...     interval="monthly",
        ...     maturity="10year"
        ... )
        >>> params = transform_request_params(request)
        >>> params["interval"]
        'monthly'
        >>> params["maturity"]
        '10year'

        >>> # Fixed interval indicator (no interval parameter)
        >>> request = EconomicIndicatorRequest(
        ...     indicator_type="inflation"
        ... )
        >>> params = transform_request_params(request)
        >>> "interval" in params
        False
    """
    params: dict[str, Any] = {
        "datatype": request.datatype,
    }

    # Add interval if provided (validated by schema)
    if request.interval is not None:
        params["interval"] = request.interval

    # Add maturity if provided (only valid for treasury_yield)
    if request.maturity is not None:
        params["maturity"] = request.maturity

    return params


def get_output_decision_params(request: EconomicIndicatorRequest) -> dict[str, bool]:
    """
    Extract output decision parameters from request.

    These parameters control whether the output should be written to a file
    or returned inline, and can override the automatic decision made by
    the output helper.

    Args:
        request: EconomicIndicatorRequest instance.

    Returns:
        Dictionary with force_inline and force_file flags.

    Examples:
        >>> request = EconomicIndicatorRequest(
        ...     indicator_type="real_gdp",
        ...     interval="quarterly",
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


def validate_routing(request: EconomicIndicatorRequest) -> None:
    """
    Validate that the request can be properly routed.

    This is a final safety check before making the API call.
    Should not raise any errors if the EconomicIndicatorRequest validation
    worked correctly, but provides defense-in-depth.

    Args:
        request: EconomicIndicatorRequest instance.

    Raises:
        ValueError: If routing validation fails.

    Examples:
        >>> request = EconomicIndicatorRequest(
        ...     indicator_type="real_gdp",
        ...     interval="quarterly"
        ... )
        >>> validate_routing(request)  # No error

        >>> request = EconomicIndicatorRequest(
        ...     indicator_type="treasury_yield",
        ...     interval="monthly",
        ...     maturity="10year"
        ... )
        >>> validate_routing(request)  # No error
    """
    indicator_type = request.indicator_type

    # Verify we can route this indicator type
    if indicator_type not in INDICATOR_TYPE_TO_FUNCTION:
        raise ValueError(f"Cannot route indicator_type '{indicator_type}'")

    # Indicators requiring interval parameter
    REQUIRES_INTERVAL = ["real_gdp", "treasury_yield", "federal_funds_rate", "cpi"]

    if indicator_type in REQUIRES_INTERVAL:
        if request.interval is None:
            raise ValueError(f"Routing failed: {indicator_type} requires interval parameter")

    # treasury_yield requires maturity
    if indicator_type == "treasury_yield":
        if request.maturity is None:
            raise ValueError("Routing failed: treasury_yield requires maturity parameter")

    # Fixed interval indicators should not have interval
    FIXED_INTERVAL_INDICATORS = [
        "real_gdp_per_capita",
        "inflation",
        "retail_sales",
        "durables",
        "unemployment",
        "nonfarm_payroll",
    ]

    if indicator_type in FIXED_INTERVAL_INDICATORS:
        if request.interval is not None:
            raise ValueError(f"Routing failed: {indicator_type} does not accept interval parameter")


class RoutingError(Exception):
    """Exception raised when request routing fails."""

    pass


def route_request(request: EconomicIndicatorRequest) -> tuple[str, dict[str, Any]]:
    """
    Route an EconomicIndicatorRequest to the appropriate API function with parameters.

    This is the main entry point for the routing logic. It:
    1. Validates the request can be routed
    2. Gets the API function name
    3. Transforms the parameters

    Args:
        request: Validated EconomicIndicatorRequest instance.

    Returns:
        Tuple of (api_function_name, api_parameters).

    Raises:
        RoutingError: If routing fails for any reason.

    Examples:
        >>> # Real GDP
        >>> request = EconomicIndicatorRequest(
        ...     indicator_type="real_gdp",
        ...     interval="quarterly"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'REAL_GDP'
        >>> params["interval"]
        'quarterly'

        >>> # Treasury yield
        >>> request = EconomicIndicatorRequest(
        ...     indicator_type="treasury_yield",
        ...     interval="monthly",
        ...     maturity="10year"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'TREASURY_YIELD'
        >>> params["maturity"]
        '10year'

        >>> # Fixed interval indicator
        >>> request = EconomicIndicatorRequest(
        ...     indicator_type="inflation"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'INFLATION'
        >>> "interval" in params
        False

        >>> # Federal funds rate
        >>> request = EconomicIndicatorRequest(
        ...     indicator_type="federal_funds_rate",
        ...     interval="monthly"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'FEDERAL_FUNDS_RATE'
        >>> params["interval"]
        'monthly'
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
