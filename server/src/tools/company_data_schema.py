"""
Unified company data request schema for Alpha Vantage MCP server.

This module consolidates 5 separate company data API endpoints into a single
GET_COMPANY_DATA tool with conditional parameter validation based on data_type.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CompanyDataRequest(BaseModel):
    """
    Unified company data request schema.

    Consolidates the following Alpha Vantage API endpoints:
    - COMPANY_OVERVIEW (company_overview) - Company information, ratios, and metrics
    - ETF_PROFILE (etf_profile) - ETF holdings and sector/asset allocations
    - DIVIDENDS (dividends) - Historical and future dividend distributions
    - SPLITS (splits) - Historical stock split events
    - EARNINGS (earnings) - Annual and quarterly earnings with estimates

    Examples:
        >>> # Get company overview for IBM
        >>> request = CompanyDataRequest(
        ...     data_type="company_overview",
        ...     symbol="IBM"
        ... )

        >>> # Get ETF profile for QQQ
        >>> request = CompanyDataRequest(
        ...     data_type="etf_profile",
        ...     symbol="QQQ"
        ... )

        >>> # Get dividend history in CSV format
        >>> request = CompanyDataRequest(
        ...     data_type="dividends",
        ...     symbol="IBM",
        ...     datatype="csv"
        ... )

        >>> # Get stock splits in JSON format
        >>> request = CompanyDataRequest(
        ...     data_type="splits",
        ...     symbol="AAPL",
        ...     datatype="json"
        ... )

        >>> # Get earnings data
        >>> request = CompanyDataRequest(
        ...     data_type="earnings",
        ...     symbol="MSFT"
        ... )
    """

    data_type: Literal["company_overview", "etf_profile", "dividends", "splits", "earnings"] = (
        Field(
            description=(
                "Type of company data to retrieve. Options: "
                "company_overview (Company information and metrics), "
                "etf_profile (ETF holdings and allocations), "
                "dividends (Dividend history), "
                "splits (Stock split history), "
                "earnings (Annual and quarterly earnings)"
            )
        )
    )

    symbol: str = Field(description="Stock or ETF ticker symbol (e.g., IBM, QQQ, AAPL)")

    datatype: Literal["json", "csv"] = Field(
        "json",
        description=(
            "Output format for dividends and splits. Options: 'json' or 'csv'. "
            "Default: 'json'. Note: company_overview, etf_profile, and earnings "
            "always return JSON regardless of this parameter."
        ),
    )

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
    def validate_data_type_params(self):
        """
        Validate that parameters are appropriate for the specified data_type.

        This validator enforces that:
        - company_overview, etf_profile, and earnings ignore the datatype parameter
          (they always return JSON)
        - dividends and splits respect the datatype parameter

        Returns:
            Validated model instance.

        Raises:
            ValueError: If force_inline and force_file are both True.
        """
        # Validate that force_inline and force_file are mutually exclusive
        if self.force_inline and self.force_file:
            raise ValueError(
                "force_inline and force_file are mutually exclusive. "
                "Choose one or neither to use automatic output decision."
            )

        # Note: We don't raise an error if datatype is set for company_overview/etf_profile/earnings
        # We just ignore it in the router. This makes the API more forgiving.

        return self
