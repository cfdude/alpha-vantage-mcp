"""
Unified materials commodity tool for Alpha Vantage MCP server.

This module consolidates 8 separate materials commodity API endpoints into a single
GET_MATERIALS_COMMODITY tool, reducing context window usage and simplifying the API.

Consolidates:
- COPPER (Global copper price index)
- ALUMINUM (Global aluminum price index)
- WHEAT (Global wheat price)
- CORN (Global corn price)
- COTTON (Global cotton price)
- SUGAR (Global sugar price)
- COFFEE (Global coffee price)
- ALL_COMMODITIES (Global price index of all commodities)
"""

import json

from pydantic import ValidationError

from src.common import _make_api_request
from src.tools.registry import tool

from .materials_commodity_router import (
    RoutingError,
    route_request,
)
from .materials_commodity_schema import MaterialsCommodityRequest


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
def get_materials_commodity(
    commodity_type: str,
    interval: str = "monthly",
    datatype: str = "csv",
    force_inline: bool = False,
    force_file: bool = False,
) -> dict | str:
    """
    Unified materials commodity price retrieval for metals, grains, and agricultural products.

    This tool consolidates 8 separate materials commodity APIs into a single endpoint with
    uniform parameter validation. It automatically handles large responses by using the
    output helper from Sprint 1.

    All materials commodities return time series price data in monthly, quarterly, or
    annual horizons.

    Args:
        commodity_type: Type of materials commodity to retrieve. Options:
            - 'copper': Global copper price index
            - 'aluminum': Global aluminum price index
            - 'wheat': Global wheat price
            - 'corn': Global corn price
            - 'cotton': Global cotton price
            - 'sugar': Global sugar price
            - 'coffee': Global coffee price
            - 'all_commodities': Global price index of all commodities

        interval: Time interval between data points (default: 'monthly'). Options:
            - 'monthly': Monthly prices
            - 'quarterly': Quarterly prices
            - 'annual': Annual prices
            All materials commodities support all three intervals.

        datatype: Response format (default: 'csv'). Options:
            - 'json': Returns data in JSON format
            - 'csv': Returns data as CSV (comma separated value) string

        force_inline: Force inline output regardless of size (default: False).
            Overrides automatic file/inline decision.

        force_file: Force file output regardless of size (default: False).
            Overrides automatic file/inline decision.

    Returns:
        Materials commodity price time series data in the specified format (JSON or CSV).
        For large responses, may return a file reference instead of inline data.

    Raises:
        ValidationError: If request parameters are invalid for the specified commodity_type.
        RoutingError: If request cannot be routed to an API endpoint.

    Examples:
        # Copper with monthly prices
        >>> result = get_materials_commodity(
        ...     commodity_type="copper",
        ...     interval="monthly"
        ... )

        # Wheat with quarterly prices
        >>> result = get_materials_commodity(
        ...     commodity_type="wheat",
        ...     interval="quarterly"
        ... )

        # All commodities index with annual prices
        >>> result = get_materials_commodity(
        ...     commodity_type="all_commodities",
        ...     interval="annual"
        ... )

        # Coffee with default monthly interval
        >>> result = get_materials_commodity(
        ...     commodity_type="coffee"
        ... )

        # Aluminum with JSON output
        >>> result = get_materials_commodity(
        ...     commodity_type="aluminum",
        ...     interval="quarterly",
        ...     datatype="json"
        ... )

        # Corn with quarterly prices
        >>> result = get_materials_commodity(
        ...     commodity_type="corn",
        ...     interval="quarterly"
        ... )

        # Cotton with annual prices
        >>> result = get_materials_commodity(
        ...     commodity_type="cotton",
        ...     interval="annual"
        ... )

        # Sugar with monthly prices
        >>> result = get_materials_commodity(
        ...     commodity_type="sugar",
        ...     interval="monthly"
        ... )

        # Force file output
        >>> result = get_materials_commodity(
        ...     commodity_type="copper",
        ...     interval="monthly",
        ...     force_file=True
        ... )

    Context Window Reduction:
        This single tool replaces 8 individual tools, reducing the context window
        required for tool definitions. Estimated savings: ~3,200 tokens.

    Data Coverage:
        - All commodities provide extensive historical data
        - Metals (copper, aluminum): Global price indices
        - Grains (wheat, corn): Global commodity prices
        - Agricultural (cotton, sugar, coffee): Global commodity prices
        - all_commodities: Comprehensive global commodity price index
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
        request = MaterialsCommodityRequest(**request_data)

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
