"""
Unified market data tool for Alpha Vantage MCP server.

This module consolidates 3 separate market data API endpoints into a single
GET_MARKET_DATA tool, reducing context window usage and simplifying the API.

Consolidates:
- LISTING_STATUS (Active or delisted US stocks and ETFs)
- EARNINGS_CALENDAR (Upcoming earnings in next 3/6/12 months)
- IPO_CALENDAR (Upcoming IPOs in next 3 months)
"""

import json

from pydantic import ValidationError

from src.common import _make_api_request
from src.tools.registry import tool

from .market_data_router import (
    RoutingError,
    route_request,
)
from .market_data_schema import MarketDataRequest


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
                "The request parameters do not meet the requirements for the specified request_type. "
                "Please check the parameter descriptions and try again."
            ),
            "request_data": request_data,
        }

    elif isinstance(error, RoutingError):
        # Routing error - problem with request_type or parameter routing
        return {
            "error": "Request routing failed",
            "message": str(error),
            "details": (
                "The request could not be routed to an API endpoint. "
                "This may indicate a configuration issue or unsupported request_type."
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
def get_market_data(
    request_type: str,
    date: str | None = None,
    state: str = "active",
    symbol: str | None = None,
    horizon: str = "3month",
    force_inline: bool = False,
    force_file: bool = False,
) -> dict | str:
    """
    Unified market data retrieval for all Alpha Vantage market data endpoints.

    This tool consolidates 3 separate market data APIs into a single endpoint with
    complex conditional parameter validation based on request_type. It automatically
    handles large responses by using the output helper from Sprint 1.

    Args:
        request_type: Type of market data to retrieve. Options:
            - 'listing_status': Active or delisted US stocks and ETFs
              Returns comprehensive listing data as of latest trading day or historical date
            - 'earnings_calendar': Upcoming company earnings in next 3, 6, or 12 months
              Returns earnings dates and estimates for all companies or specific symbol
            - 'ipo_calendar': Upcoming IPOs in next 3 months
              Returns expected IPO dates, price ranges, and company information

        date: Date for listing_status query in YYYY-MM-DD format (e.g., '2020-01-15').
            If not set, returns symbols as of latest trading day.
            If set, returns symbols on that historical date.
            Supports dates from 2010-01-01 onwards.
            Only used with request_type='listing_status'. Ignored for other types.

        state: State filter for listing_status. Options: 'active', 'delisted'. Default: 'active'.
            - 'active': Returns actively traded stocks and ETFs
            - 'delisted': Returns delisted assets
            Only used with request_type='listing_status'. Ignored for other types.

        symbol: Stock ticker symbol for earnings_calendar (e.g., 'IBM', 'AAPL').
            If not set, returns full list of scheduled earnings.
            If set, returns earnings for that specific symbol.
            Only used with request_type='earnings_calendar'. Ignored for other types.

        horizon: Time horizon for earnings_calendar. Options: '3month', '6month', '12month'.
            Default: '3month'.
            - '3month': Returns earnings expected in next 3 months
            - '6month': Returns earnings expected in next 6 months
            - '12month': Returns earnings expected in next 12 months
            Only used with request_type='earnings_calendar'. Ignored for other types.

        force_inline: Force inline output regardless of size (default: False).
            Overrides automatic file/inline decision.

        force_file: Force file output regardless of size (default: False).
            Overrides automatic file/inline decision.

    Returns:
        Market data in CSV format (str) for most requests, or dict for JSON responses.
        For large responses, may return a file reference instead of inline data.

    Raises:
        ValidationError: If request parameters are invalid for the specified request_type.
        RoutingError: If request cannot be routed to an API endpoint.

    Examples:
        # Get active stocks as of today
        >>> result = get_market_data(
        ...     request_type="listing_status"
        ... )

        # Get delisted stocks as of a specific historical date
        >>> result = get_market_data(
        ...     request_type="listing_status",
        ...     date="2020-01-15",
        ...     state="delisted"
        ... )

        # Get all earnings expected in next 3 months
        >>> result = get_market_data(
        ...     request_type="earnings_calendar"
        ... )

        # Get earnings for IBM in next 6 months
        >>> result = get_market_data(
        ...     request_type="earnings_calendar",
        ...     symbol="IBM",
        ...     horizon="6month"
        ... )

        # Get earnings for all companies in next 12 months
        >>> result = get_market_data(
        ...     request_type="earnings_calendar",
        ...     horizon="12month"
        ... )

        # Get upcoming IPOs
        >>> result = get_market_data(
        ...     request_type="ipo_calendar"
        ... )

        # Force file output for large dataset
        >>> result = get_market_data(
        ...     request_type="listing_status",
        ...     force_file=True
        ... )

    Context Window Reduction:
        This single tool replaces 3 individual tools, significantly reducing the
        context window required for tool definitions. Estimated savings: ~1,800 tokens.

    Data Structure by Type:
        listing_status:
            Returns CSV with columns:
            - symbol: Stock ticker symbol
            - name: Company name
            - exchange: Trading exchange
            - assetType: Type of asset (Stock, ETF, etc.)
            - ipoDate: Date of IPO
            - delistingDate: Date of delisting (if applicable)
            - status: Active or Delisted

        earnings_calendar:
            Returns CSV with columns:
            - symbol: Stock ticker symbol
            - name: Company name
            - reportDate: Earnings report date
            - fiscalDateEnding: Fiscal quarter/year ending date
            - estimate: Analyst EPS estimate
            - currency: Currency of estimates

        ipo_calendar:
            Returns CSV with columns:
            - symbol: Stock ticker symbol
            - name: Company name
            - ipoDate: Expected IPO date
            - priceRangeLow: Low end of IPO price range
            - priceRangeHigh: High end of IPO price range
            - currency: Currency of pricing
            - exchange: Expected trading exchange

    Parameter Requirements by Request Type:
        listing_status:
            Optional: date (YYYY-MM-DD), state (active or delisted)
            Ignored: symbol, horizon

        earnings_calendar:
            Optional: symbol, horizon (3month, 6month, or 12month)
            Ignored: date, state

        ipo_calendar:
            No additional parameters accepted
            Ignored: date, state, symbol, horizon

    Output Control:
        - By default, output decision is made automatically based on response size
        - force_inline=True: Always return data inline (use with caution for large datasets)
        - force_file=True: Always save data to file
        - force_inline and force_file are mutually exclusive

    Use Cases:
        listing_status:
            - Research asset lifecycle and survivorship
            - Identify newly listed or delisted securities
            - Historical analysis of market composition
            - Track changes in trading universe over time

        earnings_calendar:
            - Plan trading strategies around earnings releases
            - Monitor earnings seasons
            - Track specific company reporting schedules
            - Analyze earnings estimate trends

        ipo_calendar:
            - Identify new investment opportunities
            - Track upcoming market entrants
            - Plan IPO trading strategies
            - Research IPO pricing trends
    """
    # Collect all input parameters
    request_data = {
        "request_type": request_type,
        "date": date,
        "state": state,
        "symbol": symbol,
        "horizon": horizon,
        "force_inline": force_inline,
        "force_file": force_file,
    }

    try:
        # Step 1: Validate and parse request using Pydantic schema
        request = MarketDataRequest(**request_data)

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
