"""
Unit tests for EconomicIndicatorRequest schema validation.

Tests cover:
- All 10 indicator types
- Interval validation (required vs optional vs rejected)
- Maturity validation (only for treasury_yield)
- Fixed interval indicators rejecting interval parameter
- Output flag validation (force_inline/force_file)
- Invalid parameter combinations
- Edge cases and error messages
- Parameterized tests for efficiency

Test Coverage Target: ≥85%
Expected Test Count: ≥100 tests
"""

import pytest
from pydantic import ValidationError

from src.tools.economic_indicators_schema import EconomicIndicatorRequest


class TestIndicatorTypes:
    """Test all economic indicator types."""

    @pytest.mark.parametrize(
        "indicator_type",
        [
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
        ],
    )
    def test_all_valid_indicator_types(self, indicator_type):
        """Test that all 10 indicator types are recognized."""
        # For indicators requiring parameters, provide them
        if indicator_type == "real_gdp":
            request = EconomicIndicatorRequest(indicator_type=indicator_type, interval="quarterly")
        elif indicator_type == "treasury_yield":
            request = EconomicIndicatorRequest(
                indicator_type=indicator_type, interval="monthly", maturity="10year"
            )
        elif indicator_type in ["federal_funds_rate", "cpi"]:
            request = EconomicIndicatorRequest(indicator_type=indicator_type, interval="monthly")
        else:
            # Fixed interval indicators
            request = EconomicIndicatorRequest(indicator_type=indicator_type)

        assert request.indicator_type == indicator_type
        assert request.datatype == "csv"  # default
        assert request.force_inline is False  # default
        assert request.force_file is False  # default

    def test_invalid_indicator_type(self):
        """Test that invalid indicator types are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type="invalid_indicator")

        errors = exc_info.value.errors()
        assert any("indicator_type" in str(err) for err in errors)


class TestRealGDP:
    """Test real_gdp indicator validation."""

    def test_real_gdp_requires_interval(self):
        """Test that real_gdp requires interval parameter."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type="real_gdp")

        assert "interval" in str(exc_info.value).lower()
        assert "requires" in str(exc_info.value).lower()

    @pytest.mark.parametrize("interval", ["quarterly", "annual"])
    def test_real_gdp_valid_intervals(self, interval):
        """Test real_gdp accepts quarterly and annual intervals."""
        request = EconomicIndicatorRequest(indicator_type="real_gdp", interval=interval)
        assert request.interval == interval
        assert request.indicator_type == "real_gdp"

    @pytest.mark.parametrize("interval", ["daily", "weekly", "monthly", "semiannual"])
    def test_real_gdp_invalid_intervals(self, interval):
        """Test real_gdp rejects invalid intervals."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type="real_gdp", interval=interval)

        assert "interval" in str(exc_info.value).lower()
        assert interval in str(exc_info.value) or "allowed values" in str(exc_info.value).lower()

    def test_real_gdp_with_json_datatype(self):
        """Test real_gdp with JSON output format."""
        request = EconomicIndicatorRequest(
            indicator_type="real_gdp", interval="quarterly", datatype="json"
        )
        assert request.datatype == "json"

    def test_real_gdp_with_csv_datatype(self):
        """Test real_gdp with CSV output format."""
        request = EconomicIndicatorRequest(
            indicator_type="real_gdp", interval="annual", datatype="csv"
        )
        assert request.datatype == "csv"


class TestRealGDPPerCapita:
    """Test real_gdp_per_capita indicator validation (fixed quarterly interval)."""

    def test_real_gdp_per_capita_no_interval(self):
        """Test real_gdp_per_capita works without interval parameter."""
        request = EconomicIndicatorRequest(indicator_type="real_gdp_per_capita")
        assert request.indicator_type == "real_gdp_per_capita"
        assert request.interval is None

    @pytest.mark.parametrize("interval", ["quarterly", "annual", "monthly", "daily", "weekly"])
    def test_real_gdp_per_capita_rejects_interval(self, interval):
        """Test real_gdp_per_capita rejects any interval parameter."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type="real_gdp_per_capita", interval=interval)

        assert "does not accept interval" in str(exc_info.value).lower()
        assert "quarterly" in str(exc_info.value).lower()  # mentions fixed interval

    def test_real_gdp_per_capita_with_json(self):
        """Test real_gdp_per_capita with JSON output."""
        request = EconomicIndicatorRequest(indicator_type="real_gdp_per_capita", datatype="json")
        assert request.datatype == "json"


