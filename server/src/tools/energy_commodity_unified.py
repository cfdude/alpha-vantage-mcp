"""
Unified energy commodity tool for Alpha Vantage MCP server.

This module consolidates 3 separate energy commodity API endpoints into a single
GET_ENERGY_COMMODITY tool, reducing context window usage and simplifying the API.

Consolidates:
- WTI (West Texas Intermediate crude oil)
- BRENT (Brent crude oil - Europe)
- NATURAL_GAS (Henry Hub natural gas spot prices)
"""

import json

from pydantic import ValidationError

from src.common import _make_api_request
from src.tools.registry import tool

from .energy_commodity_router import (
    RoutingError,
    route_request,
)
from .energy_commodity_schema import EnergyCommodityRequest


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
                "The request parameters do not meet the requirements for the specified commodity_type. "
                "Please check the parameter descriptions and try again."
            ),
            "request_data": request_data,
        }

    elif isinstance(error, RoutingError):
        # Routing error - problem with commodity_type or parameter routing
        return {
            "error": "Request routing failed",
            "message": str(error),
            "details": (
                "The request could not be routed to an API endpoint. "
                "This may indicate a configuration issue or unsupported commodity_type."
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
def get_energy_commodity(
    commodity_type: str,
    interval: str = "monthly",
    datatype: str = "csv",
    force_inline: bool = False,
    force_file: bool = False,
) -> dict | str:
    """
    Unified energy commodity price retrieval for WTI, Brent crude oil, and natural gas.

    This tool consolidates 3 separate energy commodity APIs into a single endpoint with
    uniform parameter validation. It automatically handles large responses by using the
    output helper from Sprint 1.

    All energy commodities return time series price data in daily, weekly, or monthly
    horizons.

    Args:
        commodity_type: Type of energy commodity to retrieve. Options:
            - 'wti': West Texas Intermediate crude oil prices
            - 'brent': Brent (Europe) crude oil prices
            - 'natural_gas': Henry Hub natural gas spot prices

        interval: Time interval between data points (default: 'monthly'). Options:
            - 'daily': Daily prices
            - 'weekly': Weekly prices
            - 'monthly': Monthly prices
            All energy commodities support all three intervals.

        datatype: Response format (default: 'csv'). Options:
            - 'json': Returns data in JSON format
            - 'csv': Returns data as CSV (comma separated value) string

        force_inline: Force inline output regardless of size (default: False).
            Overrides automatic file/inline decision.

        force_file: Force file output regardless of size (default: False).
            Overrides automatic file/inline decision.

    Returns:
        Energy commodity price time series data in the specified format (JSON or CSV).
        For large responses, may return a file reference instead of inline data.

    Raises:
        ValidationError: If request parameters are invalid for the specified commodity_type.
        RoutingError: If request cannot be routed to an API endpoint.

    Examples:
        # WTI crude oil with daily prices
        >>> result = get_energy_commodity(
        ...     commodity_type="wti",
        ...     interval="daily"
        ... )

        # Brent crude oil with weekly prices
        >>> result = get_energy_commodity(
        ...     commodity_type="brent",
        ...     interval="weekly"
        ... )

        # Natural gas with monthly prices (default)
        >>> result = get_energy_commodity(
        ...     commodity_type="natural_gas"
        ... )

        # WTI with JSON output
        >>> result = get_energy_commodity(
        ...     commodity_type="wti",
        ...     interval="monthly",
        ...     datatype="json"
        ... )

        # Force file output
        >>> result = get_energy_commodity(
        ...     commodity_type="brent",
        ...     interval="daily",
        ...     force_file=True
        ... )

    Context Window Reduction:
        This single tool replaces 3 individual tools, reducing the context window
        required for tool definitions. Estimated savings: ~1,200 tokens.

    Data Coverage:
        - All commodities provide extensive historical data
        - WTI and Brent: Daily, weekly, and monthly crude oil prices
        - Natural gas: Daily, weekly, and monthly spot prices
        - Data is updated regularly

    Output Control:
        - By default, output decision is made automatically based on response size
        - force_inline=True: Always return data inline (use with caution for large datasets)
        - force_file=True: Always save data to file
        - force_inline and force_file are mutually exclusive
    """
    # Collect all input parameters
    request_data = {
        "commodity_type": commodity_type,
        "interval": interval,
        "datatype": datatype,
        "force_inline": force_inline,
        "force_file": force_file,
    }

    try:
        # Step 1: Validate and parse request using Pydantic schema
        request = EnergyCommodityRequest(**request_data)

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
