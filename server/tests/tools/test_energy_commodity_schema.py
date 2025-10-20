"""
Unit tests for EnergyCommodityRequest schema validation.

Tests cover:
- All 3 energy commodity types
- All interval options (daily, weekly, monthly)
- Datatype validation (json, csv)
- Output flag validation (force_inline/force_file)
- Invalid parameter combinations
- Default values
- Edge cases and error messages

Test Coverage Target: ≥85%
Expected Test Count: ≥40 tests
"""

import pytest
from pydantic import ValidationError

from src.tools.energy_commodity_router import (
    get_api_function_name,
    route_request,
    transform_request_params,
    validate_routing,
)
from src.tools.energy_commodity_schema import EnergyCommodityRequest


class TestCommodityTypes:
    """Test all energy commodity types."""

    @pytest.mark.parametrize(
        "commodity_type,expected_function",
        [
            ("wti", "WTI"),
            ("brent", "BRENT"),
            ("natural_gas", "NATURAL_GAS"),
        ],
    )
    def test_all_valid_commodity_types(self, commodity_type, expected_function):
        """Test that all 3 commodity types are recognized."""
        request = EnergyCommodityRequest(commodity_type=commodity_type, interval="monthly")
        assert request.commodity_type == commodity_type
        assert request.datatype == "csv"  # default
        assert request.force_inline is False  # default
        assert request.force_file is False  # default

        # Also verify routing
        function_name = get_api_function_name(commodity_type)
        assert function_name == expected_function

    def test_invalid_commodity_type(self):
        """Test that invalid commodity types are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EnergyCommodityRequest(commodity_type="invalid_commodity")

        errors = exc_info.value.errors()
        assert any("commodity_type" in str(err) for err in errors)


class TestIntervals:
    """Test interval validation for energy commodities."""

    @pytest.mark.parametrize("interval", ["daily", "weekly", "monthly"])
    def test_all_valid_intervals(self, interval):
        """Test all valid intervals for energy commodities."""
        request = EnergyCommodityRequest(commodity_type="wti", interval=interval)
        assert request.interval == interval

    @pytest.mark.parametrize("commodity_type", ["wti", "brent", "natural_gas"])
    @pytest.mark.parametrize("interval", ["daily", "weekly", "monthly"])
    def test_all_commodities_support_all_intervals(self, commodity_type, interval):
        """Test that all energy commodities support all intervals."""
        request = EnergyCommodityRequest(commodity_type=commodity_type, interval=interval)
        assert request.commodity_type == commodity_type
        assert request.interval == interval

    def test_default_interval(self):
        """Test that default interval is monthly."""
        request = EnergyCommodityRequest(commodity_type="wti")
        assert request.interval == "monthly"

    def test_invalid_interval(self):
        """Test that invalid intervals are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EnergyCommodityRequest(commodity_type="wti", interval="invalid")

        errors = exc_info.value.errors()
        assert any("interval" in str(err) for err in errors)


class TestWTI:
    """Test WTI commodity specifically."""

    @pytest.mark.parametrize("interval", ["daily", "weekly", "monthly"])
    def test_wti_all_intervals(self, interval):
        """Test WTI with all valid intervals."""
        request = EnergyCommodityRequest(commodity_type="wti", interval=interval)
        assert request.commodity_type == "wti"
        assert request.interval == interval

    def test_wti_with_json_datatype(self):
        """Test WTI with JSON output format."""
        request = EnergyCommodityRequest(commodity_type="wti", interval="daily", datatype="json")
        assert request.datatype == "json"

    def test_wti_with_csv_datatype(self):
        """Test WTI with CSV output format."""
        request = EnergyCommodityRequest(commodity_type="wti", interval="weekly", datatype="csv")
        assert request.datatype == "csv"

    def test_wti_default_parameters(self):
        """Test WTI with default parameters."""
        request = EnergyCommodityRequest(commodity_type="wti")
        assert request.commodity_type == "wti"
        assert request.interval == "monthly"
        assert request.datatype == "csv"
        assert request.force_inline is False
        assert request.force_file is False


class TestBrent:
    """Test Brent commodity specifically."""

    @pytest.mark.parametrize("interval", ["daily", "weekly", "monthly"])
    def test_brent_all_intervals(self, interval):
        """Test Brent with all valid intervals."""
        request = EnergyCommodityRequest(commodity_type="brent", interval=interval)
        assert request.commodity_type == "brent"
        assert request.interval == interval

    def test_brent_with_json_datatype(self):
        """Test Brent with JSON output format."""
        request = EnergyCommodityRequest(
            commodity_type="brent", interval="monthly", datatype="json"
        )
        assert request.datatype == "json"


class TestNaturalGas:
    """Test natural gas commodity specifically."""

    @pytest.mark.parametrize("interval", ["daily", "weekly", "monthly"])
    def test_natural_gas_all_intervals(self, interval):
        """Test natural gas with all valid intervals."""
        request = EnergyCommodityRequest(commodity_type="natural_gas", interval=interval)
        assert request.commodity_type == "natural_gas"
        assert request.interval == interval

    def test_natural_gas_with_json_datatype(self):
        """Test natural gas with JSON output format."""
        request = EnergyCommodityRequest(
            commodity_type="natural_gas", interval="weekly", datatype="json"
        )
        assert request.datatype == "json"