class TestTreasuryYield:
    """Test treasury_yield indicator validation (requires both interval AND maturity)."""

    def test_treasury_yield_requires_interval(self):
        """Test treasury_yield requires interval parameter."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type="treasury_yield", maturity="10year")

        assert "interval" in str(exc_info.value).lower()
        assert "requires" in str(exc_info.value).lower()

    def test_treasury_yield_requires_maturity(self):
        """Test treasury_yield requires maturity parameter."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type="treasury_yield", interval="monthly")

        assert "maturity" in str(exc_info.value).lower()
        assert "requires" in str(exc_info.value).lower()

    def test_treasury_yield_requires_both_params(self):
        """Test treasury_yield requires both interval and maturity."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type="treasury_yield")

        error_str = str(exc_info.value).lower()
        assert "interval" in error_str or "maturity" in error_str

    @pytest.mark.parametrize("interval", ["daily", "weekly", "monthly"])
    @pytest.mark.parametrize("maturity", ["3month", "2year", "5year", "7year", "10year", "30year"])
    def test_treasury_yield_valid_combinations(self, interval, maturity):
        """Test all valid interval/maturity combinations for treasury_yield."""
        request = EconomicIndicatorRequest(
            indicator_type="treasury_yield", interval=interval, maturity=maturity
        )
        assert request.interval == interval
        assert request.maturity == maturity

    @pytest.mark.parametrize("interval", ["quarterly", "annual", "semiannual"])
    def test_treasury_yield_invalid_intervals(self, interval):
        """Test treasury_yield rejects invalid intervals."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(
                indicator_type="treasury_yield", interval=interval, maturity="10year"
            )

        assert "interval" in str(exc_info.value).lower()

    def test_treasury_yield_invalid_maturity(self):
        """Test treasury_yield rejects invalid maturity values."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(
                indicator_type="treasury_yield", interval="monthly", maturity="invalid"
            )

        errors = exc_info.value.errors()
        assert any("maturity" in str(err) for err in errors)


class TestFederalFundsRate:
    """Test federal_funds_rate indicator validation."""

    def test_federal_funds_rate_requires_interval(self):
        """Test federal_funds_rate requires interval parameter."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type="federal_funds_rate")

        assert "interval" in str(exc_info.value).lower()
        assert "requires" in str(exc_info.value).lower()

    @pytest.mark.parametrize("interval", ["daily", "weekly", "monthly"])
    def test_federal_funds_rate_valid_intervals(self, interval):
        """Test federal_funds_rate accepts daily, weekly, and monthly intervals."""
        request = EconomicIndicatorRequest(indicator_type="federal_funds_rate", interval=interval)
        assert request.interval == interval

    @pytest.mark.parametrize("interval", ["quarterly", "annual", "semiannual"])
    def test_federal_funds_rate_invalid_intervals(self, interval):
        """Test federal_funds_rate rejects invalid intervals."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type="federal_funds_rate", interval=interval)

        assert "interval" in str(exc_info.value).lower()


class TestCPI:
    """Test cpi (Consumer Price Index) indicator validation."""

    def test_cpi_requires_interval(self):
        """Test cpi requires interval parameter."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type="cpi")

        assert "interval" in str(exc_info.value).lower()
        assert "requires" in str(exc_info.value).lower()

    @pytest.mark.parametrize("interval", ["monthly", "semiannual"])
    def test_cpi_valid_intervals(self, interval):
        """Test cpi accepts monthly and semiannual intervals."""
        request = EconomicIndicatorRequest(indicator_type="cpi", interval=interval)
        assert request.interval == interval

    @pytest.mark.parametrize("interval", ["daily", "weekly", "quarterly", "annual"])
    def test_cpi_invalid_intervals(self, interval):
        """Test cpi rejects invalid intervals."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type="cpi", interval=interval)

        assert "interval" in str(exc_info.value).lower()


class TestFixedIntervalIndicators:
    """Test indicators with fixed intervals (no interval parameter accepted)."""

    @pytest.mark.parametrize(
        "indicator_type",
        ["inflation", "retail_sales", "durables", "unemployment", "nonfarm_payroll"],
    )
    def test_fixed_interval_indicators_no_interval(self, indicator_type):
        """Test fixed interval indicators work without interval parameter."""
        request = EconomicIndicatorRequest(indicator_type=indicator_type)
        assert request.indicator_type == indicator_type
        assert request.interval is None

    @pytest.mark.parametrize(
        "indicator_type,expected_interval",
        [
            ("inflation", "annual"),
            ("retail_sales", "monthly"),
            ("durables", "monthly"),
            ("unemployment", "monthly"),
            ("nonfarm_payroll", "monthly"),
        ],
    )
    @pytest.mark.parametrize("interval", ["daily", "weekly", "monthly", "quarterly", "annual"])
    def test_fixed_interval_indicators_reject_interval(
        self, indicator_type, expected_interval, interval
    ):
        """Test fixed interval indicators reject any interval parameter."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type=indicator_type, interval=interval)

        error_str = str(exc_info.value).lower()
        assert "does not accept interval" in error_str
        assert expected_interval in error_str  # mentions the fixed interval


