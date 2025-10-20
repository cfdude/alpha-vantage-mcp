"""
Unified economic indicators tool for Alpha Vantage MCP server.

This module consolidates 10 separate economic indicator API endpoints into a single
GET_ECONOMIC_INDICATOR tool, reducing context window usage and simplifying the API.

Consolidates:
- REAL_GDP (Annual and quarterly Real GDP)
- REAL_GDP_PER_CAPITA (Quarterly Real GDP per capita)
- TREASURY_YIELD (Daily/weekly/monthly US treasury yields)
- FEDERAL_FUNDS_RATE (Daily/weekly/monthly federal funds rate)
- CPI (Monthly/semiannual Consumer Price Index)
- INFLATION (Annual inflation rates)
- RETAIL_SALES (Monthly retail sales data)
- DURABLES (Monthly durable goods orders)
- UNEMPLOYMENT (Monthly unemployment rate)
- NONFARM_PAYROLL (Monthly nonfarm payroll)
"""

import json

from pydantic import ValidationError

from src.common import _make_api_request
from src.tools.registry import tool

from .economic_indicators_router import (
    RoutingError,
    route_request,
)
from .economic_indicators_schema import EconomicIndicatorRequest


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
def get_economic_indicator(
    indicator_type: str,
    interval: str | None = None,
    maturity: str | None = None,
    datatype: str = "csv",
    force_inline: bool = False,
    force_file: bool = False,
) -> dict | str:
    """
    Unified economic indicator retrieval for all Alpha Vantage economic indicator endpoints.

    This tool consolidates 10 separate economic indicator APIs into a single endpoint with
    conditional parameter validation based on indicator_type. It automatically handles
    large responses by using the output helper from Sprint 1.

    All economic indicators return time series data for the United States covering
    multiple years of historical data.

    Args:
        indicator_type: Type of economic indicator to retrieve. Options:
            - 'real_gdp': Annual/quarterly Real GDP (requires interval: quarterly OR annual)
            - 'real_gdp_per_capita': Quarterly Real GDP per capita (no interval parameter)
            - 'treasury_yield': Daily/weekly/monthly US treasury yields
              (requires interval: daily/weekly/monthly AND maturity: 3month/2year/5year/7year/10year/30year)
            - 'federal_funds_rate': Daily/weekly/monthly federal funds rate
              (requires interval: daily/weekly/monthly)
            - 'cpi': Monthly/semiannual Consumer Price Index
              (requires interval: monthly OR semiannual)
            - 'inflation': Annual inflation rates (no interval parameter)
            - 'retail_sales': Monthly retail sales data (no interval parameter)
            - 'durables': Monthly durable goods orders (no interval parameter)
            - 'unemployment': Monthly unemployment rate (no interval parameter)
            - 'nonfarm_payroll': Monthly nonfarm payroll (no interval parameter)

        interval: Time interval between data points. Required for some indicators:
            - real_gdp: 'quarterly' OR 'annual'
            - treasury_yield: 'daily', 'weekly', OR 'monthly'
            - federal_funds_rate: 'daily', 'weekly', OR 'monthly'
            - cpi: 'monthly' OR 'semiannual'
            Not accepted for: real_gdp_per_capita, inflation, retail_sales,
            durables, unemployment, nonfarm_payroll (these use fixed intervals).

        maturity: Maturity timeline for treasury yields. Required only for treasury_yield.
            Options: '3month', '2year', '5year', '7year', '10year', '30year'.
            Not applicable to other indicators.

        datatype: Response format (default: 'csv'). Options:
            - 'json': Returns data in JSON format
            - 'csv': Returns data as CSV (comma separated value) string

        force_inline: Force inline output regardless of size (default: False).
            Overrides automatic file/inline decision.

        force_file: Force file output regardless of size (default: False).
            Overrides automatic file/inline decision.

    Returns:
        Economic indicator time series data in the specified format (JSON or CSV).
        For large responses, may return a file reference instead of inline data.

    Raises:
        ValidationError: If request parameters are invalid for the specified indicator_type.
        RoutingError: If request cannot be routed to an API endpoint.

    Examples:
        # Real GDP with quarterly interval
        >>> result = get_economic_indicator(
        ...     indicator_type="real_gdp",
        ...     interval="quarterly"
        ... )

        # Treasury yield with interval and maturity
        >>> result = get_economic_indicator(
        ...     indicator_type="treasury_yield",
        ...     interval="monthly",
        ...     maturity="10year"
        ... )

        # Federal funds rate with daily interval
        >>> result = get_economic_indicator(
        ...     indicator_type="federal_funds_rate",
        ...     interval="daily"
        ... )

        # CPI with semiannual interval
        >>> result = get_economic_indicator(
        ...     indicator_type="cpi",
        ...     interval="semiannual"
        ... )

        # Fixed interval indicator (no interval parameter)
        >>> result = get_economic_indicator(
        ...     indicator_type="inflation"
        ... )

        # Unemployment data
        >>> result = get_economic_indicator(
        ...     indicator_type="unemployment"
        ... )

        # Retail sales data
        >>> result = get_economic_indicator(
        ...     indicator_type="retail_sales"
        ... )

        # Force JSON output
        >>> result = get_economic_indicator(
        ...     indicator_type="real_gdp",
        ...     interval="annual",
        ...     datatype="json"
        ... )

    Context Window Reduction:
        This single tool replaces 10 individual tools, significantly reducing the
        context window required for tool definitions. Estimated savings: ~5,400 tokens.

    Parameter Requirements by Indicator Type:

        **Indicators Requiring interval Parameter**:
        - real_gdp: interval ∈ {quarterly, annual}
        - treasury_yield: interval ∈ {daily, weekly, monthly} + maturity ∈ {3month, 2year, 5year, 7year, 10year, 30year}
        - federal_funds_rate: interval ∈ {daily, weekly, monthly}
        - cpi: interval ∈ {monthly, semiannual}

        **Indicators with Fixed Intervals** (interval parameter NOT accepted):
        - real_gdp_per_capita: quarterly only
        - inflation: annual only
        - retail_sales: monthly only
        - durables: monthly only
        - unemployment: monthly only
        - nonfarm_payroll: monthly only

        **Special Cases**:
        - treasury_yield is the ONLY indicator requiring both interval AND maturity
        - maturity parameter is ONLY valid for treasury_yield

    Output Control:
        - By default, output decision is made automatically based on response size
        - force_inline=True: Always return data inline (use with caution for large datasets)
        - force_file=True: Always save data to file
        - force_inline and force_file are mutually exclusive

    Data Coverage:
        - Most indicators provide 20+ years of historical data
        - Data is updated regularly (frequency varies by indicator)
        - All data represents United States economic metrics
    """
    # Collect all input parameters
    request_data = {
        "indicator_type": indicator_type,
        "interval": interval,
        "maturity": maturity,
        "datatype": datatype,
        "force_inline": force_inline,
        "force_file": force_file,
    }

    try:
        # Step 1: Validate and parse request using Pydantic schema
        request = EconomicIndicatorRequest(**request_data)

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
