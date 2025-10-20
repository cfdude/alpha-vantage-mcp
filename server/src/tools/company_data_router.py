"""
Routing logic for unified company data tool.

This module maps data_type values to Alpha Vantage API function names
and transforms request parameters into API-compatible format.
"""

from typing import Any

from .company_data_schema import CompanyDataRequest

# Mapping of data_type to Alpha Vantage API function names
DATA_TYPE_TO_FUNCTION = {
    "company_overview": "OVERVIEW",
    "etf_profile": "ETF_PROFILE",
    "dividends": "DIVIDENDS",
    "splits": "SPLITS",
    "earnings": "EARNINGS",
}


def get_api_function_name(data_type: str) -> str:
    """
    Get Alpha Vantage API function name for a data type.

    Args:
        data_type: The data type from CompanyDataRequest.

    Returns:
        Alpha Vantage API function name (uppercase).

    Raises:
        ValueError: If data_type is not recognized.

    Examples:
        >>> get_api_function_name("company_overview")
        'OVERVIEW'
        >>> get_api_function_name("etf_profile")
        'ETF_PROFILE'
        >>> get_api_function_name("dividends")
        'DIVIDENDS'
        >>> get_api_function_name("splits")
        'SPLITS'
        >>> get_api_function_name("earnings")
        'EARNINGS'
    """
    if data_type not in DATA_TYPE_TO_FUNCTION:
        valid_types = ", ".join(DATA_TYPE_TO_FUNCTION.keys())
        raise ValueError(f"Unknown data_type '{data_type}'. Valid options: {valid_types}")

    return DATA_TYPE_TO_FUNCTION[data_type]


def transform_request_params(request: CompanyDataRequest) -> dict[str, Any]:
    """
    Transform CompanyDataRequest into Alpha Vantage API parameters.

    This function:
    1. Extracts the parameters needed for the specific data_type
    2. Includes datatype parameter only for dividends and splits
    3. Always includes symbol parameter

    Args:
        request: Validated CompanyDataRequest instance.

    Returns:
        Dictionary of API parameters ready for _make_api_request.

    Examples:
        >>> # Company overview (no datatype parameter)
        >>> request = CompanyDataRequest(
        ...     data_type="company_overview",
        ...     symbol="IBM"
        ... )
        >>> params = transform_request_params(request)
        >>> params["symbol"]
        'IBM'
        >>> "datatype" in params
        False

        >>> # Dividends with datatype parameter
        >>> request = CompanyDataRequest(
        ...     data_type="dividends",
        ...     symbol="AAPL",
        ...     datatype="csv"
        ... )
        >>> params = transform_request_params(request)
        >>> params["symbol"]
        'AAPL'
        >>> params["datatype"]
        'csv'

        >>> # ETF profile (no datatype parameter)
        >>> request = CompanyDataRequest(
        ...     data_type="etf_profile",
        ...     symbol="QQQ"
        ... )
        >>> params = transform_request_params(request)
        >>> "datatype" in params
        False
    """
    data_type = request.data_type
    params: dict[str, Any] = {}

    # All data types require symbol
    params["symbol"] = request.symbol

    # Only dividends and splits support datatype parameter
    if data_type in ["dividends", "splits"]:
        params["datatype"] = request.datatype

    # company_overview, etf_profile, and earnings always return JSON
    # (they don't support datatype parameter)

    return params


def get_output_decision_params(request: CompanyDataRequest) -> dict[str, bool]:
    """
    Extract output decision parameters from request.

    These parameters control whether the output should be written to a file
    or returned inline, and can override the automatic decision made by
    the output helper.

    Args:
        request: CompanyDataRequest instance.

    Returns:
        Dictionary with force_inline and force_file flags.

    Examples:
        >>> request = CompanyDataRequest(
        ...     data_type="company_overview",
        ...     symbol="IBM",
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


def validate_routing(request: CompanyDataRequest) -> None:
    """
    Validate that the request can be properly routed.

    This is a final safety check before making the API call.
    Should not raise any errors if the CompanyDataRequest validation
    worked correctly, but provides defense-in-depth.

    Args:
        request: CompanyDataRequest instance.

    Raises:
        ValueError: If routing validation fails.

    Examples:
        >>> request = CompanyDataRequest(
        ...     data_type="company_overview",
        ...     symbol="IBM"
        ... )
        >>> validate_routing(request)  # No error
    """
    data_type = request.data_type

    # Verify we can route this data type
    if data_type not in DATA_TYPE_TO_FUNCTION:
        raise ValueError(f"Cannot route data_type '{data_type}'")

    # Verify symbol is provided (should be caught by Pydantic, but double-check)
    if not request.symbol or not isinstance(request.symbol, str):
        raise ValueError("Routing failed: symbol must be a non-empty string")


class RoutingError(Exception):
    """Exception raised when request routing fails."""

    pass


def route_request(request: CompanyDataRequest) -> tuple[str, dict[str, Any]]:
    """
    Route a CompanyDataRequest to the appropriate API function with parameters.

    This is the main entry point for the routing logic. It:
    1. Validates the request can be routed
    2. Gets the API function name
    3. Transforms the parameters

    Args:
        request: Validated CompanyDataRequest instance.

    Returns:
        Tuple of (api_function_name, api_parameters).

    Raises:
        RoutingError: If routing fails for any reason.

    Examples:
        >>> request = CompanyDataRequest(
        ...     data_type="company_overview",
        ...     symbol="AAPL"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'OVERVIEW'
        >>> params["symbol"]
        'AAPL'

        >>> request = CompanyDataRequest(
        ...     data_type="dividends",
        ...     symbol="IBM",
        ...     datatype="csv"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'DIVIDENDS'
        >>> params["datatype"]
        'csv'

        >>> request = CompanyDataRequest(
        ...     data_type="earnings",
        ...     symbol="MSFT"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'EARNINGS'
        >>> params["symbol"]
        'MSFT'
    """
    try:
        # Validate routing
        validate_routing(request)

        # Get API function name
        function_name = get_api_function_name(request.data_type)

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
