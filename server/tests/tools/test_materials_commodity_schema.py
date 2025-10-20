"""
Unit tests for MaterialsCommodityRequest schema validation.

Tests cover:
- All 8 materials commodity types
- All interval options (monthly, quarterly, annual)
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

from src.tools.materials_commodity_router import (
    get_api_function_name,
    route_request,
    transform_request_params,
    validate_routing,
)
from src.tools.materials_commodity_schema import MaterialsCommodityRequest


class TestCommodityTypes:
    """Test all materials commodity types."""

    @pytest.mark.parametrize(
        "commodity_type,expected_function",
        [
            ("copper", "COPPER"),
            ("aluminum", "ALUMINUM"),
            ("wheat", "WHEAT"),
            ("corn", "CORN"),
            ("cotton", "COTTON"),
            ("sugar", "SUGAR"),
            ("coffee", "COFFEE"),
            ("all_commodities", "ALL_COMMODITIES"),
        ],
    )
    def test_all_valid_commodity_types(self, commodity_type, expected_function):
        """Test that all 8 commodity types are recognized."""
        request = MaterialsCommodityRequest(commodity_type=commodity_type, interval="monthly")
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
            MaterialsCommodityRequest(commodity_type="invalid_commodity")

        errors = exc_info.value.errors()
        assert any("commodity_type" in str(err) for err in errors)


class TestIntervals:
    """Test interval validation for materials commodities."""

    @pytest.mark.parametrize("interval", ["monthly", "quarterly", "annual"])
    def test_all_valid_intervals(self, interval):
        """Test all valid intervals for materials commodities."""
        request = MaterialsCommodityRequest(commodity_type="copper", interval=interval)
        assert request.interval == interval

    @pytest.mark.parametrize(
        "commodity_type",
        ["copper", "aluminum", "wheat", "corn", "cotton", "sugar", "coffee", "all_commodities"],
    )
    @pytest.mark.parametrize("interval", ["monthly", "quarterly", "annual"])
    def test_all_commodities_support_all_intervals(self, commodity_type, interval):
        """Test that all materials commodities support all intervals."""
        request = MaterialsCommodityRequest(commodity_type=commodity_type, interval=interval)
        assert request.commodity_type == commodity_type
        assert request.interval == interval

    def test_default_interval(self):
        """Test that default interval is monthly."""
        request = MaterialsCommodityRequest(commodity_type="copper")
        assert request.interval == "monthly"

    def test_invalid_interval(self):
        """Test that invalid intervals are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MaterialsCommodityRequest(commodity_type="copper", interval="invalid")

        errors = exc_info.value.errors()
        assert any("interval" in str(err) for err in errors)

    def test_energy_intervals_not_valid(self):
        """Test that energy commodity intervals (daily, weekly) are not valid."""
        for interval in ["daily", "weekly"]:
            with pytest.raises(ValidationError):
                MaterialsCommodityRequest(commodity_type="copper", interval=interval)


class TestMetalCommodities:
    """Test metal commodity types (copper, aluminum)."""

    @pytest.mark.parametrize("interval", ["monthly", "quarterly", "annual"])
    def test_copper_all_intervals(self, interval):
        """Test copper with all valid intervals."""
        request = MaterialsCommodityRequest(commodity_type="copper", interval=interval)
        assert request.commodity_type == "copper"
        assert request.interval == interval

    @pytest.mark.parametrize("interval", ["monthly", "quarterly", "annual"])
    def test_aluminum_all_intervals(self, interval):
        """Test aluminum with all valid intervals."""
        request = MaterialsCommodityRequest(commodity_type="aluminum", interval=interval)
        assert request.commodity_type == "aluminum"
        assert request.interval == interval

    def test_copper_with_json_datatype(self):
        """Test copper with JSON output format."""
        request = MaterialsCommodityRequest(
            commodity_type="copper", interval="quarterly", datatype="json"
        )
        assert request.datatype == "json"

    def test_copper_default_parameters(self):
        """Test copper with default parameters."""
        request = MaterialsCommodityRequest(commodity_type="copper")
        assert request.commodity_type == "copper"
        assert request.interval == "monthly"
        assert request.datatype == "csv"
        assert request.force_inline is False
        assert request.force_file is False


class TestGrainCommodities:
    """Test grain commodity types (wheat, corn)."""

    @pytest.mark.parametrize("interval", ["monthly", "quarterly", "annual"])
    def test_wheat_all_intervals(self, interval):
        """Test wheat with all valid intervals."""
        request = MaterialsCommodityRequest(commodity_type="wheat", interval=interval)
        assert request.commodity_type == "wheat"
        assert request.interval == interval

    @pytest.mark.parametrize("interval", ["monthly", "quarterly", "annual"])
    def test_corn_all_intervals(self, interval):
        """Test corn with all valid intervals."""
        request = MaterialsCommodityRequest(commodity_type="corn", interval=interval)
        assert request.commodity_type == "corn"
        assert request.interval == interval

    def test_wheat_with_json_datatype(self):
        """Test wheat with JSON output format."""
        request = MaterialsCommodityRequest(
            commodity_type="wheat", interval="annual", datatype="json"
        )
        assert request.datatype == "json"