class TestInflation:
    """Test inflation indicator (fixed annual interval)."""

    def test_inflation_no_params(self):
        """Test inflation works with no parameters."""
        request = EconomicIndicatorRequest(indicator_type="inflation")
        assert request.indicator_type == "inflation"
        assert request.interval is None

    def test_inflation_with_datatype(self):
        """Test inflation with JSON datatype."""
        request = EconomicIndicatorRequest(indicator_type="inflation", datatype="json")
        assert request.datatype == "json"


class TestRetailSales:
    """Test retail_sales indicator (fixed monthly interval)."""

    def test_retail_sales_no_params(self):
        """Test retail_sales works with no parameters."""
        request = EconomicIndicatorRequest(indicator_type="retail_sales")
        assert request.indicator_type == "retail_sales"
        assert request.interval is None


class TestDurables:
    """Test durables indicator (fixed monthly interval)."""

    def test_durables_no_params(self):
        """Test durables works with no parameters."""
        request = EconomicIndicatorRequest(indicator_type="durables")
        assert request.indicator_type == "durables"
        assert request.interval is None


class TestUnemployment:
    """Test unemployment indicator (fixed monthly interval)."""

    def test_unemployment_no_params(self):
        """Test unemployment works with no parameters."""
        request = EconomicIndicatorRequest(indicator_type="unemployment")
        assert request.indicator_type == "unemployment"
        assert request.interval is None


class TestNonfarmPayroll:
    """Test nonfarm_payroll indicator (fixed monthly interval)."""

    def test_nonfarm_payroll_no_params(self):
        """Test nonfarm_payroll works with no parameters."""
        request = EconomicIndicatorRequest(indicator_type="nonfarm_payroll")
        assert request.indicator_type == "nonfarm_payroll"
        assert request.interval is None


