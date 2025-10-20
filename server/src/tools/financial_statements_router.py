"""
Routing logic for unified financial statements tool.

This module maps statement_type values to Alpha Vantage API function names
and transforms request parameters into API-compatible format.
"""

from typing import Any

from .financial_statements_schema import FinancialStatementsRequest

# Mapping of statement_type to Alpha Vantage API function names
STATEMENT_TYPE_TO_FUNCTION = {
    "income_statement": "INCOME_STATEMENT",
    "balance_sheet": "BALANCE_SHEET",
    "cash_flow": "CASH_FLOW",
}


def get_api_function_name(statement_type: str) -> str:
    """
    Get Alpha Vantage API function name for a statement type.

    Args:
        statement_type: The statement type from FinancialStatementsRequest.

    Returns:
        Alpha Vantage API function name (uppercase).

    Raises:
        ValueError: If statement_type is not recognized.

    Examples:
        >>> get_api_function_name("income_statement")
        'INCOME_STATEMENT'
        >>> get_api_function_name("balance_sheet")
        'BALANCE_SHEET'
        >>> get_api_function_name("cash_flow")
        'CASH_FLOW'
    """
    if statement_type not in STATEMENT_TYPE_TO_FUNCTION:
        valid_types = ", ".join(STATEMENT_TYPE_TO_FUNCTION.keys())
        raise ValueError(f"Unknown statement_type '{statement_type}'. Valid options: {valid_types}")

    return STATEMENT_TYPE_TO_FUNCTION[statement_type]


def transform_request_params(request: FinancialStatementsRequest) -> dict[str, Any]:
    """
    Transform FinancialStatementsRequest into Alpha Vantage API parameters.

    This function extracts the parameters needed for the API call.
    All financial statement endpoints use the same parameters (symbol only).

    Args:
        request: Validated FinancialStatementsRequest instance.

    Returns:
        Dictionary of API parameters ready for _make_api_request.

    Examples:
        >>> request = FinancialStatementsRequest(
        ...     statement_type="income_statement",
        ...     symbol="IBM"
        ... )
        >>> params = transform_request_params(request)
        >>> params["symbol"]
        'IBM'
    """
    params: dict[str, Any] = {
        "symbol": request.symbol,
    }

    return params


def get_output_decision_params(request: FinancialStatementsRequest) -> dict[str, bool]:
    """
    Extract output decision parameters from request.

    These parameters control whether the output should be written to a file
    or returned inline, and can override the automatic decision made by
    the output helper.

    Args:
        request: FinancialStatementsRequest instance.

    Returns:
        Dictionary with force_inline and force_file flags.

    Examples:
        >>> request = FinancialStatementsRequest(
        ...     statement_type="income_statement",
        ...     symbol="IBM",
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


def validate_routing(request: FinancialStatementsRequest) -> None:
    """
    Validate that the request can be properly routed.

    This is a final safety check before making the API call.
    Should not raise any errors if the FinancialStatementsRequest validation
    worked correctly, but provides defense-in-depth.

    Args:
        request: FinancialStatementsRequest instance.

    Raises:
        ValueError: If routing validation fails.

    Examples:
        >>> request = FinancialStatementsRequest(
        ...     statement_type="income_statement",
        ...     symbol="IBM"
        ... )
        >>> validate_routing(request)  # No error
    """
    statement_type = request.statement_type

    # Verify we can route this statement type
    if statement_type not in STATEMENT_TYPE_TO_FUNCTION:
        raise ValueError(f"Cannot route statement_type '{statement_type}'")

    # Verify symbol is provided (should be caught by Pydantic, but double-check)
    if not request.symbol or not isinstance(request.symbol, str):
        raise ValueError("Routing failed: symbol must be a non-empty string")


class RoutingError(Exception):
    """Exception raised when request routing fails."""

    pass


def route_request(request: FinancialStatementsRequest) -> tuple[str, dict[str, Any]]:
    """
    Route a FinancialStatementsRequest to the appropriate API function with parameters.

    This is the main entry point for the routing logic. It:
    1. Validates the request can be routed
    2. Gets the API function name
    3. Transforms the parameters

    Args:
        request: Validated FinancialStatementsRequest instance.

    Returns:
        Tuple of (api_function_name, api_parameters).

    Raises:
        RoutingError: If routing fails for any reason.

    Examples:
        >>> request = FinancialStatementsRequest(
        ...     statement_type="income_statement",
        ...     symbol="AAPL"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'INCOME_STATEMENT'
        >>> params["symbol"]
        'AAPL'

        >>> request = FinancialStatementsRequest(
        ...     statement_type="balance_sheet",
        ...     symbol="MSFT"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'BALANCE_SHEET'
        >>> params["symbol"]
        'MSFT'

        >>> request = FinancialStatementsRequest(
        ...     statement_type="cash_flow",
        ...     symbol="GOOGL"
        ... )
        >>> function_name, params = route_request(request)
        >>> function_name
        'CASH_FLOW'
        >>> params["symbol"]
        'GOOGL'
    """
    try:
        # Validate routing
        validate_routing(request)

        # Get API function name
        function_name = get_api_function_name(request.statement_type)

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