class TestDatatypeValidation:
    """Test datatype parameter validation."""

    @pytest.mark.parametrize("datatype", ["json", "csv"])
    def test_valid_datatypes(self, datatype):
        """Test all valid datatype options."""
        request = EnergyCommodityRequest(commodity_type="wti", datatype=datatype)
        assert request.datatype == datatype

    def test_default_datatype(self):
        """Test that default datatype is csv."""
        request = EnergyCommodityRequest(commodity_type="wti")
        assert request.datatype == "csv"

    def test_invalid_datatype(self):
        """Test that invalid datatypes are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EnergyCommodityRequest(commodity_type="wti", datatype="invalid")

        errors = exc_info.value.errors()
        assert any("datatype" in str(err) for err in errors)


class TestOutputFlags:
    """Test output control flags validation."""

    def test_force_inline_flag(self):
        """Test force_inline flag can be set."""
        request = EnergyCommodityRequest(commodity_type="wti", force_inline=True)
        assert request.force_inline is True
        assert request.force_file is False

    def test_force_file_flag(self):
        """Test force_file flag can be set."""
        request = EnergyCommodityRequest(commodity_type="wti", force_file=True)
        assert request.force_file is True
        assert request.force_inline is False

    def test_mutually_exclusive_flags(self):
        """Test that force_inline and force_file are mutually exclusive."""
        with pytest.raises(ValidationError) as exc_info:
            EnergyCommodityRequest(commodity_type="wti", force_inline=True, force_file=True)

        assert "mutually exclusive" in str(exc_info.value).lower()

    def test_default_output_flags(self):
        """Test that output flags default to False."""
        request = EnergyCommodityRequest(commodity_type="wti")
        assert request.force_inline is False
        assert request.force_file is False


class TestRouting:
    """Test routing logic for energy commodities."""

    @pytest.mark.parametrize(
        "commodity_type,expected_function",
        [
            ("wti", "WTI"),
            ("brent", "BRENT"),
            ("natural_gas", "NATURAL_GAS"),
        ],
    )
    def test_commodity_type_routing(self, commodity_type, expected_function):
        """Test that commodity types route to correct API functions."""
        request = EnergyCommodityRequest(commodity_type=commodity_type)
        function_name, params = route_request(request)
        assert function_name == expected_function

    @pytest.mark.parametrize("interval", ["daily", "weekly", "monthly"])
    def test_interval_routing(self, interval):
        """Test that interval parameter is correctly routed."""
        request = EnergyCommodityRequest(commodity_type="wti", interval=interval)
        function_name, params = route_request(request)
        assert params["interval"] == interval

    @pytest.mark.parametrize("datatype", ["json", "csv"])
    def test_datatype_routing(self, datatype):
        """Test that datatype parameter is correctly routed."""
        request = EnergyCommodityRequest(commodity_type="wti", datatype=datatype)
        function_name, params = route_request(request)
        assert params["datatype"] == datatype

    def test_complete_routing(self):
        """Test complete routing with all parameters."""
        request = EnergyCommodityRequest(commodity_type="brent", interval="daily", datatype="json")
        function_name, params = route_request(request)
        assert function_name == "BRENT"
        assert params["interval"] == "daily"
        assert params["datatype"] == "json"

    def test_invalid_commodity_type_routing(self):
        """Test that invalid commodity types raise RoutingError."""
        # This should not happen due to Pydantic validation, but test defense-in-depth
        # We can't create an invalid request through normal means, so test the function directly
        with pytest.raises(ValueError):
            get_api_function_name("invalid_commodity")


class TestParameterTransformation:
    """Test parameter transformation logic."""

    def test_transform_request_params_basic(self):
        """Test basic parameter transformation."""
        request = EnergyCommodityRequest(commodity_type="wti")
        params = transform_request_params(request)
        assert "interval" in params
        assert "datatype" in params
        assert params["interval"] == "monthly"
        assert params["datatype"] == "csv"

    def test_transform_request_params_all_options(self):
        """Test parameter transformation with all options."""
        request = EnergyCommodityRequest(
            commodity_type="natural_gas", interval="daily", datatype="json"
        )
        params = transform_request_params(request)
        assert params["interval"] == "daily"
        assert params["datatype"] == "json"


class TestValidationLogic:
    """Test validation logic."""

    def test_validate_routing_success(self):
        """Test that valid requests pass routing validation."""
        request = EnergyCommodityRequest(commodity_type="wti")
        validate_routing(request)  # Should not raise

    def test_validate_routing_all_commodities(self):
        """Test routing validation for all commodity types."""
        for commodity_type in ["wti", "brent", "natural_gas"]:
            request = EnergyCommodityRequest(commodity_type=commodity_type)
            validate_routing(request)  # Should not raise


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_commodity_type(self):
        """Test that empty string commodity type is rejected."""
        with pytest.raises(ValidationError):
            EnergyCommodityRequest(commodity_type="")

    def test_none_commodity_type(self):
        """Test that None commodity type is rejected."""
        with pytest.raises(ValidationError):
            EnergyCommodityRequest(commodity_type=None)

    def test_case_sensitive_commodity_type(self):
        """Test that commodity_type is case-sensitive."""
        with pytest.raises(ValidationError):
            EnergyCommodityRequest(commodity_type="WTI")  # uppercase should fail

    def test_case_sensitive_interval(self):
        """Test that interval is case-sensitive."""
        with pytest.raises(ValidationError):
            EnergyCommodityRequest(commodity_type="wti", interval="DAILY")

    def test_whitespace_commodity_type(self):
        """Test that whitespace in commodity_type is rejected."""
        with pytest.raises(ValidationError):
            EnergyCommodityRequest(commodity_type=" wti ")
