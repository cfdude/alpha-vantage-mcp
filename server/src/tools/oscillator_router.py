"""
Routing logic for unified oscillator/momentum indicator tool.

This module maps indicator_type values to Alpha Vantage API function names
and transforms request parameters into API-compatible format.
"""

from typing import Any

from .oscillator_schema import OscillatorRequest

# Mapping of indicator_type to Alpha Vantage API function names
INDICATOR_TYPE_TO_FUNCTION = {
    "macd": "MACD",
    "macdext": "MACDEXT",
    "stoch": "STOCH",
    "stochf": "STOCHF",
    "rsi": "RSI",
    "stochrsi": "STOCHRSI",
    "willr": "WILLR",
    "adx": "ADX",
    "adxr": "ADXR",
    "apo": "APO",
    "ppo": "PPO",
    "mom": "MOM",
    "bop": "BOP",
    "cci": "CCI",
    "cmo": "CMO",
    "roc": "ROC",
    "rocr": "ROCR",
}


def get_api_function_name(indicator_type: str) -> str:
    """
    Get Alpha Vantage API function name for an oscillator indicator type.

    Args:
        indicator_type: The indicator type from OscillatorRequest.

    Returns:
        Alpha Vantage API function name (uppercase).

    Raises:
        ValueError: If indicator_type is not recognized.

    Examples:
        >>> get_api_function_name("rsi")
        'RSI'
        >>> get_api_function_name("macd")
        'MACD'
        >>> get_api_function_name("stochrsi")
        'STOCHRSI'
    """
    if indicator_type not in INDICATOR_TYPE_TO_FUNCTION:
        valid_types = ", ".join(INDICATOR_TYPE_TO_FUNCTION.keys())
        raise ValueError(f"Unknown indicator_type '{indicator_type}'. Valid options: {valid_types}")

    return INDICATOR_TYPE_TO_FUNCTION[indicator_type]


def transform_request_params(request: OscillatorRequest) -> dict[str, Any]:
    """
    Transform OscillatorRequest into Alpha Vantage API parameters.

    This function:
    1. Extracts only the parameters needed for the specific indicator_type
    2. Handles default values for optional parameters (set in schema validation)
    3. Converts parameters to API-compatible format

    Args:
        request: Validated OscillatorRequest instance.

    Returns:
        Dictionary of API parameters ready for _make_api_request.

    Examples:
        >>> # RSI example (simple: time_period + series_type)
        >>> request = OscillatorRequest(
        ...     indicator_type="rsi",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=14,
        ...     series_type="close"
        ... )
        >>> params = transform_request_params(request)
        >>> params["time_period"]
        14
        >>> params["series_type"]
        'close'

        >>> # MACD example (fast/slow/signal periods)
        >>> request = OscillatorRequest(
        ...     indicator_type="macd",
        ...     symbol="AAPL",
        ...     interval="daily",
        ...     series_type="close"
        ... )
        >>> params = transform_request_params(request)
        >>> params["fastperiod"]
        12
        >>> params["slowperiod"]
        26
        >>> params["signalperiod"]
        9

        >>> # BOP example (no additional params)
        >>> request = OscillatorRequest(
        ...     indicator_type="bop",
        ...     symbol="GOOGL",
        ...     interval="daily"
        ... )
        >>> params = transform_request_params(request)
        >>> "time_period" in params
        False
        >>> "series_type" in params
        False
    """
    indicator_type = request.indicator_type
    params: dict[str, Any] = {}

    # Common parameters (all indicators need these)
    params["symbol"] = request.symbol
    params["interval"] = request.interval
    params["datatype"] = request.datatype

    # Group indicators by parameter requirements (matching schema validation)
    simple_period = ["willr", "adx", "adxr", "cci"]
    series_period = ["rsi", "mom", "cmo", "roc", "rocr"]
    macd_indicators = ["macd"]
    macdext_indicators = ["macdext"]
    apo_ppo_indicators = ["apo", "ppo"]
    stoch_indicators = ["stoch"]
    stochf_indicators = ["stochf"]
    stochrsi_indicators = ["stochrsi"]
    no_params = ["bop"]

    # ========== Group 1: Simple Period ==========
    if indicator_type in simple_period:
        params["time_period"] = request.time_period

    # ========== Group 2: Series + Period ==========
    elif indicator_type in series_period:
        params["time_period"] = request.time_period
        params["series_type"] = request.series_type

    # ========== Group 3: MACD ==========
    elif indicator_type in macd_indicators:
        params["series_type"] = request.series_type
        params["fastperiod"] = request.fastperiod
        params["slowperiod"] = request.slowperiod
        params["signalperiod"] = request.signalperiod

    # ========== Group 4: MACD Extended ==========
    elif indicator_type in macdext_indicators:
        params["series_type"] = request.series_type
        params["fastperiod"] = request.fastperiod
        params["slowperiod"] = request.slowperiod
        params["signalperiod"] = request.signalperiod
        params["fastmatype"] = request.fastmatype
        params["slowmatype"] = request.slowmatype
        params["signalmatype"] = request.signalmatype

    # ========== Group 5: APO/PPO ==========
    elif indicator_type in apo_ppo_indicators:
        params["series_type"] = request.series_type
        params["fastperiod"] = request.fastperiod
        params["slowperiod"] = request.slowperiod
        params["matype"] = request.matype

    # ========== Group 6: Stochastic ==========
    elif indicator_type in stoch_indicators:
        params["fastkperiod"] = request.fastkperiod
        params["slowkperiod"] = request.slowkperiod
        params["slowdperiod"] = request.slowdperiod
        params["slowkmatype"] = request.slowkmatype
        params["slowdmatype"] = request.slowdmatype

    # ========== Group 7: Stochastic Fast ==========
    elif indicator_type in stochf_indicators:
        params["fastkperiod"] = request.fastkperiod
        params["fastdperiod"] = request.fastdperiod
        params["fastdmatype"] = request.fastdmatype

    # ========== Group 8: Stochastic RSI ==========
    elif indicator_type in stochrsi_indicators:
        params["time_period"] = request.time_period
        params["series_type"] = request.series_type
        params["fastkperiod"] = request.fastkperiod
        params["fastdperiod"] = request.fastdperiod
        params["fastdmatype"] = request.fastdmatype

    # ========== Group 9: Balance of Power (no additional params) ==========
    elif indicator_type in no_params:
        # BOP only needs symbol, interval, datatype (already added above)
        pass

    # Add optional month parameter (intraday only)
    if request.month and request.interval in ["1min", "5min", "15min", "30min", "60min"]:
        params["month"] = request.month

    return params


