"""
Routing logic for unified time series tool.

This module maps series_type values to Alpha Vantage API function names
and transforms request parameters into API-compatible format.
"""

from typing import Any

from .time_series_schema import TimeSeriesRequest

# Mapping of series_type to Alpha Vantage API function names
SERIES_TYPE_TO_FUNCTION = {
    "intraday": "TIME_SERIES_INTRADAY",
    "daily": "TIME_SERIES_DAILY",
    "daily_adjusted": "TIME_SERIES_DAILY_ADJUSTED",
    "weekly": "TIME_SERIES_WEEKLY",
    "weekly_adjusted": "TIME_SERIES_WEEKLY_ADJUSTED",
    "monthly": "TIME_SERIES_MONTHLY",
    "monthly_adjusted": "TIME_SERIES_MONTHLY_ADJUSTED",
    "quote": "GLOBAL_QUOTE",
    "bulk_quotes": "REALTIME_BULK_QUOTES",
    "search": "SYMBOL_SEARCH",
    "market_status": "MARKET_STATUS",
}


def get_api_function_name(series_type: str) -> str:
    """
    Get Alpha Vantage API function name for a series type.

    Args:
        series_type: The series type from TimeSeriesRequest.

    Returns:
        Alpha Vantage API function name.

    Raises:
        ValueError: If series_type is not recognized.

    Examples:
        >>> get_api_function_name("intraday")
        'TIME_SERIES_INTRADAY'
        >>> get_api_function_name("daily_adjusted")
        'TIME_SERIES_DAILY_ADJUSTED'
        >>> get_api_function_name("market_status")
        'MARKET_STATUS'
    """
    if series_type not in SERIES_TYPE_TO_FUNCTION:
        valid_types = ", ".join(SERIES_TYPE_TO_FUNCTION.keys())
        raise ValueError(f"Unknown series_type '{series_type}'. Valid options: {valid_types}")

    return SERIES_TYPE_TO_FUNCTION[series_type]


def transform_request_params(request: TimeSeriesRequest) -> dict[str, Any]:
    """
    Transform TimeSeriesRequest into Alpha Vantage API parameters.

    This function:
    1. Extracts only the parameters needed for the specific series_type
    2. Converts parameter names to Alpha Vantage API format
    3. Handles special cases (e.g., bulk_quotes uses 'symbol' not 'symbols' in API)

    Args:
        request: Validated TimeSeriesRequest instance.

    Returns:
        Dictionary of API parameters ready for _make_api_request.

    Examples:
        >>> request = TimeSeriesRequest(
        ...     series_type="intraday",
        ...     symbol="IBM",
        ...     interval="5min",
        ...     outputsize="compact"
        ... )
        >>> params = transform_request_params(request)
        >>> params["symbol"]
        'IBM'
        >>> params["interval"]
        '5min'
        >>> params["adjusted"]
        'true'
    """
    series_type = request.series_type
    params: dict[str, Any] = {}

    # Common parameters (datatype always included)
    params["datatype"] = request.datatype

    # Series-type specific parameter extraction
    if series_type == "intraday":
        # Intraday requires: symbol, interval
        # Optional: adjusted, extended_hours, month, outputsize
        params["symbol"] = request.symbol
        params["interval"] = request.interval
        params["adjusted"] = str(request.adjusted).lower()
        params["extended_hours"] = str(request.extended_hours).lower()
        params["outputsize"] = request.outputsize

        if request.month:
            params["month"] = request.month

    elif series_type in ["daily", "daily_adjusted"]:
        # Daily requires: symbol
        # Optional: outputsize
        params["symbol"] = request.symbol
        params["outputsize"] = request.outputsize

    elif series_type in [
        "weekly",
        "weekly_adjusted",
        "monthly",
        "monthly_adjusted",
    ]:
        # Weekly/Monthly requires: symbol
        # No outputsize parameter (always full history)
        params["symbol"] = request.symbol

    elif series_type == "quote":
        # Quote requires: symbol
        params["symbol"] = request.symbol

    elif series_type == "bulk_quotes":
        # Bulk quotes requires: symbols (but API expects 'symbol' parameter)
        # IMPORTANT: Alpha Vantage API uses 'symbol' for both single and bulk quotes
        params["symbol"] = request.symbols

    elif series_type == "search":
        # Search requires: keywords
        params["keywords"] = request.keywords

    elif series_type == "market_status":
        # Market status has no required parameters
        pass

    # Add entitlement if provided (applies to all series types)
    if request.entitlement:
        params["entitlement"] = request.entitlement

    return params


