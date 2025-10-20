"""
Unified volume indicator tool for Alpha Vantage MCP server.

This module consolidates 4 separate volume indicator API endpoints into a single
GET_VOLUME_INDICATOR tool, reducing context window usage and simplifying the API.

Consolidates:
- AD (Chaikin A/D Line)
- ADOSC (Chaikin A/D Oscillator)
- OBV (On Balance Volume)
- MFI (Money Flow Index)
"""

import json

from pydantic import ValidationError

from src.common import _make_api_request
from src.tools.registry import tool

from .volume_router import (
    RoutingError,
    route_request,
)
from .volume_schema import VolumeRequest


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
def get_volume_indicator(
    indicator_type: str,
    symbol: str,
    interval: str,
    time_period: int | None = None,
    fastperiod: int | None = None,
    slowperiod: int | None = None,
    month: str | None = None,
    datatype: str = "csv",
    force_inline: bool = False,
    force_file: bool = False,
) -> dict | str:
    """
    Unified volume indicator retrieval for all Alpha Vantage volume endpoints.

    This tool consolidates 4 separate volume indicator APIs into a single endpoint with
    conditional parameter validation. Handles volume-based technical analysis including
    accumulation/distribution and money flow indicators.

    Args:
        indicator_type: Type of volume indicator. Options:
            - 'ad': Chaikin A/D Line
            - 'adosc': Chaikin A/D Oscillator
            - 'obv': On Balance Volume
            - 'mfi': Money Flow Index

        symbol: Stock ticker symbol (e.g., 'IBM', 'AAPL'). Required for all indicators.

        interval: Time interval between consecutive data points. Options:
            '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly'

        time_period: Number of data points used to calculate MFI.
            Required for: mfi
            Not used for: ad, adosc, obv
            Example: time_period=14 for a 14-period Money Flow Index

        fastperiod: Fast period for ADOSC EMA calculation (default: 3).
            Only used with indicator_type='adosc'.

        slowperiod: Slow period for ADOSC EMA calculation (default: 10).
            Only used with indicator_type='adosc'.

        month: Query specific month of intraday data in YYYY-MM format (e.g., '2009-01').
            Only applicable for intraday intervals (1min-60min).
            Supports months from 2000-01 onwards.

        datatype: Output format. Options: 'json', 'csv'. Default: 'csv'.

        force_inline: Force inline output regardless of size (default: False).
            Overrides automatic file/inline decision.

        force_file: Force file output regardless of size (default: False).
            Overrides automatic file/inline decision.

    Returns:
        Volume indicator data in requested format (dict for JSON, str for CSV).
        For large responses, may return a file reference instead of inline data.

    Raises:
        ValidationError: If request parameters are invalid for the specified indicator_type.
        RoutingError: If request cannot be routed to an API endpoint.

    Examples:
        # Get Money Flow Index (MFI) for IBM
        >>> result = get_volume_indicator(
        ...     indicator_type="mfi",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=14
        ... )

        # Get Chaikin A/D Oscillator for Apple
        >>> result = get_volume_indicator(
        ...     indicator_type="adosc",
        ...     symbol="AAPL",
        ...     interval="daily",
        ...     fastperiod=3,
        ...     slowperiod=10
        ... )

        # Get Chaikin A/D Line for Microsoft - no additional params
        >>> result = get_volume_indicator(
        ...     indicator_type="ad",
        ...     symbol="MSFT",
        ...     interval="daily"
        ... )

        # Get On Balance Volume (OBV) for Google - no additional params
        >>> result = get_volume_indicator(
        ...     indicator_type="obv",
        ...     symbol="GOOGL",
        ...     interval="daily"
        ... )

        # Get MFI with intraday data
        >>> result = get_volume_indicator(
        ...     indicator_type="mfi",
        ...     symbol="TSLA",
        ...     interval="15min",
        ...     time_period=14,
        ...     month="2024-01"
        ... )

    Context Window Reduction:
        This single tool replaces 4 individual tools, significantly reducing the
        context window required for tool definitions. Estimated savings: ~2400 tokens.

    Parameter Requirements by Indicator Type:
        MFI (Money Flow Index):
            Required: symbol, interval, time_period
            Optional: month (intraday only)

        ADOSC (Chaikin A/D Oscillator):
            Required: symbol, interval
            Optional: fastperiod (default: 3), slowperiod (default: 10), month

        AD (Chaikin A/D Line):
            Required: symbol, interval
            Optional: month
            Note: No additional parameters needed

        OBV (On Balance Volume):
            Required: symbol, interval
            Optional: month
            Note: No additional parameters needed
    """
    # Collect all input parameters
    request_data = {
        "indicator_type": indicator_type,
        "symbol": symbol,
        "interval": interval,
        "time_period": time_period,
        "fastperiod": fastperiod,
        "slowperiod": slowperiod,
        "month": month,
        "datatype": datatype,
        "force_inline": force_inline,
        "force_file": force_file,
    }

    try:
        # Step 1: Validate and parse request using Pydantic schema
        request = VolumeRequest(**request_data)

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