def get_output_decision_params(request: OscillatorRequest) -> dict[str, bool]:
    """
    Extract output decision parameters from request.

    These parameters control whether the output should be written to a file
    or returned inline, and can override the automatic decision made by
    the output helper.

    Args:
        request: OscillatorRequest instance.

    Returns:
        Dictionary with force_inline and force_file flags.

    Examples:
        >>> request = OscillatorRequest(
        ...     indicator_type="rsi",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=14,
        ...     series_type="close",
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


def validate_routing(request: OscillatorRequest) -> None:
    """
    Validate that the request can be properly routed.

    This is a final safety check before making the API call.
    Should not raise any errors if the OscillatorRequest validation
    worked correctly, but provides defense-in-depth.

    Args:
        request: OscillatorRequest instance.

    Raises:
        ValueError: If routing validation fails.

    Examples:
        >>> request = OscillatorRequest(
        ...     indicator_type="rsi",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=14,
        ...     series_type="close"
        ... )
        >>> validate_routing(request)  # No error
    """
    indicator_type = request.indicator_type

    # Verify we can route this indicator type
    if indicator_type not in INDICATOR_TYPE_TO_FUNCTION:
        raise ValueError(f"Cannot route indicator_type '{indicator_type}'")

    # Define parameter groups (matching schema validation)
    simple_period = ["willr", "adx", "adxr", "cci"]
    series_period = ["rsi", "mom", "cmo", "roc", "rocr"]
    macd_indicators = ["macd"]
    macdext_indicators = ["macdext"]
    apo_ppo_indicators = ["apo", "ppo"]
    stoch_indicators = ["stoch"]
    stochf_indicators = ["stochf"]
    stochrsi_indicators = ["stochrsi"]
    no_params = ["bop"]

    # Validate based on group (these should already be caught by Pydantic, but double-check)
    if indicator_type in simple_period:
        if request.time_period is None:
            raise ValueError(f"Routing failed: {indicator_type} requires time_period parameter")

    elif indicator_type in series_period:
        if request.time_period is None:
            raise ValueError(f"Routing failed: {indicator_type} requires time_period parameter")
        if request.series_type is None:
            raise ValueError(f"Routing failed: {indicator_type} requires series_type parameter")

    elif indicator_type in macd_indicators:
        if request.series_type is None:
            raise ValueError("Routing failed: macd requires series_type parameter")
        # fastperiod, slowperiod, signalperiod should have defaults set by schema

    elif indicator_type in macdext_indicators:
        if request.series_type is None:
            raise ValueError("Routing failed: macdext requires series_type parameter")
        # All period and matype params should have defaults set by schema

    elif indicator_type in apo_ppo_indicators:
        if request.series_type is None:
            raise ValueError(f"Routing failed: {indicator_type} requires series_type parameter")
        # fastperiod, slowperiod, matype should have defaults set by schema

    elif indicator_type in stoch_indicators:
        # All stoch params should have defaults set by schema
        pass

    elif indicator_type in stochf_indicators:
        # All stochf params should have defaults set by schema
        pass

    elif indicator_type in stochrsi_indicators:
        if request.time_period is None:
            raise ValueError("Routing failed: stochrsi requires time_period parameter")
        if request.series_type is None:
            raise ValueError("Routing failed: stochrsi requires series_type parameter")
        # Stochastic params should have defaults set by schema

    elif indicator_type in no_params:
        # BOP requires no additional params
        pass


class RoutingError(Exception):
    """Exception raised when request routing fails."""

    pass


def route_request(request: OscillatorRequest) -> tuple[str, dict[str, Any]]:
    """
    Route an OscillatorRequest to the appropriate API function with parameters.

    This is the main entry point for the routing logic. It:
    1. Validates the request can be routed
    2. Gets the API function name
    3. Transforms the parameters

    Args:
        request: Validated OscillatorRequest instance.

    Returns:
        Tuple of (api_function_name, api_parameters).

    Raises:
        RoutingError: If routing fails for any reason.

    Examples:
        >>> # RSI example
        >>> request = OscillatorRequest(
        ...     indicator_type="rsi",
        ...     symbol="IBM",
        ...     interval="daily",
        ...     time_period=14,
        ...     series_type="close"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'RSI'
        >>> params["time_period"]
        14

        >>> # MACD example
        >>> request = OscillatorRequest(
        ...     indicator_type="macd",
        ...     symbol="AAPL",
        ...     interval="daily",
        ...     series_type="close"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'MACD'
        >>> params["fastperiod"]
        12

        >>> # BOP example (no params)
        >>> request = OscillatorRequest(
        ...     indicator_type="bop",
        ...     symbol="GOOGL",
        ...     interval="daily"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'BOP'
        >>> "time_period" in params
        False
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