class TestMaturityValidation:
    """Test maturity parameter validation (only valid for treasury_yield)."""

    @pytest.mark.parametrize(
        "indicator_type",
        [
            "real_gdp",
            "real_gdp_per_capita",
            "federal_funds_rate",
            "cpi",
            "inflation",
            "retail_sales",
            "durables",
            "unemployment",
            "nonfarm_payroll",
        ],
    )
    def test_maturity_rejected_for_non_treasury_indicators(self, indicator_type):
        """Test maturity parameter is rejected for all non-treasury indicators."""
        # Prepare valid request for each indicator type
        if indicator_type == "real_gdp":
            with pytest.raises(ValidationError) as exc_info:
                EconomicIndicatorRequest(
                    indicator_type=indicator_type, interval="quarterly", maturity="10year"
                )
        elif indicator_type in ["federal_funds_rate", "cpi"]:
            with pytest.raises(ValidationError) as exc_info:
                EconomicIndicatorRequest(
                    indicator_type=indicator_type, interval="monthly", maturity="10year"
                )
        else:
            # Fixed interval indicators
            with pytest.raises(ValidationError) as exc_info:
                EconomicIndicatorRequest(indicator_type=indicator_type, maturity="10year")

        assert "maturity" in str(exc_info.value).lower()
        assert "treasury" in str(exc_info.value).lower()

    def test_maturity_accepted_for_treasury_yield(self):
        """Test maturity parameter is accepted for treasury_yield."""
        request = EconomicIndicatorRequest(
            indicator_type="treasury_yield", interval="monthly", maturity="10year"
        )
        assert request.maturity == "10year"


class TestDatatypeValidation:
    """Test datatype parameter validation."""

    @pytest.mark.parametrize("datatype", ["json", "csv"])
    def test_valid_datatypes(self, datatype):
        """Test both JSON and CSV datatypes are accepted."""
        request = EconomicIndicatorRequest(indicator_type="inflation", datatype=datatype)
        assert request.datatype == datatype

    def test_invalid_datatype(self):
        """Test invalid datatype is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type="inflation", datatype="xml")

        errors = exc_info.value.errors()
        assert any("datatype" in str(err) for err in errors)

    def test_default_datatype(self):
        """Test default datatype is CSV."""
        request = EconomicIndicatorRequest(indicator_type="inflation")
        assert request.datatype == "csv"


class TestOutputFlags:
    """Test force_inline and force_file parameter validation."""

    def test_force_inline_only(self):
        """Test force_inline=True without force_file."""
        request = EconomicIndicatorRequest(indicator_type="inflation", force_inline=True)
        assert request.force_inline is True
        assert request.force_file is False

    def test_force_file_only(self):
        """Test force_file=True without force_inline."""
        request = EconomicIndicatorRequest(indicator_type="inflation", force_file=True)
        assert request.force_file is True
        assert request.force_inline is False

    def test_both_flags_false(self):
        """Test default behavior with both flags False."""
        request = EconomicIndicatorRequest(indicator_type="inflation")
        assert request.force_inline is False
        assert request.force_file is False

    def test_both_flags_true_rejected(self):
        """Test that setting both force_inline and force_file is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(
                indicator_type="inflation",
                force_inline=True,
                force_file=True,
            )

        assert "mutually exclusive" in str(exc_info.value).lower()

    @pytest.mark.parametrize(
        "force_inline,force_file,should_pass",
        [
            (False, False, True),
            (True, False, True),
            (False, True, True),
            (True, True, False),
        ],
    )
    def test_output_flag_combinations(self, force_inline, force_file, should_pass):
        """Test all combinations of output flags."""
        if should_pass:
            request = EconomicIndicatorRequest(
                indicator_type="inflation",
                force_inline=force_inline,
                force_file=force_file,
            )
            assert request.force_inline == force_inline
            assert request.force_file == force_file
        else:
            with pytest.raises(ValidationError) as exc_info:
                EconomicIndicatorRequest(
                    indicator_type="inflation",
                    force_inline=force_inline,
                    force_file=force_file,
                )
            assert "mutually exclusive" in str(exc_info.value).lower()


