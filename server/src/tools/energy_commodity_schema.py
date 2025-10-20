"""
Unified energy commodity request schema for Alpha Vantage MCP server.

This module consolidates 3 separate energy commodity API endpoints into a single
GET_ENERGY_COMMODITY tool with simple parameter validation.

Energy commodities covered:
- wti: West Texas Intermediate crude oil prices
- brent: Brent (Europe) crude oil prices
- natural_gas: Henry Hub natural gas spot prices

All energy commodities support the same intervals: daily, weekly, monthly
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class EnergyCommodityRequest(BaseModel):
    """
    Unified energy commodity request schema.

    Consolidates 3 Alpha Vantage energy commodity API endpoints with uniform
    parameter validation. All energy commodities support the same intervals.

    **Supported Commodities**:
    - wti: West Texas Intermediate crude oil prices
    - brent: Brent (Europe) crude oil prices
    - natural_gas: Henry Hub natural gas spot prices

    **Intervals** (all commodities support):
    - daily: Daily prices
    - weekly: Weekly prices
    - monthly: Monthly prices (default)

    Examples:
        >>> # WTI crude oil with daily prices
        >>> request = EnergyCommodityRequest(
        ...     commodity_type="wti",
        ...     interval="daily"
        ... )

        >>> # Brent crude oil with monthly prices
        >>> request = EnergyCommodityRequest(
        ...     commodity_type="brent",
        ...     interval="monthly"
        ... )

        >>> # Natural gas with weekly prices
        >>> request = EnergyCommodityRequest(
        ...     commodity_type="natural_gas",
        ...     interval="weekly"
        ... )

        >>> # Default interval (monthly) with JSON output
        >>> request = EnergyCommodityRequest(
        ...     commodity_type="wti",
        ...     datatype="json"
        ... )
    """

    commodity_type: Literal["wti", "brent", "natural_gas"] = Field(
        description=(
            "Type of energy commodity to retrieve. Options:\n"
            "- wti: West Texas Intermediate crude oil prices\n"
            "- brent: Brent (Europe) crude oil prices\n"
            "- natural_gas: Henry Hub natural gas spot prices"
        )
    )

    interval: Literal["daily", "weekly", "monthly"] = Field(
        "monthly",
        description=(
            "Time interval between data points. All energy commodities support:\n"
            "- daily: Daily prices\n"
            "- weekly: Weekly prices\n"
            "- monthly: Monthly prices (default)"
        ),
    )

    datatype: Literal["json", "csv"] = Field(
        "csv",
        description=(
            "Response format. Options:\n"
            "- json: Returns data in JSON format\n"
            "- csv: Returns data as CSV (comma separated value) string (default)"
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
    def validate_mutually_exclusive_flags(self):
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
