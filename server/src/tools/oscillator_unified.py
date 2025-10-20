"""
Unified oscillator/momentum indicator tool for Alpha Vantage MCP server.

This module consolidates 17 separate oscillator and momentum indicator API endpoints into a single
GET_OSCILLATOR tool, reducing context window usage and simplifying the API.

Consolidates:
- MACD (Moving Average Convergence Divergence)
- MACDEXT (MACD with Controllable MA Type)
- STOCH (Stochastic Oscillator)
- STOCHF (Stochastic Fast)
- RSI (Relative Strength Index)
- STOCHRSI (Stochastic RSI)
- WILLR (Williams' %R)
- ADX (Average Directional Index)
- ADXR (ADX Rating)
- APO (Absolute Price Oscillator)
- PPO (Percentage Price Oscillator)
- MOM (Momentum)
- BOP (Balance of Power)
- CCI (Commodity Channel Index)
- CMO (Chande Momentum Oscillator)
- ROC (Rate of Change)
- ROCR (Rate of Change Ratio)
"""

import json

from pydantic import ValidationError

from src.common import _make_api_request
from src.tools.registry import tool

from .oscillator_router import (
    RoutingError,
    route_request,
)
from .oscillator_schema import OscillatorRequest


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
def get_oscillator(
    indicator_type: str,
    symbol: str,
    interval: str,
    time_period: int | None = None,
    series_type: str | None = None,
    fastperiod: int | None = None,
    slowperiod: int | None = None,
    signalperiod: int | None = None,
    fastkperiod: int | None = None,
    slowkperiod: int | None = None,
    slowdperiod: int | None = None,
    fastdperiod: int | None = None,
    matype: int | None = None,
    fastmatype: int | None = None,
    slowmatype: int | None = None,
    signalmatype: int | None = None,
    slowkmatype: int | None = None,
    slowdmatype: int | None = None,
    fastdmatype: int | None = None,
    month: str | None = None,
    datatype: str = "csv",
    force_inline: bool = False,
    force_file: bool = False,
) -> dict | str:
    """
    Unified oscillator/momentum indicator retrieval for all Alpha Vantage oscillator endpoints.

    This tool consolidates 17 separate oscillator and momentum indicator APIs into a single endpoint
    with conditional parameter validation based on indicator_type. It automatically handles large
    responses by using the output helper from Sprint 1.

    Args:
        indicator_type: Type of oscillator/momentum indicator. Options:
            - 'macd': Moving Average Convergence Divergence
            - 'macdext': MACD with Controllable MA Type
            - 'stoch': Stochastic Oscillator
            - 'stochf': Stochastic Fast
            - 'rsi': Relative Strength Index
            - 'stochrsi': Stochastic RSI
            - 'willr': Williams' %R
            - 'adx': Average Directional Index
            - 'adxr': ADX Rating
            - 'apo': Absolute Price Oscillator
            - 'ppo': Percentage Price Oscillator
            - 'mom': Momentum
            - 'bop': Balance of Power
            - 'cci': Commodity Channel Index
            - 'cmo': Chande Momentum Oscillator
            - 'roc': Rate of Change
            - 'rocr': Rate of Change Ratio

        symbol: Stock ticker symbol (e.g., 'IBM', 'AAPL'). Required for all indicators.

        interval: Time interval between consecutive data points. Options:
            '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly'

        time_period: Number of data points used to calculate each indicator value.
            Required for: rsi, willr, adx, adxr, cci, mom, cmo, roc, rocr, stochrsi
            Not used for: macd, macdext, stoch, stochf, apo, ppo, bop

        series_type: Price type to use for calculation. Options: 'close', 'open', 'high', 'low'
            Required for: macd, macdext, rsi, apo, ppo, mom, cmo, roc, rocr, stochrsi
            Not used for: stoch, stochf, willr, adx, adxr, bop, cci

        fastperiod: Fast period for moving average calculation (default: 12).
            Used with: macd, macdext, apo, ppo

        slowperiod: Slow period for moving average calculation (default: 26).
            Used with: macd, macdext, apo, ppo

        signalperiod: Signal period for MACD calculation (default: 9).
            Used with: macd, macdext

        fastkperiod: Fast K period for stochastic calculation (default: 5).
            Used with: stoch, stochf, stochrsi

        slowkperiod: Slow K period for stochastic calculation (default: 3).
            Used with: stoch

        slowdperiod: Slow D period for stochastic calculation (default: 3).
            Used with: stoch

        fastdperiod: Fast D period for stochastic calculation (default: 3).
            Used with: stochf, stochrsi

        matype: Moving average type (0=SMA, 1=EMA, 2=WMA, 3=DEMA, 4=TEMA, 5=TRIMA, 6=T3, 7=KAMA, 8=MAMA).
            Used with: apo, ppo (default: 0)

        fastmatype: Fast moving average type (default: 0).
            Used with: macdext, stochrsi

        slowmatype: Slow moving average type (default: 0).
            Used with: macdext

        signalmatype: Signal moving average type (default: 0).
            Used with: macdext

        slowkmatype: Slow K moving average type (default: 0).
            Used with: stoch

        slowdmatype: Slow D moving average type (default: 0).
            Used with: stoch

        fastdmatype: Fast D moving average type (default: 0).
            Used with: stochf, stochrsi

        month: Query specific month of intraday data in YYYY-MM format (e.g., '2009-01').
            Only applicable for intraday intervals (1min-60min).
            Supports months from 2000-01 onwards.

        datatype: Output format. Options: 'json', 'csv'. Default: 'csv'.

        force_inline: Force inline output regardless of size (default: False).
            Overrides automatic file/inline decision.

        force_file: Force file output regardless of size (default: False).
            Overrides automatic file/inline decision.

    Returns:
        Oscillator/momentum indicator data in requested format (dict for JSON, str for CSV).
        For large responses, may return a file reference instead of inline data.

    Raises:
        ValidationError: If request parameters are invalid for the specified indicator_type.
        RoutingError: If request cannot be routed to an API endpoint.

    Examples:
        # Get RSI (Relative Strength Index)
        >>> result = get_oscillator(
        ...     indicator_type="rsi",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=14,
        ...     series_type="close"
        ... )

        # Get MACD (Moving Average Convergence Divergence)
        >>> result = get_oscillator(
        ...     indicator_type="macd",
        ...     symbol="AAPL",
        ...     interval="daily",
        ...     series_type="close"
        ... )

        # Get Stochastic Oscillator
        >>> result = get_oscillator(
        ...     indicator_type="stoch",
        ...     symbol="MSFT",
        ...     interval="daily"
        ... )

        # Get Williams' %R
        >>> result = get_oscillator(
        ...     indicator_type="willr",
        ...     symbol="GOOGL",
        ...     interval="daily",
        ...     time_period=14
        ... )

        # Get Balance of Power (no additional params)
        >>> result = get_oscillator(
        ...     indicator_type="bop",
        ...     symbol="TSLA",
        ...     interval="daily"
        ... )

        # Get Stochastic RSI (combination indicator)
        >>> result = get_oscillator(
        ...     indicator_type="stochrsi",
        ...     symbol="NVDA",
        ...     interval="daily",
        ...     time_period=14,
        ...     series_type="close"
        ... )

        # Get intraday MACD for a specific month
        >>> result = get_oscillator(
        ...     indicator_type="macd",
        ...     symbol="AMZN",
        ...     interval="15min",
        ...     series_type="close",
        ...     month="2024-01"
        ... )

    Context Window Reduction:
        This single tool replaces 17 individual tools, significantly reducing the
        context window required for tool definitions. Estimated savings: ~10,000+ tokens.

    Parameter Requirements by Indicator Type:
        Simple Period (willr, adx, adxr, cci):
            Required: symbol, interval, time_period
            Optional: month (intraday only)

        Series + Period (rsi, mom, cmo, roc, rocr):
            Required: symbol, interval, time_period, series_type
            Optional: month (intraday only)

        MACD:
            Required: symbol, interval, series_type
            Optional: fastperiod (12), slowperiod (26), signalperiod (9), month

        MACD Extended:
            Required: symbol, interval, series_type
            Optional: fastperiod (12), slowperiod (26), signalperiod (9),
                     fastmatype (0), slowmatype (0), signalmatype (0), month

        APO/PPO:
            Required: symbol, interval, series_type
            Optional: fastperiod (12), slowperiod (26), matype (0), month

        Stochastic (stoch):
            Required: symbol, interval
            Optional: fastkperiod (5), slowkperiod (3), slowdperiod (3),
                     slowkmatype (0), slowdmatype (0), month

        Stochastic Fast (stochf):
            Required: symbol, interval
            Optional: fastkperiod (5), fastdperiod (3), fastdmatype (0), month

        Stochastic RSI (stochrsi):
            Required: symbol, interval, time_period, series_type
            Optional: fastkperiod (5), fastdperiod (3), fastdmatype (0), month

        Balance of Power (bop):
            Required: symbol, interval
            Optional: month (intraday only)
    """
    # Collect all input parameters
    request_data = {
        "indicator_type": indicator_type,
        "symbol": symbol,
        "interval": interval,
        "time_period": time_period,
        "series_type": series_type,
        "fastperiod": fastperiod,
        "slowperiod": slowperiod,
        "signalperiod": signalperiod,
        "fastkperiod": fastkperiod,
        "slowkperiod": slowkperiod,
        "slowdperiod": slowdperiod,
        "fastdperiod": fastdperiod,
        "matype": matype,
        "fastmatype": fastmatype,
        "slowmatype": slowmatype,
        "signalmatype": signalmatype,
        "slowkmatype": slowkmatype,
        "slowdmatype": slowdmatype,
        "fastdmatype": fastdmatype,
        "month": month,
        "datatype": datatype,
        "force_inline": force_inline,
        "force_file": force_file,
    }

    try:
        # Step 1: Validate and parse request using Pydantic schema
        request = OscillatorRequest(**request_data)

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
