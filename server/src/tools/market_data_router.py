"""
Routing logic for unified market data tool.

This module maps request_type values to Alpha Vantage API function names
and transforms request parameters into API-compatible format.
"""

from typing import Any

from .market_data_schema import MarketDataRequest

# Mapping of request_type to Alpha Vantage API function names
REQUEST_TYPE_TO_FUNCTION = {
    "listing_status": "LISTING_STATUS",
    "earnings_calendar": "EARNINGS_CALENDAR",
    "ipo_calendar": "IPO_CALENDAR",
}


def get_api_function_name(request_type: str) -> str:
    """
    Get Alpha Vantage API function name for a request type.

    Args:
        request_type: The request type from MarketDataRequest.

    Returns:
        Alpha Vantage API function name (uppercase).

    Raises:
        ValueError: If request_type is not recognized.

    Examples:
        >>> get_api_function_name("listing_status")
        'LISTING_STATUS'
        >>> get_api_function_name("earnings_calendar")
        'EARNINGS_CALENDAR'
        >>> get_api_function_name("ipo_calendar")
        'IPO_CALENDAR'
    """
    if request_type not in REQUEST_TYPE_TO_FUNCTION:
        valid_types = ", ".join(REQUEST_TYPE_TO_FUNCTION.keys())
        raise ValueError(f"Unknown request_type '{request_type}'. Valid options: {valid_types}")

    return REQUEST_TYPE_TO_FUNCTION[request_type]


def transform_request_params(request: MarketDataRequest) -> dict[str, Any]:
    """
    Transform MarketDataRequest into Alpha Vantage API parameters.

    This function:
    1. Extracts only the parameters needed for the specific request_type
    2. Handles the different parameter patterns for each request type:
       - listing_status: date (optional), state (default: active)
       - earnings_calendar: symbol (optional), horizon (default: 3month)
       - ipo_calendar: no parameters

    Args:
        request: Validated MarketDataRequest instance.

    Returns:
        Dictionary of API parameters ready for _make_api_request.

    Examples:
        >>> # listing_status with defaults
        >>> request = MarketDataRequest(
        ...     request_type="listing_status"
        ... )
        >>> params = transform_request_params(request)
        >>> params["state"]
        'active'
        >>> "date" in params
        False

        >>> # listing_status with date
        >>> request = MarketDataRequest(
        ...     request_type="listing_status",
        ...     date="2020-01-15",
        ...     state="delisted"
        ... )
        >>> params = transform_request_params(request)
        >>> params["date"]
        '2020-01-15'
        >>> params["state"]
        'delisted'

        >>> # earnings_calendar with defaults
        >>> request = MarketDataRequest(
        ...     request_type="earnings_calendar"
        ... )
        >>> params = transform_request_params(request)
        >>> params["horizon"]
        '3month'
        >>> "symbol" in params
        False

        >>> # earnings_calendar with symbol
        >>> request = MarketDataRequest(
        ...     request_type="earnings_calendar",
        ...     symbol="IBM",
        ...     horizon="6month"
        ... )
        >>> params = transform_request_params(request)
        >>> params["symbol"]
        'IBM'
        >>> params["horizon"]
        '6month'

        >>> # ipo_calendar (no parameters)
        >>> request = MarketDataRequest(
        ...     request_type="ipo_calendar"
        ... )
        >>> params = transform_request_params(request)
        >>> params
        {}
    """
    request_type = request.request_type
    params: dict[str, Any] = {}

    if request_type == "listing_status":
        # Always include state parameter
        params["state"] = request.state

        # Include date only if provided
        if request.date is not None:
            params["date"] = request.date

    elif request_type == "earnings_calendar":
        # Always include horizon parameter
        params["horizon"] = request.horizon

        # Include symbol only if provided
        if request.symbol is not None:
            params["symbol"] = request.symbol

    elif request_type == "ipo_calendar":
        # No parameters for IPO calendar
        pass

    return params


def get_output_decision_params(request: MarketDataRequest) -> dict[str, bool]:
    """
    Extract output decision parameters from request.

    These parameters control whether the output should be written to a file
    or returned inline, and can override the automatic decision made by
    the output helper.

    Args:
        request: MarketDataRequest instance.

    Returns:
        Dictionary with force_inline and force_file flags.

    Examples:
        >>> request = MarketDataRequest(
        ...     request_type="listing_status",
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


def validate_routing(request: MarketDataRequest) -> None:
    """
    Validate that the request can be properly routed.

    This is a final safety check before making the API call.
    Should not raise any errors if the MarketDataRequest validation
    worked correctly, but provides defense-in-depth.

    Args:
        request: MarketDataRequest instance.

    Raises:
        ValueError: If routing validation fails.

    Examples:
        >>> request = MarketDataRequest(
        ...     request_type="listing_status"
        ... )
        >>> validate_routing(request)  # No error
    """
    request_type = request.request_type

    # Verify we can route this request type
    if request_type not in REQUEST_TYPE_TO_FUNCTION:
        raise ValueError(f"Cannot route request_type '{request_type}'")

    # Request-type-specific validation
    if request_type == "listing_status":
        # State must be valid
        if request.state not in ["active", "delisted"]:
            raise ValueError("Routing failed: state must be 'active' or 'delisted'")

    elif request_type == "earnings_calendar":
        # Horizon must be valid
        if request.horizon not in ["3month", "6month", "12month"]:
            raise ValueError("Routing failed: horizon must be '3month', '6month', or '12month'")


class RoutingError(Exception):
    """Exception raised when request routing fails."""

    pass


def route_request(request: MarketDataRequest) -> tuple[str, dict[str, Any]]:
    """
    Route a MarketDataRequest to the appropriate API function with parameters.

    This is the main entry point for the routing logic. It:
    1. Validates the request can be routed
    2. Gets the API function name
    3. Transforms the parameters

    Args:
        request: Validated MarketDataRequest instance.

    Returns:
        Tuple of (api_function_name, api_parameters).

    Raises:
        RoutingError: If routing fails for any reason.

    Examples:
        >>> request = MarketDataRequest(
        ...     request_type="listing_status"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'LISTING_STATUS'
        >>> params["state"]
        'active'

        >>> request = MarketDataRequest(
        ...     request_type="earnings_calendar",
        ...     symbol="IBM"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'EARNINGS_CALENDAR'
        >>> params["symbol"]
        'IBM'

        >>> request = MarketDataRequest(
        ...     request_type="ipo_calendar"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'IPO_CALENDAR'
        >>> params
        {}
    """
    try:
        # Validate routing
        validate_routing(request)

        # Get API function name
        function_name = get_api_function_name(request.request_type)

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
