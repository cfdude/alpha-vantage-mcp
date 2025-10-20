"""
Unified company data tool for Alpha Vantage MCP server.

This module consolidates 5 separate company data API endpoints into a single
GET_COMPANY_DATA tool, reducing context window usage and simplifying the API.

Consolidates:
- COMPANY_OVERVIEW (Company information, ratios, and metrics)
- ETF_PROFILE (ETF holdings and sector/asset allocations)
- DIVIDENDS (Historical and future dividend distributions)
- SPLITS (Historical stock split events)
- EARNINGS (Annual and quarterly earnings with estimates)
"""

import json

from pydantic import ValidationError

from src.common import _make_api_request
from src.tools.registry import tool

from .company_data_router import (
    RoutingError,
    route_request,
)
from .company_data_schema import CompanyDataRequest


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
                "The request parameters do not meet the requirements for the specified data_type. "
                "Please check the parameter descriptions and try again."
            ),
            "request_data": request_data,
        }

    elif isinstance(error, RoutingError):
        # Routing error - problem with data_type or parameter routing
        return {
            "error": "Request routing failed",
            "message": str(error),
            "details": (
                "The request could not be routed to an API endpoint. "
                "This may indicate a configuration issue or unsupported data_type."
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
def get_company_data(
    data_type: str,
    symbol: str,
    datatype: str = "json",
    force_inline: bool = False,
    force_file: bool = False,
) -> dict | str:
    """
    Unified company data retrieval for all Alpha Vantage company data endpoints.

    This tool consolidates 5 separate company data APIs into a single endpoint with
    conditional parameter validation based on data_type. It automatically handles
    large responses by using the output helper from Sprint 1.

    Args:
        data_type: Type of company data to retrieve. Options:
            - 'company_overview': Company information, financial ratios, and key metrics
              (P/E ratio, market cap, dividend yield, etc.)
            - 'etf_profile': ETF holdings and allocations by asset types and sectors
              (net assets, expense ratio, turnover, top holdings)
            - 'dividends': Historical and future (declared) dividend distributions
            - 'splits': Historical stock split events
            - 'earnings': Annual and quarterly earnings (EPS) with analyst estimates
              and surprise metrics

        symbol: Stock or ETF ticker symbol (e.g., 'IBM', 'QQQ', 'AAPL'). Required for all data types.

        datatype: Output format. Options: 'json', 'csv'. Default: 'json'.
            Note: This parameter is only used for 'dividends' and 'splits'.
            'company_overview', 'etf_profile', and 'earnings' always return JSON.

        force_inline: Force inline output regardless of size (default: False).
            Overrides automatic file/inline decision.

        force_file: Force file output regardless of size (default: False).
            Overrides automatic file/inline decision.

    Returns:
        Company data in requested format (dict for JSON, str for CSV).
        For large responses, may return a file reference instead of inline data.

    Raises:
        ValidationError: If request parameters are invalid for the specified data_type.
        RoutingError: If request cannot be routed to an API endpoint.

    Examples:
        # Get company overview for IBM
        >>> result = get_company_data(
        ...     data_type="company_overview",
        ...     symbol="IBM"
        ... )

        # Get ETF profile for QQQ (Nasdaq 100 ETF)
        >>> result = get_company_data(
        ...     data_type="etf_profile",
        ...     symbol="QQQ"
        ... )

        # Get dividend history in CSV format
        >>> result = get_company_data(
        ...     data_type="dividends",
        ...     symbol="AAPL",
        ...     datatype="csv"
        ... )

        # Get stock split history in JSON format
        >>> result = get_company_data(
        ...     data_type="splits",
        ...     symbol="TSLA",
        ...     datatype="json"
        ... )

        # Get earnings data with analyst estimates
        >>> result = get_company_data(
        ...     data_type="earnings",
        ...     symbol="MSFT"
        ... )

        # Force file output for large dataset
        >>> result = get_company_data(
        ...     data_type="dividends",
        ...     symbol="IBM",
        ...     datatype="csv",
        ...     force_file=True
        ... )

    Context Window Reduction:
        This single tool replaces 5 individual tools, significantly reducing the
        context window required for tool definitions. Estimated savings: ~3,000 tokens.

    Data Structure by Type:
        company_overview:
            - Company information (name, description, sector, industry)
            - Financial metrics (market cap, P/E ratio, PEG ratio, book value)
            - Profitability ratios (profit margin, ROA, ROE)
            - Dividend information (dividend per share, yield, payout ratio)
            - Latest earnings date and fiscal year end

        etf_profile:
            - ETF information (name, description, inception date)
            - Key metrics (net assets, expense ratio, turnover ratio)
            - Asset allocation (equity, bond, cash percentages)
            - Sector allocation (technology, healthcare, financials, etc.)
            - Top 10 holdings with weights

        dividends:
            - Historical dividend payments with ex-dividend dates
            - Declared future dividends
            - Payment dates and amounts
            - Frequency information

        splits:
            - Historical stock split events
            - Split ratios and effective dates
            - Forward and reverse splits

        earnings:
            - Annual earnings (fiscal year, reported EPS)
            - Quarterly earnings (fiscal quarter, reported EPS, estimated EPS, surprise)
            - Analyst estimate data
            - Surprise percentage

    Parameter Requirements by Data Type:
        company_overview:
            Required: symbol
            Optional: None (always returns JSON)

        etf_profile:
            Required: symbol
            Optional: None (always returns JSON)

        dividends:
            Required: symbol
            Optional: datatype (json or csv)

        splits:
            Required: symbol
            Optional: datatype (json or csv)

        earnings:
            Required: symbol
            Optional: None (always returns JSON)

    Output Control:
        - By default, output decision is made automatically based on response size
        - force_inline=True: Always return data inline (use with caution for large datasets)
        - force_file=True: Always save data to file
        - force_inline and force_file are mutually exclusive
    """
    # Collect all input parameters
    request_data = {
        "data_type": data_type,
        "symbol": symbol,
        "datatype": datatype,
        "force_inline": force_inline,
        "force_file": force_file,
    }

    try:
        # Step 1: Validate and parse request using Pydantic schema
        request = CompanyDataRequest(**request_data)

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