def get_output_decision_params(request: TimeSeriesRequest) -> dict[str, bool]:
    """
    Extract output decision parameters from request.

    These parameters control whether the output should be written to a file
    or returned inline, and can override the automatic decision made by
    the output helper.

    Args:
        request: TimeSeriesRequest instance.

    Returns:
        Dictionary with force_inline and force_file flags.

    Examples:
        >>> request = TimeSeriesRequest(
        ...     series_type="daily",
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


def validate_routing(request: TimeSeriesRequest) -> None:
    """
    Validate that the request can be properly routed.

    This is a final safety check before making the API call.
    Should not raise any errors if the TimeSeriesRequest validation
    worked correctly, but provides defense-in-depth.

    Args:
        request: TimeSeriesRequest instance.

    Raises:
        ValueError: If routing validation fails.

    Examples:
        >>> request = TimeSeriesRequest(
        ...     series_type="intraday",
        ...     symbol="IBM",
        ...     interval="5min"
        ... )
        >>> validate_routing(request)  # No error
        >>> # This would fail in schema validation, but just to demonstrate:
        >>> # bad_request = TimeSeriesRequest(series_type="intraday", symbol="IBM")
        >>> # validate_routing(bad_request)  # Raises ValueError
    """
    series_type = request.series_type

    # Verify we can route this series type
    if series_type not in SERIES_TYPE_TO_FUNCTION:
        raise ValueError(f"Cannot route series_type '{series_type}'")

    # These validations should already be caught by Pydantic,
    # but we double-check for safety
    if series_type == "intraday" and not request.interval:
        raise ValueError("Routing failed: intraday requires interval parameter")

    if (
        series_type
        in [
            "intraday",
            "daily",
            "daily_adjusted",
            "weekly",
            "weekly_adjusted",
            "monthly",
            "monthly_adjusted",
            "quote",
        ]
        and not request.symbol
    ):
        raise ValueError(f"Routing failed: {series_type} requires symbol parameter")

    if series_type == "bulk_quotes" and not request.symbols:
        raise ValueError("Routing failed: bulk_quotes requires symbols parameter")

    if series_type == "search" and not request.keywords:
        raise ValueError("Routing failed: search requires keywords parameter")


class RoutingError(Exception):
    """Exception raised when request routing fails."""

    pass


def route_request(request: TimeSeriesRequest) -> tuple[str, dict[str, Any]]:
    """
    Route a TimeSeriesRequest to the appropriate API function with parameters.

    This is the main entry point for the routing logic. It:
    1. Validates the request can be routed
    2. Gets the API function name
    3. Transforms the parameters

    Args:
        request: Validated TimeSeriesRequest instance.

    Returns:
        Tuple of (api_function_name, api_parameters).

    Raises:
        RoutingError: If routing fails for any reason.

    Examples:
        >>> request = TimeSeriesRequest(
        ...     series_type="daily_adjusted",
        ...     symbol="AAPL",
        ...     outputsize="full"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'TIME_SERIES_DAILY_ADJUSTED'
        >>> params["symbol"]
        'AAPL'
        >>> params["outputsize"]
        'full'
    """
    try:
        # Validate routing
        validate_routing(request)

        # Get API function name
        function_name = get_api_function_name(request.series_type)

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
