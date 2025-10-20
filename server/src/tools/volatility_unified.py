"""
Unified volatility indicator tool for Alpha Vantage MCP server.

This module consolidates 7 separate volatility indicator API endpoints into a single
GET_VOLATILITY_INDICATOR tool, reducing context window usage and simplifying the API.

Consolidates:
- BBANDS (Bollinger Bands)
- TRANGE (True Range)
- ATR (Average True Range)
- NATR (Normalized Average True Range)
- MIDPOINT (Midpoint)
- MIDPRICE (Midpoint Price)
- SAR (Parabolic SAR)
"""

import json

from pydantic import ValidationError

from src.common import _make_api_request
from src.tools.registry import tool

from .volatility_router import (
    RoutingError,
    route_request,
)
from .volatility_schema import VolatilityRequest


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
def get_volatility_indicator(
    indicator_type: str,
    symbol: str,
    interval: str,
    time_period: int | None = None,
    series_type: str | None = None,
    nbdevup: int | None = None,
    nbdevdn: int | None = None,
    matype: int | None = None,
    acceleration: float | None = None,
    maximum: float | None = None,
    month: str | None = None,
    datatype: str = "csv",
    force_inline: bool = False,
    force_file: bool = False,
) -> dict | str:
    """
    Unified volatility indicator retrieval for all Alpha Vantage volatility endpoints.

    This tool consolidates 7 separate volatility indicator APIs into a single endpoint with
    conditional parameter validation based on indicator_type. Handles complex parameter
    patterns for Bollinger Bands, Parabolic SAR, and other volatility measures.

    Args:
        indicator_type: Type of volatility indicator. Options:
            - 'bbands': Bollinger Bands
            - 'trange': True Range
            - 'atr': Average True Range
            - 'natr': Normalized Average True Range
            - 'midpoint': Midpoint
            - 'midprice': Midpoint Price
            - 'sar': Parabolic SAR

        symbol: Stock ticker symbol (e.g., 'IBM', 'AAPL'). Required for all indicators.

        interval: Time interval between consecutive data points. Options:
            '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly'

        time_period: Number of data points used to calculate each indicator value.
            Required for: bbands, atr, natr, midpoint, midprice
            Not used for: trange, sar
            Example: time_period=20 for a 20-period Bollinger Band

        series_type: Price type to use for calculation. Options: 'close', 'open', 'high', 'low'
            Required for: bbands, midpoint
            Not used for: trange, atr, natr, midprice, sar

        nbdevup: Standard deviation multiplier for upper Bollinger Band (default: 2).
            Only used with indicator_type='bbands'.

        nbdevdn: Standard deviation multiplier for lower Bollinger Band (default: 2).
            Only used with indicator_type='bbands'.

        matype: Moving average type for Bollinger Bands (0-8, default: 0).
            0=SMA, 1=EMA, 2=WMA, 3=DEMA, 4=TEMA, 5=TRIMA, 6=T3, 7=KAMA, 8=MAMA.
            Only used with indicator_type='bbands'.

        acceleration: Acceleration factor for Parabolic SAR (0.0-1.0, default: 0.01).
            Only used with indicator_type='sar'.

        maximum: Maximum acceleration factor for Parabolic SAR (0.0-1.0, default: 0.20).
            Only used with indicator_type='sar'.

        month: Query specific month of intraday data in YYYY-MM format (e.g., '2009-01').
            Only applicable for intraday intervals (1min-60min).
            Supports months from 2000-01 onwards.

        datatype: Output format. Options: 'json', 'csv'. Default: 'csv'.

        force_inline: Force inline output regardless of size (default: False).
            Overrides automatic file/inline decision.

        force_file: Force file output regardless of size (default: False).
            Overrides automatic file/inline decision.

    Returns:
        Volatility indicator data in requested format (dict for JSON, str for CSV).
        For large responses, may return a file reference instead of inline data.

    Raises:
        ValidationError: If request parameters are invalid for the specified indicator_type.
        RoutingError: If request cannot be routed to an API endpoint.

    Examples:
        # Get Bollinger Bands for IBM
        >>> result = get_volatility_indicator(
        ...     indicator_type="bbands",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=20,
        ...     series_type="close",
        ...     nbdevup=2,
        ...     nbdevdn=2
        ... )

        # Get Average True Range (ATR) for Apple
        >>> result = get_volatility_indicator(
        ...     indicator_type="atr",
        ...     symbol="AAPL",
        ...     interval="daily",
        ...     time_period=14
        ... )

        # Get Parabolic SAR for Microsoft
        >>> result = get_volatility_indicator(
        ...     indicator_type="sar",
        ...     symbol="MSFT",
        ...     interval="daily",
        ...     acceleration=0.02,
        ...     maximum=0.20
        ... )

        # Get True Range (TRANGE) - no additional params
        >>> result = get_volatility_indicator(
        ...     indicator_type="trange",
        ...     symbol="GOOGL",
        ...     interval="daily"
        ... )

        # Get Midpoint with intraday data
        >>> result = get_volatility_indicator(
        ...     indicator_type="midpoint",
        ...     symbol="TSLA",
        ...     interval="15min",
        ...     time_period=14,
        ...     series_type="close",
        ...     month="2024-01"
        ... )

    Context Window Reduction:
        This single tool replaces 7 individual tools, significantly reducing the
        context window required for tool definitions. Estimated savings: ~4200 tokens.

    Parameter Requirements by Indicator Type:
        BBANDS (Bollinger Bands):
            Required: symbol, interval, time_period, series_type
            Optional: nbdevup (default: 2), nbdevdn (default: 2), matype (default: 0), month

        ATR, NATR, MIDPRICE:
            Required: symbol, interval, time_period
            Optional: month

        MIDPOINT:
            Required: symbol, interval, time_period, series_type
            Optional: month

        SAR (Parabolic SAR):
            Required: symbol, interval
            Optional: acceleration (default: 0.01), maximum (default: 0.20), month
            Note: Does NOT use time_period or series_type

        TRANGE (True Range):
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
        "series_type": series_type,
        "nbdevup": nbdevup,
        "nbdevdn": nbdevdn,
        "matype": matype,
        "acceleration": acceleration,
        "maximum": maximum,
        "month": month,
        "datatype": datatype,
        "force_inline": force_inline,
        "force_file": force_file,
    }

    try:
        # Step 1: Validate and parse request using Pydantic schema
        request = VolatilityRequest(**request_data)

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
