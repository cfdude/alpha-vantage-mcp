"""
Unified financial statements request schema for Alpha Vantage MCP server.

This module consolidates 3 separate financial statement API endpoints into a single
GET_FINANCIAL_STATEMENTS tool with conditional parameter validation based on statement_type.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class FinancialStatementsRequest(BaseModel):
    """
    Unified financial statements request schema.

    Consolidates the following Alpha Vantage API endpoints:
    - INCOME_STATEMENT (income_statement) - Annual and quarterly income statements
    - BALANCE_SHEET (balance_sheet) - Annual and quarterly balance sheets
    - CASH_FLOW (cash_flow) - Annual and quarterly cash flow statements

    All statements return normalized fields mapped to GAAP and IFRS taxonomies.
    Data is generally refreshed on the same day a company reports its latest
    earnings and financials.

    Examples:
        >>> # Get income statement for IBM
        >>> request = FinancialStatementsRequest(
        ...     statement_type="income_statement",
        ...     symbol="IBM"
        ... )

        >>> # Get balance sheet for Apple
        >>> request = FinancialStatementsRequest(
        ...     statement_type="balance_sheet",
        ...     symbol="AAPL"
        ... )

        >>> # Get cash flow statement for Microsoft
        >>> request = FinancialStatementsRequest(
        ...     statement_type="cash_flow",
        ...     symbol="MSFT"
        ... )
    """

    statement_type: Literal["income_statement", "balance_sheet", "cash_flow"] = Field(
        description=(
            "Type of financial statement to retrieve. Options: "
            "income_statement (Income Statement), "
            "balance_sheet (Balance Sheet), "
            "cash_flow (Cash Flow Statement)"
        )
    )

    symbol: str = Field(description="Stock ticker symbol (e.g., IBM, AAPL, MSFT)")

    # Output control overrides
    force_inline: bool = Field(
        False,
        description=(
            "Force inline output regardless of size. Overrides automatic file/inline decision. "
            "Use with caution for large datasets."
        ),
    )

    force_file: bool = Field(
        False,
        description=(
            "Force file output regardless of size. Overrides automatic file/inline decision. "
            "Useful for ensuring data is saved to disk."
        ),
    )

    @model_validator(mode="after")
    def validate_output_flags(self):
        """
        Validate that force_inline and force_file are mutually exclusive.

        Returns:
            Validated model instance.

        Raises:
            ValueError: If both force_inline and force_file are True.
        """
        if self.force_inline and self.force_file:
            raise ValueError(
                "force_inline and force_file are mutually exclusive. "
                "Choose one or neither to use automatic output decision."
            )

        return self