class TestAgriculturalCommodities:
    """Test agricultural commodity types (cotton, sugar, coffee)."""

    @pytest.mark.parametrize("interval", ["monthly", "quarterly", "annual"])
    def test_cotton_all_intervals(self, interval):
        """Test cotton with all valid intervals."""
        request = MaterialsCommodityRequest(commodity_type="cotton", interval=interval)
        assert request.commodity_type == "cotton"
        assert request.interval == interval

    @pytest.mark.parametrize("interval", ["monthly", "quarterly", "annual"])
    def test_sugar_all_intervals(self, interval):
        """Test sugar with all valid intervals."""
        request = MaterialsCommodityRequest(commodity_type="sugar", interval=interval)
        assert request.commodity_type == "sugar"
        assert request.interval == interval

    @pytest.mark.parametrize("interval", ["monthly", "quarterly", "annual"])
    def test_coffee_all_intervals(self, interval):
        """Test coffee with all valid intervals."""
        request = MaterialsCommodityRequest(commodity_type="coffee", interval=interval)
        assert request.commodity_type == "coffee"
        assert request.interval == interval

    def test_cotton_with_json_datatype(self):
        """Test cotton with JSON output format."""
        request = MaterialsCommodityRequest(
            commodity_type="cotton", interval="quarterly", datatype="json"
        )
        assert request.datatype == "json"


class TestAllCommoditiesIndex:
    """Test all_commodities index specifically."""

    @pytest.mark.parametrize("interval", ["monthly", "quarterly", "annual"])
    def test_all_commodities_all_intervals(self, interval):
        """Test all_commodities with all valid intervals."""
        request = MaterialsCommodityRequest(commodity_type="all_commodities", interval=interval)
        assert request.commodity_type == "all_commodities"
        assert request.interval == interval

    def test_all_commodities_with_json_datatype(self):
        """Test all_commodities with JSON output format."""
        request = MaterialsCommodityRequest(
            commodity_type="all_commodities", interval="annual", datatype="json"
        )
        assert request.datatype == "json"

    def test_all_commodities_default_parameters(self):
        """Test all_commodities with default parameters."""
        request = MaterialsCommodityRequest(commodity_type="all_commodities")
        assert request.commodity_type == "all_commodities"
        assert request.interval == "monthly"
        assert request.datatype == "csv"


