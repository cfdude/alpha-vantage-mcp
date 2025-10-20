"""
Unified materials commodity request schema for Alpha Vantage MCP server.

This module consolidates 8 separate materials commodity API endpoints into a single
GET_MATERIALS_COMMODITY tool with simple parameter validation.

Materials commodities covered:
- copper: Global copper price index
- aluminum: Global aluminum price index
- wheat: Global wheat price
- corn: Global corn price
- cotton: Global cotton price
- sugar: Global sugar price
- coffee: Global coffee price
- all_commodities: Global price index of all commodities

All materials commodities support the same intervals: monthly, quarterly, annual
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class MaterialsCommodityRequest(BaseModel):
    """
    Unified materials commodity request schema.

    Consolidates 8 Alpha Vantage materials commodity API endpoints with uniform
    parameter validation. All materials commodities support the same intervals.

    **Supported Commodities**:
    - copper: Global copper price index
    - aluminum: Global aluminum price index
    - wheat: Global wheat price
    - corn: Global corn price
    - cotton: Global cotton price
    - sugar: Global sugar price
    - coffee: Global coffee price
    - all_commodities: Global price index of all commodities

    **Intervals** (all commodities support):
    - monthly: Monthly prices (default)
    - quarterly: Quarterly prices
    - annual: Annual prices

    Examples:
        >>> # Copper with monthly prices
        >>> request = MaterialsCommodityRequest(
        ...     commodity_type="copper",
        ...     interval="monthly"
        ... )

        >>> # Wheat with quarterly prices
        >>> request = MaterialsCommodityRequest(
        ...     commodity_type="wheat",
        ...     interval="quarterly"
        ... )

        >>> # All commodities index with annual prices
        >>> request = MaterialsCommodityRequest(
        ...     commodity_type="all_commodities",
        ...     interval="annual"
        ... )

        >>> # Default interval (monthly) with JSON output
        >>> request = MaterialsCommodityRequest(
        ...     commodity_type="coffee",
        ...     datatype="json"
        ... )
    """

    commodity_type: Literal[
        "copper", "aluminum", "wheat", "corn", "cotton", "sugar", "coffee", "all_commodities"
    ] = Field(
        description=(
            "Type of materials commodity to retrieve. Options:\n"
            "- copper: Global copper price index\n"
            "- aluminum: Global aluminum price index\n"
            "- wheat: Global wheat price\n"
            "- corn: Global corn price\n"
            "- cotton: Global cotton price\n"
            "- sugar: Global sugar price\n"
            "- coffee: Global coffee price\n"
            "- all_commodities: Global price index of all commodities"
        )
    )

    interval: Literal["monthly", "quarterly", "annual"] = Field(
        "monthly",
        description=(
            "Time interval between data points. All materials commodities support:\n"
            "- monthly: Monthly prices (default)\n"
            "- quarterly: Quarterly prices\n"
            "- annual: Annual prices"
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
