"""
Unified cycle (Hilbert Transform) indicator tool for Alpha Vantage MCP server.

This module consolidates 6 separate Hilbert Transform indicator API endpoints into a single
GET_CYCLE_INDICATOR tool, reducing context window usage and simplifying the API.

Consolidates:
- HT_TRENDLINE (Hilbert Transform Instantaneous Trendline)
- HT_SINE (Hilbert Transform Sine Wave)
- HT_TRENDMODE (Hilbert Transform Trend vs Cycle Mode)
- HT_DCPERIOD (Hilbert Transform Dominant Cycle Period)
- HT_DCPHASE (Hilbert Transform Dominant Cycle Phase)
- HT_PHASOR (Hilbert Transform Phasor Components)
"""

import json

from pydantic import ValidationError

from src.common import _make_api_request
from src.tools.registry import tool

from .cycle_router import (
    RoutingError,
    route_request,
)
from .cycle_schema import CycleRequest


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
def get_cycle_indicator(
    indicator_type: str,
    symbol: str,
    interval: str,
    series_type: str,
    month: str | None = None,
    datatype: str = "csv",
    force_inline: bool = False,
    force_file: bool = False,
) -> dict | str:
    """
    Unified cycle (Hilbert Transform) indicator retrieval for all Alpha Vantage HT endpoints.

    This tool consolidates 6 separate Hilbert Transform indicator APIs into a single endpoint.
    All HT indicators analyze dominant cycle characteristics and trend vs cycle modes in
    price data using advanced signal processing techniques.

    Args:
        indicator_type: Type of Hilbert Transform indicator. Options:
            - 'ht_trendline': Instantaneous Trendline
            - 'ht_sine': Sine Wave
            - 'ht_trendmode': Trend vs Cycle Mode
            - 'ht_dcperiod': Dominant Cycle Period
            - 'ht_dcphase': Dominant Cycle Phase
            - 'ht_phasor': Phasor Components

        symbol: Stock ticker symbol (e.g., 'IBM', 'AAPL'). Required for all indicators.

        interval: Time interval between consecutive data points. Options:
            '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly'

        series_type: Price type to use for Hilbert Transform calculation.
            Options: 'close', 'open', 'high', 'low'
            Required for all HT indicators.

        month: Query specific month of intraday data in YYYY-MM format (e.g., '2009-01').
            Only applicable for intraday intervals (1min-60min).
            Supports months from 2000-01 onwards.

        datatype: Output format. Options: 'json', 'csv'. Default: 'csv'.

        force_inline: Force inline output regardless of size (default: False).
            Overrides automatic file/inline decision.

        force_file: Force file output regardless of size (default: False).
            Overrides automatic file/inline decision.

    Returns:
        Hilbert Transform indicator data in requested format (dict for JSON, str for CSV).
        For large responses, may return a file reference instead of inline data.

    Raises:
        ValidationError: If request parameters are invalid for the specified indicator_type.
        RoutingError: If request cannot be routed to an API endpoint.

    Examples:
        # Get Hilbert Transform Trendline for IBM
        >>> result = get_cycle_indicator(
        ...     indicator_type="ht_trendline",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     series_type="close"
        ... )

        # Get Dominant Cycle Period for Apple
        >>> result = get_cycle_indicator(
        ...     indicator_type="ht_dcperiod",
        ...     symbol="AAPL",
        ...     interval="weekly",
        ...     series_type="close"
        ... )

        # Get Sine Wave with high prices for Microsoft
        >>> result = get_cycle_indicator(
        ...     indicator_type="ht_sine",
        ...     symbol="MSFT",
        ...     interval="daily",
        ...     series_type="high"
        ... )

        # Get Trend vs Cycle Mode for Google
        >>> result = get_cycle_indicator(
        ...     indicator_type="ht_trendmode",
        ...     symbol="GOOGL",
        ...     interval="daily",
        ...     series_type="close"
        ... )

        # Get Phasor Components with intraday data
        >>> result = get_cycle_indicator(
        ...     indicator_type="ht_phasor",
        ...     symbol="TSLA",
        ...     interval="15min",
        ...     series_type="close",
        ...     month="2024-01"
        ... )

        # Get Dominant Cycle Phase
        >>> result = get_cycle_indicator(
        ...     indicator_type="ht_dcphase",
        ...     symbol="NVDA",
        ...     interval="daily",
        ...     series_type="close"
        ... )

    Context Window Reduction:
        This single tool replaces 6 individual tools, significantly reducing the
        context window required for tool definitions. Estimated savings: ~3600 tokens.

    Parameter Requirements:
        All Hilbert Transform indicators require:
            - symbol: Stock ticker
            - interval: Time interval
            - series_type: Price type (close, open, high, low)

        Optional for all:
            - month: Intraday month filter (YYYY-MM format)
            - datatype: Output format (json or csv)

    Technical Background:
        Hilbert Transform indicators use digital signal processing to identify
        dominant cycles and trends in price data. They're particularly useful for:
        - Identifying market cycles
        - Distinguishing trending vs cycling markets
        - Determining cycle phase and period
        - Generating leading indicators
    """
    # Collect all input parameters
    request_data = {
        "indicator_type": indicator_type,
        "symbol": symbol,
        "interval": interval,
        "series_type": series_type,
        "month": month,
        "datatype": datatype,
        "force_inline": force_inline,
        "force_file": force_file,
    }

    try:
        # Step 1: Validate and parse request using Pydantic schema
        request = CycleRequest(**request_data)

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