class TestDatatypeValidation:
    """Test datatype parameter validation."""

    @pytest.mark.parametrize("datatype", ["json", "csv"])
    def test_valid_datatypes(self, datatype):
        """Test all valid datatype options."""
        request = MaterialsCommodityRequest(commodity_type="copper", datatype=datatype)
        assert request.datatype == datatype

    def test_default_datatype(self):
        """Test that default datatype is csv."""
        request = MaterialsCommodityRequest(commodity_type="copper")
        assert request.datatype == "csv"

    def test_invalid_datatype(self):
        """Test that invalid datatypes are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MaterialsCommodityRequest(commodity_type="copper", datatype="invalid")

        errors = exc_info.value.errors()
        assert any("datatype" in str(err) for err in errors)


class TestOutputFlags:
    """Test output control flags validation."""

    def test_force_inline_flag(self):
        """Test force_inline flag can be set."""
        request = MaterialsCommodityRequest(commodity_type="copper", force_inline=True)
        assert request.force_inline is True
        assert request.force_file is False

    def test_force_file_flag(self):
        """Test force_file flag can be set."""
        request = MaterialsCommodityRequest(commodity_type="copper", force_file=True)
        assert request.force_file is True
        assert request.force_inline is False

    def test_mutually_exclusive_flags(self):
        """Test that force_inline and force_file are mutually exclusive."""
        with pytest.raises(ValidationError) as exc_info:
            MaterialsCommodityRequest(commodity_type="copper", force_inline=True, force_file=True)

        assert "mutually exclusive" in str(exc_info.value).lower()

    def test_default_output_flags(self):
        """Test that output flags default to False."""
        request = MaterialsCommodityRequest(commodity_type="copper")
        assert request.force_inline is False
        assert request.force_file is False


class TestRouting:
    """Test routing logic for materials commodities."""

    @pytest.mark.parametrize(
        "commodity_type,expected_function",
        [
            ("copper", "COPPER"),
            ("aluminum", "ALUMINUM"),
            ("wheat", "WHEAT"),
            ("corn", "CORN"),
            ("cotton", "COTTON"),
            ("sugar", "SUGAR"),
            ("coffee", "COFFEE"),
            ("all_commodities", "ALL_COMMODITIES"),
        ],
    )
    def test_commodity_type_routing(self, commodity_type, expected_function):
        """Test that commodity types route to correct API functions."""
        request = MaterialsCommodityRequest(commodity_type=commodity_type)
        function_name, params = route_request(request)
        assert function_name == expected_function

    @pytest.mark.parametrize("interval", ["monthly", "quarterly", "annual"])
    def test_interval_routing(self, interval):
        """Test that interval parameter is correctly routed."""
        request = MaterialsCommodityRequest(commodity_type="copper", interval=interval)
        function_name, params = route_request(request)
        assert params["interval"] == interval

    @pytest.mark.parametrize("datatype", ["json", "csv"])
    def test_datatype_routing(self, datatype):
        """Test that datatype parameter is correctly routed."""
        request = MaterialsCommodityRequest(commodity_type="copper", datatype=datatype)
        function_name, params = route_request(request)
        assert params["datatype"] == datatype

    def test_complete_routing(self):
        """Test complete routing with all parameters."""
        request = MaterialsCommodityRequest(
            commodity_type="wheat", interval="quarterly", datatype="json"
        )
        function_name, params = route_request(request)
        assert function_name == "WHEAT"
        assert params["interval"] == "quarterly"
        assert params["datatype"] == "json"

    def test_invalid_commodity_type_routing(self):
        """Test that invalid commodity types raise ValueError."""
        # This should not happen due to Pydantic validation, but test defense-in-depth
        # We can't create an invalid request through normal means, so test the function directly
        with pytest.raises(ValueError):
            get_api_function_name("invalid_commodity")


class TestParameterTransformation:
    """Test parameter transformation logic."""

    def test_transform_request_params_basic(self):
        """Test basic parameter transformation."""
        request = MaterialsCommodityRequest(commodity_type="copper")
        params = transform_request_params(request)
        assert "interval" in params
        assert "datatype" in params
        assert params["interval"] == "monthly"
        assert params["datatype"] == "csv"

    def test_transform_request_params_all_options(self):
        """Test parameter transformation with all options."""
        request = MaterialsCommodityRequest(
            commodity_type="wheat", interval="annual", datatype="json"
        )
        params = transform_request_params(request)
        assert params["interval"] == "annual"
        assert params["datatype"] == "json"


class TestValidationLogic:
    """Test validation logic."""

    def test_validate_routing_success(self):
        """Test that valid requests pass routing validation."""
        request = MaterialsCommodityRequest(commodity_type="copper")
        validate_routing(request)  # Should not raise

    def test_validate_routing_all_commodities(self):
        """Test routing validation for all commodity types."""
        for commodity_type in [
            "copper",
            "aluminum",
            "wheat",
            "corn",
            "cotton",
            "sugar",
            "coffee",
            "all_commodities",
        ]:
            request = MaterialsCommodityRequest(commodity_type=commodity_type)
            validate_routing(request)  # Should not raise


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_commodity_type(self):
        """Test that empty string commodity type is rejected."""
        with pytest.raises(ValidationError):
            MaterialsCommodityRequest(commodity_type="")

    def test_none_commodity_type(self):
        """Test that None commodity type is rejected."""
        with pytest.raises(ValidationError):
            MaterialsCommodityRequest(commodity_type=None)

    def test_case_sensitive_commodity_type(self):
        """Test that commodity_type is case-sensitive."""
        with pytest.raises(ValidationError):
            MaterialsCommodityRequest(commodity_type="COPPER")  # uppercase should fail

    def test_case_sensitive_interval(self):
        """Test that interval is case-sensitive."""
        with pytest.raises(ValidationError):
            MaterialsCommodityRequest(commodity_type="copper", interval="MONTHLY")

    def test_whitespace_commodity_type(self):
        """Test that whitespace in commodity_type is rejected."""
        with pytest.raises(ValidationError):
            MaterialsCommodityRequest(commodity_type=" copper ")

    def test_special_commodity_name_all_commodities(self):
        """Test that all_commodities (with underscore) is valid."""
        request = MaterialsCommodityRequest(commodity_type="all_commodities")
        assert request.commodity_type == "all_commodities"


class TestCrossValidation:
    """Test cross-validation between different parameter combinations."""

    @pytest.mark.parametrize("commodity_type", ["copper", "wheat", "coffee"])
    @pytest.mark.parametrize("interval", ["monthly", "quarterly", "annual"])
    @pytest.mark.parametrize("datatype", ["json", "csv"])
    def test_all_valid_combinations(self, commodity_type, interval, datatype):
        """Test all valid parameter combinations work together."""
        request = MaterialsCommodityRequest(
            commodity_type=commodity_type, interval=interval, datatype=datatype
        )
        assert request.commodity_type == commodity_type
        assert request.interval == interval
        assert request.datatype == datatype

        # Also verify routing works
        function_name, params = route_request(request)
        assert function_name is not None
        assert params["interval"] == interval
        assert params["datatype"] == datatype
