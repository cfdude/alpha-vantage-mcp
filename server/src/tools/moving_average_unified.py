"""
Unified moving average tool for Alpha Vantage MCP server.

This module consolidates 10 separate moving average indicator API endpoints into a single
GET_MOVING_AVERAGE tool, reducing context window usage and simplifying the API.

Consolidates:
- SMA (Simple Moving Average)
- EMA (Exponential Moving Average)
- WMA (Weighted Moving Average)
- DEMA (Double Exponential Moving Average)
- TEMA (Triple Exponential Moving Average)
- TRIMA (Triangular Moving Average)
- KAMA (Kaufman Adaptive Moving Average)
- MAMA (MESA Adaptive Moving Average)
- T3 (Triple Exponential Moving Average T3)
- VWAP (Volume Weighted Average Price)
"""

import json

from pydantic import ValidationError

from src.common import _make_api_request
from src.tools.registry import tool

from .moving_average_router import (
    RoutingError,
    route_request,
)
from .moving_average_schema import MovingAverageRequest


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
def get_moving_average(
    indicator_type: str,
    symbol: str,
    interval: str,
    time_period: int | None = None,
    series_type: str | None = None,
    fastlimit: float | None = None,
    slowlimit: float | None = None,
    month: str | None = None,
    datatype: str = "csv",
    force_inline: bool = False,
    force_file: bool = False,
) -> dict | str:
    """
    Unified moving average indicator retrieval for all Alpha Vantage moving average endpoints.

    This tool consolidates 10 separate moving average APIs into a single endpoint with
    conditional parameter validation based on indicator_type. It automatically handles
    large responses by using the output helper from Sprint 1.

    Args:
        indicator_type: Type of moving average indicator. Options:
            - 'sma': Simple Moving Average
            - 'ema': Exponential Moving Average
            - 'wma': Weighted Moving Average
            - 'dema': Double Exponential Moving Average
            - 'tema': Triple Exponential Moving Average
            - 'trima': Triangular Moving Average
            - 'kama': Kaufman Adaptive Moving Average
            - 'mama': MESA Adaptive Moving Average
            - 't3': Triple Exponential Moving Average T3
            - 'vwap': Volume Weighted Average Price

        symbol: Stock ticker symbol (e.g., 'IBM', 'AAPL'). Required for all indicators.

        interval: Time interval between consecutive data points. Options:
            '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly'
            Note: VWAP only supports intraday intervals (1min-60min).

        time_period: Number of data points used to calculate each moving average value.
            Required for: sma, ema, wma, dema, tema, trima, kama, t3
            Not used for: mama, vwap
            Example: time_period=60 for a 60-period moving average

        series_type: Price type to use for calculation. Options: 'close', 'open', 'high', 'low'
            Required for: sma, ema, wma, dema, tema, trima, kama, mama, t3
            Not used for: vwap

        fastlimit: Fast limit for MAMA indicator (0.0-1.0, default: 0.01).
            Only used with indicator_type='mama'.

        slowlimit: Slow limit for MAMA indicator (0.0-1.0, default: 0.01).
            Only used with indicator_type='mama'.

        month: Query specific month of intraday data in YYYY-MM format (e.g., '2009-01').
            Only applicable for intraday intervals (1min-60min).
            Supports months from 2000-01 onwards.

        datatype: Output format. Options: 'json', 'csv'. Default: 'csv'.

        force_inline: Force inline output regardless of size (default: False).
            Overrides automatic file/inline decision.

        force_file: Force file output regardless of size (default: False).
            Overrides automatic file/inline decision.

    Returns:
        Moving average indicator data in requested format (dict for JSON, str for CSV).
        For large responses, may return a file reference instead of inline data.

    Raises:
        ValidationError: If request parameters are invalid for the specified indicator_type.
        RoutingError: If request cannot be routed to an API endpoint.

    Examples:
        # Get Simple Moving Average (SMA) for IBM
        >>> result = get_moving_average(
        ...     indicator_type="sma",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=60,
        ...     series_type="close"
        ... )

        # Get Exponential Moving Average (EMA) for Apple
        >>> result = get_moving_average(
        ...     indicator_type="ema",
        ...     symbol="AAPL",
        ...     interval="weekly",
        ...     time_period=200,
        ...     series_type="close"
        ... )

        # Get MESA Adaptive Moving Average (MAMA)
        >>> result = get_moving_average(
        ...     indicator_type="mama",
        ...     symbol="MSFT",
        ...     interval="daily",
        ...     series_type="close",
        ...     fastlimit=0.01,
        ...     slowlimit=0.01
        ... )

        # Get Volume Weighted Average Price (VWAP) - intraday only
        >>> result = get_moving_average(
        ...     indicator_type="vwap",
        ...     symbol="GOOGL",
        ...     interval="5min"
        ... )

        # Get intraday SMA for a specific month
        >>> result = get_moving_average(
        ...     indicator_type="sma",
        ...     symbol="TSLA",
        ...     interval="15min",
        ...     time_period=50,
        ...     series_type="close",
        ...     month="2024-01"
        ... )

    Context Window Reduction:
        This single tool replaces 10 individual tools, significantly reducing the
        context window required for tool definitions. Estimated savings: ~6000 tokens.

    Parameter Requirements by Indicator Type:
        Standard indicators (sma, ema, wma, dema, tema, trima, kama, t3):
            Required: symbol, interval, time_period, series_type
            Optional: month (intraday only)

        MAMA:
            Required: symbol, interval, series_type
            Optional: fastlimit, slowlimit (default: 0.01), month (intraday only)
            Note: Does NOT use time_period

        VWAP:
            Required: symbol, interval (must be intraday: 1min-60min)
            Optional: month
            Note: Does NOT use time_period or series_type
    """
    # Collect all input parameters
    request_data = {
        "indicator_type": indicator_type,
        "symbol": symbol,
        "interval": interval,
        "time_period": time_period,
        "series_type": series_type,
        "fastlimit": fastlimit,
        "slowlimit": slowlimit,
        "month": month,
        "datatype": datatype,
        "force_inline": force_inline,
        "force_file": force_file,
    }

    try:
        # Step 1: Validate and parse request using Pydantic schema
        request = MovingAverageRequest(**request_data)

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
