"""
Unified economic indicators request schema for Alpha Vantage MCP server.

This module consolidates 10 separate economic indicator API endpoints into a single
GET_ECONOMIC_INDICATOR tool with conditional parameter validation based on indicator_type.

Economic indicators covered:
- real_gdp: Annual/quarterly Real GDP
- real_gdp_per_capita: Quarterly Real GDP per capita (fixed interval)
- treasury_yield: Daily/weekly/monthly US treasury yields (requires maturity)
- federal_funds_rate: Daily/weekly/monthly federal funds rate
- cpi: Monthly/semiannual Consumer Price Index
- inflation: Annual inflation rates (fixed interval)
- retail_sales: Monthly retail sales data (fixed interval)
- durables: Monthly durable goods orders (fixed interval)
- unemployment: Monthly unemployment rate (fixed interval)
- nonfarm_payroll: Monthly nonfarm payroll (fixed interval)
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class EconomicIndicatorRequest(BaseModel):
    """
    Unified economic indicator request schema.

    Consolidates 10 Alpha Vantage economic indicator API endpoints with conditional
    parameter validation based on indicator type. Each indicator has different interval
    requirements:

    **Flexible Intervals** (interval parameter required):
    - real_gdp: quarterly OR annual
    - treasury_yield: daily, weekly, OR monthly (also requires maturity)
    - federal_funds_rate: daily, weekly, OR monthly
    - cpi: monthly OR semiannual

    **Fixed Intervals** (no interval parameter accepted):
    - real_gdp_per_capita: quarterly only
    - inflation: annual only
    - retail_sales: monthly only
    - durables: monthly only
    - unemployment: monthly only
    - nonfarm_payroll: monthly only

    **Special Cases**:
    - treasury_yield: Requires BOTH interval AND maturity parameters

    Examples:
        >>> # GDP with quarterly interval
        >>> request = EconomicIndicatorRequest(
        ...     indicator_type="real_gdp",
        ...     interval="quarterly"
        ... )

        >>> # Treasury yield with interval and maturity
        >>> request = EconomicIndicatorRequest(
        ...     indicator_type="treasury_yield",
        ...     interval="monthly",
        ...     maturity="10year"
        ... )

        >>> # Fixed interval indicator (no interval parameter)
        >>> request = EconomicIndicatorRequest(
        ...     indicator_type="inflation"
        ... )

        >>> # CPI with semiannual interval
        >>> request = EconomicIndicatorRequest(
        ...     indicator_type="cpi",
        ...     interval="semiannual"
        ... )
    """

    indicator_type: Literal[
        "real_gdp",
        "real_gdp_per_capita",
        "treasury_yield",
        "federal_funds_rate",
        "cpi",
        "inflation",
        "retail_sales",
        "durables",
        "unemployment",
        "nonfarm_payroll",
    ] = Field(
        description=(
            "Type of economic indicator to retrieve. Options:\n"
            "- real_gdp: US Real GDP (quarterly/annual)\n"
            "- real_gdp_per_capita: US Real GDP per capita (quarterly only)\n"
            "- treasury_yield: US Treasury yields (daily/weekly/monthly + maturity)\n"
            "- federal_funds_rate: Federal funds rate (daily/weekly/monthly)\n"
            "- cpi: Consumer Price Index (monthly/semiannual)\n"
            "- inflation: Inflation rates (annual only)\n"
            "- retail_sales: Retail sales data (monthly only)\n"
            "- durables: Durable goods orders (monthly only)\n"
            "- unemployment: Unemployment rate (monthly only)\n"
            "- nonfarm_payroll: Nonfarm payroll (monthly only)"
        )
    )

    interval: Literal["daily", "weekly", "monthly", "quarterly", "annual", "semiannual"] | None = (
        Field(
            None,
            description=(
                "Time interval between data points. Required for some indicators:\n"
                "- real_gdp: quarterly OR annual\n"
                "- treasury_yield: daily, weekly, OR monthly\n"
                "- federal_funds_rate: daily, weekly, OR monthly\n"
                "- cpi: monthly OR semiannual\n"
                "Not accepted for: real_gdp_per_capita, inflation, retail_sales, "
                "durables, unemployment, nonfarm_payroll (these use fixed intervals)"
            ),
        )
    )

    maturity: Literal["3month", "2year", "5year", "7year", "10year", "30year"] | None = Field(
        None,
        description=(
            "Maturity timeline for treasury yields. Required for treasury_yield indicator. "
            "Options: 3month, 2year, 5year, 7year, 10year, 30year. "
            "Not applicable to other indicators."
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
    def validate_indicator_params(self):
        """
        Validate parameters based on indicator type.

        This validator enforces complex conditional logic:
        1. Indicators requiring interval parameter with specific allowed values
        2. Indicators with fixed intervals that reject interval parameter
        3. treasury_yield requiring both interval AND maturity
        4. Maturity only valid for treasury_yield
        5. Mutually exclusive output flags

        Returns:
            Validated model instance.

        Raises:
            ValueError: If parameters are invalid for the specified indicator_type.
        """
        # Define interval requirements per indicator type
        REQUIRES_INTERVAL = {
            "real_gdp": ["quarterly", "annual"],
            "federal_funds_rate": ["daily", "weekly", "monthly"],
            "cpi": ["monthly", "semiannual"],
        }

        TREASURY_YIELD_INTERVALS = ["daily", "weekly", "monthly"]

        FIXED_INTERVAL_INDICATORS = [
            "real_gdp_per_capita",
            "inflation",
            "retail_sales",
            "durables",
            "unemployment",
            "nonfarm_payroll",
        ]

        # Validate indicators requiring interval parameter
        if self.indicator_type in REQUIRES_INTERVAL:
            allowed_intervals = REQUIRES_INTERVAL[self.indicator_type]

            if self.interval is None:
                raise ValueError(
                    f"{self.indicator_type} requires interval parameter. "
                    f"Allowed values: {', '.join(allowed_intervals)}"
                )

            if self.interval not in allowed_intervals:
                raise ValueError(
                    f"Invalid interval '{self.interval}' for {self.indicator_type}. "
                    f"Allowed values: {', '.join(allowed_intervals)}"
                )

        # Validate treasury_yield special case (requires both interval AND maturity)
        if self.indicator_type == "treasury_yield":
            if self.interval is None:
                raise ValueError(
                    "treasury_yield requires interval parameter. "
                    f"Allowed values: {', '.join(TREASURY_YIELD_INTERVALS)}"
                )

            if self.interval not in TREASURY_YIELD_INTERVALS:
                raise ValueError(
                    f"Invalid interval '{self.interval}' for treasury_yield. "
                    f"Allowed values: {', '.join(TREASURY_YIELD_INTERVALS)}"
                )

            if self.maturity is None:
                raise ValueError(
                    "treasury_yield requires maturity parameter. "
                    "Allowed values: 3month, 2year, 5year, 7year, 10year, 30year"
                )

        # Validate indicators with fixed intervals (reject interval if provided)
        if self.indicator_type in FIXED_INTERVAL_INDICATORS:
            if self.interval is not None:
                # Determine the fixed interval for error message
                fixed_intervals = {
                    "real_gdp_per_capita": "quarterly",
                    "inflation": "annual",
                    "retail_sales": "monthly",
                    "durables": "monthly",
                    "unemployment": "monthly",
                    "nonfarm_payroll": "monthly",
                }
                fixed_interval = fixed_intervals[self.indicator_type]

                raise ValueError(
                    f"{self.indicator_type} does not accept interval parameter. "
                    f"This indicator uses a fixed {fixed_interval} interval."
                )

        # Validate maturity only valid for treasury_yield
        if self.maturity is not None and self.indicator_type != "treasury_yield":
            raise ValueError(
                f"maturity parameter is only valid for treasury_yield indicator, "
                f"not for {self.indicator_type}"
            )

        # Validate mutually exclusive output flags
        if self.force_inline and self.force_file:
            raise ValueError(
                "force_inline and force_file are mutually exclusive. "
                "Choose one or neither to use automatic output decision."
            )

        return self