class TestComplexScenarios:
    """Test complex multi-parameter scenarios."""

    def test_real_gdp_full_request(self):
        """Test real_gdp with all optional parameters."""
        request = EconomicIndicatorRequest(
            indicator_type="real_gdp",
            interval="quarterly",
            datatype="json",
            force_file=True,
        )
        assert request.indicator_type == "real_gdp"
        assert request.interval == "quarterly"
        assert request.datatype == "json"
        assert request.force_file is True
        assert request.force_inline is False

    def test_treasury_yield_full_request(self):
        """Test treasury_yield with all optional parameters."""
        request = EconomicIndicatorRequest(
            indicator_type="treasury_yield",
            interval="daily",
            maturity="30year",
            datatype="csv",
            force_inline=True,
        )
        assert request.indicator_type == "treasury_yield"
        assert request.interval == "daily"
        assert request.maturity == "30year"
        assert request.datatype == "csv"
        assert request.force_inline is True
        assert request.force_file is False

    @pytest.mark.parametrize(
        "indicator_type,interval,maturity,datatype",
        [
            ("real_gdp", "quarterly", None, "json"),
            ("real_gdp", "annual", None, "csv"),
            ("treasury_yield", "monthly", "10year", "json"),
            ("treasury_yield", "weekly", "5year", "csv"),
            ("federal_funds_rate", "daily", None, "json"),
            ("federal_funds_rate", "monthly", None, "csv"),
            ("cpi", "monthly", None, "json"),
            ("cpi", "semiannual", None, "csv"),
        ],
    )
    def test_various_valid_combinations(self, indicator_type, interval, maturity, datatype):
        """Test various valid parameter combinations."""
        request = EconomicIndicatorRequest(
            indicator_type=indicator_type,
            interval=interval,
            maturity=maturity,
            datatype=datatype,
        )
        assert request.indicator_type == indicator_type
        assert request.interval == interval
        assert request.maturity == maturity
        assert request.datatype == datatype


class TestErrorMessages:
    """Test that error messages are clear and helpful."""

    def test_missing_interval_error_message(self):
        """Test error message when interval is missing for real_gdp."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type="real_gdp")

        error_msg = str(exc_info.value).lower()
        assert "interval" in error_msg
        assert "requires" in error_msg
        assert "allowed values" in error_msg or "quarterly" in error_msg

    def test_invalid_interval_error_message(self):
        """Test error message when interval is invalid for indicator type."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type="real_gdp", interval="monthly")

        error_msg = str(exc_info.value).lower()
        assert "interval" in error_msg
        assert "invalid" in error_msg or "allowed" in error_msg

    def test_rejected_interval_error_message(self):
        """Test error message when interval is provided for fixed interval indicator."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type="inflation", interval="annual")

        error_msg = str(exc_info.value).lower()
        assert "does not accept interval" in error_msg
        assert "annual" in error_msg  # mentions the fixed interval

    def test_missing_maturity_error_message(self):
        """Test error message when maturity is missing for treasury_yield."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(indicator_type="treasury_yield", interval="monthly")

        error_msg = str(exc_info.value).lower()
        assert "maturity" in error_msg
        assert "requires" in error_msg

    def test_invalid_maturity_error_message(self):
        """Test error message when maturity is provided for non-treasury indicator."""
        with pytest.raises(ValidationError) as exc_info:
            EconomicIndicatorRequest(
                indicator_type="real_gdp", interval="quarterly", maturity="10year"
            )

        error_msg = str(exc_info.value).lower()
        assert "maturity" in error_msg
        assert "treasury" in error_msg


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_none_values_for_optional_params(self):
        """Test that None values work for optional parameters."""
        request = EconomicIndicatorRequest(
            indicator_type="inflation",
            interval=None,
            maturity=None,
        )
        assert request.interval is None
        assert request.maturity is None

    def test_all_treasury_maturity_values(self):
        """Test all 6 maturity values for treasury_yield."""
        maturities = ["3month", "2year", "5year", "7year", "10year", "30year"]
        for maturity in maturities:
            request = EconomicIndicatorRequest(
                indicator_type="treasury_yield",
                interval="monthly",
                maturity=maturity,
            )
            assert request.maturity == maturity

    def test_case_sensitivity(self):
        """Test that indicator_type values are case-sensitive."""
        # Valid lowercase
        request = EconomicIndicatorRequest(indicator_type="inflation")
        assert request.indicator_type == "inflation"

        # Invalid uppercase should fail
        with pytest.raises(ValidationError):
            EconomicIndicatorRequest(indicator_type="INFLATION")

        # Invalid mixed case should fail
        with pytest.raises(ValidationError):
            EconomicIndicatorRequest(indicator_type="Inflation")
