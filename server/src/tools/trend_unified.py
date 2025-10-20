"""
Unified trend indicator tool for Alpha Vantage MCP server.

This module consolidates 7 separate trend indicator API endpoints into a single
GET_TREND_INDICATOR tool, reducing context window usage and simplifying the API.

Consolidates:
- AROON (Aroon indicator)
- AROONOSC (Aroon Oscillator)
- DX (Directional Movement Index)
- MINUS_DI (Minus Directional Indicator)
- PLUS_DI (Plus Directional Indicator)
- MINUS_DM (Minus Directional Movement)
- PLUS_DM (Plus Directional Movement)
"""

import json

from pydantic import ValidationError

from src.common import _make_api_request
from src.tools.registry import tool

from .trend_router import (
    RoutingError,
    route_request,
)
from .trend_schema import TrendRequest


def _create_error_response(error: Exception, request_data: dict) -> dict:
    """
    Create a standardized error response.

    Args:
        error: The exception that occurred.
        request_data: The original request data.

    Returns:
        Dictionary with error information.
    """
    if isinstance(error, ValidationError):
        # Pydantic validation error - extract field-specific errors
        errors = []
        for err in error.errors():
            field = " -> ".join(str(loc) for loc in err["loc"])
            message = err["msg"]
            errors.append(f"{field}: {message}")

        return {
            "error": "Request validation failed",
            "validation_errors": errors,
            "details": (
                "The request parameters do not meet the requirements for the specified indicator_type. "
                "Please check the parameter descriptions and try again."
            ),
            "request_data": request_data,
        }

    elif isinstance(error, RoutingError):
        # Routing error - problem with indicator_type or parameter routing
        return {
            "error": "Request routing failed",
            "message": str(error),
            "details": (
                "The request could not be routed to an API endpoint. "
                "This may indicate a configuration issue or unsupported indicator_type."
            ),
            "request_data": request_data,
        }

    else:
        # Generic error
        return {
            "error": type(error).__name__,
            "message": str(error),
            "details": "An unexpected error occurred while processing your request.",
            "request_data": request_data,
        }


@tool
def get_trend_indicator(
    indicator_type: str,
    symbol: str,
    interval: str,
    time_period: int,
    month: str | None = None,
    datatype: str = "csv",
    force_inline: bool = False,
    force_file: bool = False,
) -> dict | str:
    """
    Unified trend indicator retrieval for all Alpha Vantage trend endpoints.

    This tool consolidates 7 separate trend indicator APIs into a single endpoint with
    parameter validation. It handles directional movement indicators and Aroon indicators.

    Args:
        indicator_type: Type of trend indicator. Options:
            - 'aroon': Aroon indicator
            - 'aroonosc': Aroon Oscillator
            - 'dx': Directional Movement Index
            - 'minus_di': Minus Directional Indicator
            - 'plus_di': Plus Directional Indicator
            - 'minus_dm': Minus Directional Movement
            - 'plus_dm': Plus Directional Movement

        symbol: Stock ticker symbol (e.g., 'IBM', 'AAPL'). Required for all indicators.

        interval: Time interval between consecutive data points. Options:
            '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly'

        time_period: Number of data points used to calculate each indicator value.
            Example: time_period=14 for a 14-period Aroon

        month: Query specific month of intraday data in YYYY-MM format (e.g., '2009-01').
            Only applicable for intraday intervals (1min-60min).
            Supports months from 2000-01 onwards.

        datatype: Output format. Options: 'json', 'csv'. Default: 'csv'.

        force_inline: Force inline output regardless of size (default: False).
            Overrides automatic file/inline decision.

        force_file: Force file output regardless of size (default: False).
            Overrides automatic file/inline decision.

    Returns:
        Trend indicator data in requested format (dict for JSON, str for CSV).
        For large responses, may return a file reference instead of inline data.

    Raises:
        ValidationError: If request parameters are invalid for the specified indicator_type.
        RoutingError: If request cannot be routed to an API endpoint.

    Examples:
        # Get Aroon indicator for IBM
        >>> result = get_trend_indicator(
        ...     indicator_type="aroon",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=14
        ... )

        # Get Directional Movement Index (DX) for Apple
        >>> result = get_trend_indicator(
        ...     indicator_type="dx",
        ...     symbol="AAPL",
        ...     interval="weekly",
        ...     time_period=14
        ... )

        # Get Plus Directional Indicator with intraday data
        >>> result = get_trend_indicator(
        ...     indicator_type="plus_di",
        ...     symbol="MSFT",
        ...     interval="15min",
        ...     time_period=14,
        ...     month="2024-01"
        ... )

    Context Window Reduction:
        This single tool replaces 7 individual tools, significantly reducing the
        context window required for tool definitions. Estimated savings: ~4200 tokens.

    Parameter Requirements:
        All trend indicators require:
            - symbol: Stock ticker
            - interval: Time interval
            - time_period: Number of data points (positive integer)

        Optional for all:
            - month: Intraday month filter (YYYY-MM format)
            - datatype: Output format (json or csv)
    """
    # Collect all input parameters
    request_data = {
        "indicator_type": indicator_type,
        "symbol": symbol,
        "interval": interval,
        "time_period": time_period,
        "month": month,
        "datatype": datatype,
        "force_inline": force_inline,
        "force_file": force_file,
    }

    try:
        # Step 1: Validate and parse request using Pydantic schema
        request = TrendRequest(**request_data)

        # Step 2: Route request to appropriate API function
        function_name, api_params = route_request(request)

        # Step 3: Make API request with Sprint 1 integration
        # Pass force_inline and force_file to enable output helper system
        response = _make_api_request(
            function_name,
            api_params,
            force_inline=request.force_inline,
            force_file=request.force_file,
        )

        return response

    except ValidationError as e:
        # Validation failed - return structured error
        error_response = _create_error_response(e, request_data)
        return json.dumps(error_response, indent=2)

    except RoutingError as e:
        # Routing failed - return structured error
        error_response = _create_error_response(e, request_data)
        return json.dumps(error_response, indent=2)

    except Exception as e:
        # Unexpected error - return generic error
        error_response = _create_error_response(e, request_data)
        return json.dumps(error_response, indent=2)
