"""
Unit tests for CompanyDataRequest schema validation.

Tests cover:
- Parameter validation for each data_type
- Conditional datatype parameter handling
- Output flag validation (force_inline/force_file)
- Invalid parameter combinations
- Edge cases and error messages
- Parameterized tests for efficiency
"""

import pytest
from pydantic import ValidationError

from src.tools.company_data_schema import CompanyDataRequest


class TestDataTypes:
    """Test all company data types."""

    @pytest.mark.parametrize(
        "data_type",
        ["company_overview", "etf_profile", "dividends", "splits", "earnings"],
    )
    def test_valid_data_type(self, data_type):
        """Test valid requests for all data types."""
        request = CompanyDataRequest(
            data_type=data_type,
            symbol="IBM",
        )
        assert request.data_type == data_type
        assert request.symbol == "IBM"
        assert request.datatype == "json"  # Default
        assert request.force_inline is False
        assert request.force_file is False

    def test_invalid_data_type(self):
        """Test that invalid data types are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CompanyDataRequest(
                data_type="invalid_data",
                symbol="IBM",
            )
        errors = exc_info.value.errors()
        assert any("data_type" in str(err) for err in errors)

    @pytest.mark.parametrize(
        "data_type,symbol",
        [
            ("company_overview", "AAPL"),
            ("etf_profile", "QQQ"),
            ("dividends", "MSFT"),
            ("splits", "TSLA"),
            ("earnings", "GOOGL"),
        ],
    )
    def test_various_symbols(self, data_type, symbol):
        """Test various symbols with different data types."""
        request = CompanyDataRequest(
            data_type=data_type,
            symbol=symbol,
        )
        assert request.symbol == symbol
        assert request.data_type == data_type


class TestDatatypeParameter:
    """Test datatype parameter validation."""

    @pytest.mark.parametrize(
        "data_type",
        ["dividends", "splits"],
    )
    def test_datatype_json_for_dividends_splits(self, data_type):
        """Test datatype=json for dividends and splits."""
        request = CompanyDataRequest(
            data_type=data_type,
            symbol="IBM",
            datatype="json",
        )
        assert request.datatype == "json"

    @pytest.mark.parametrize(
        "data_type",
        ["dividends", "splits"],
    )
    def test_datatype_csv_for_dividends_splits(self, data_type):
        """Test datatype=csv for dividends and splits."""
        request = CompanyDataRequest(
            data_type=data_type,
            symbol="IBM",
            datatype="csv",
        )
        assert request.datatype == "csv"

    @pytest.mark.parametrize(
        "data_type",
        ["company_overview", "etf_profile", "earnings"],
    )
    def test_datatype_ignored_for_json_only_endpoints(self, data_type):
        """Test that datatype is accepted but ignored for JSON-only endpoints."""
        # These endpoints always return JSON, but we don't reject the parameter
        request = CompanyDataRequest(
            data_type=data_type,
            symbol="IBM",
            datatype="csv",  # Will be ignored in router
        )
        assert request.datatype == "csv"  # Accepted in schema

    def test_invalid_datatype(self):
        """Test that invalid datatype values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CompanyDataRequest(
                data_type="dividends",
                symbol="IBM",
                datatype="xml",  # Invalid
            )
        errors = exc_info.value.errors()
        assert any("datatype" in str(err) for err in errors)

    def test_default_datatype_is_json(self):
        """Test that default datatype is json."""
        request = CompanyDataRequest(
            data_type="dividends",
            symbol="IBM",
        )
        assert request.datatype == "json"


class TestSymbolValidation:
    """Test symbol parameter validation."""

    def test_missing_symbol(self):
        """Test that missing symbol is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CompanyDataRequest(
                data_type="company_overview",
            )
        errors = exc_info.value.errors()
        assert any("symbol" in str(err["loc"]) for err in errors)

    @pytest.mark.parametrize(
        "symbol",
        ["IBM", "AAPL", "MSFT", "GOOGL", "TSLA", "QQQ", "SPY", "VTI"],
    )
    def test_valid_symbols(self, symbol):
        """Test various valid stock and ETF symbols."""
        request = CompanyDataRequest(
            data_type="company_overview",
            symbol=symbol,
        )
        assert request.symbol == symbol


class TestOutputFlags:
    """Test force_inline and force_file parameter validation."""

    def test_force_inline_only(self):
        """Test force_inline=True without force_file."""
        request = CompanyDataRequest(
            data_type="company_overview",
            symbol="IBM",
            force_inline=True,
        )
        assert request.force_inline is True
        assert request.force_file is False

    def test_force_file_only(self):
        """Test force_file=True without force_inline."""
        request = CompanyDataRequest(
            data_type="company_overview",
            symbol="IBM",
            force_file=True,
        )
        assert request.force_file is True
        assert request.force_inline is False

    def test_both_flags_true_rejected(self):
        """Test that setting both force_inline and force_file is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CompanyDataRequest(
                data_type="company_overview",
                symbol="IBM",
                force_inline=True,
                force_file=True,
            )
        errors = exc_info.value.errors()
        assert any("mutually exclusive" in str(err) for err in errors)


class TestCompanyOverview:
    """Test company_overview specific behavior."""

    def test_basic_company_overview(self):
        """Test basic company overview request."""
        request = CompanyDataRequest(
            data_type="company_overview",
            symbol="IBM",
        )
        assert request.data_type == "company_overview"

    def test_company_overview_with_various_symbols(self):
        """Test company overview with various stock symbols."""
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
        for symbol in symbols:
            request = CompanyDataRequest(
                data_type="company_overview",
                symbol=symbol,
            )
            assert request.symbol == symbol


class TestETFProfile:
    """Test etf_profile specific behavior."""

    def test_basic_etf_profile(self):
        """Test basic ETF profile request."""
        request = CompanyDataRequest(
            data_type="etf_profile",
            symbol="QQQ",
        )
        assert request.data_type == "etf_profile"

    @pytest.mark.parametrize(
        "etf_symbol",
        ["QQQ", "SPY", "VTI", "VOO", "IWM"],
    )
    def test_etf_profile_with_various_etfs(self, etf_symbol):
        """Test ETF profile with various ETF symbols."""
        request = CompanyDataRequest(
            data_type="etf_profile",
            symbol=etf_symbol,
        )
        assert request.symbol == etf_symbol


class TestDividends:
    """Test dividends specific behavior."""

    def test_dividends_json(self):
        """Test dividends request with JSON output."""
        request = CompanyDataRequest(
            data_type="dividends",
            symbol="IBM",
            datatype="json",
        )
        assert request.datatype == "json"

    def test_dividends_csv(self):
        """Test dividends request with CSV output."""
        request = CompanyDataRequest(
            data_type="dividends",
            symbol="AAPL",
            datatype="csv",
        )
        assert request.datatype == "csv"

    def test_dividends_default_json(self):
        """Test dividends defaults to JSON."""
        request = CompanyDataRequest(
            data_type="dividends",
            symbol="MSFT",
        )
        assert request.datatype == "json"


class TestSplits:
    """Test splits specific behavior."""

    def test_splits_json(self):
        """Test splits request with JSON output."""
        request = CompanyDataRequest(
            data_type="splits",
            symbol="TSLA",
            datatype="json",
        )
        assert request.datatype == "json"

    def test_splits_csv(self):
        """Test splits request with CSV output."""
        request = CompanyDataRequest(
            data_type="splits",
            symbol="AAPL",
            datatype="csv",
        )
        assert request.datatype == "csv"

    def test_splits_default_json(self):
        """Test splits defaults to JSON."""
        request = CompanyDataRequest(
            data_type="splits",
            symbol="GOOGL",
        )
        assert request.datatype == "json"


class TestEarnings:
    """Test earnings specific behavior."""

    def test_basic_earnings(self):
        """Test basic earnings request."""
        request = CompanyDataRequest(
            data_type="earnings",
            symbol="MSFT",
        )
        assert request.data_type == "earnings"

    def test_earnings_with_various_symbols(self):
        """Test earnings with various stock symbols."""
        symbols = ["IBM", "AAPL", "GOOGL", "AMZN", "META"]
        for symbol in symbols:
            request = CompanyDataRequest(
                data_type="earnings",
                symbol=symbol,
            )
            assert request.symbol == symbol


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_lowercase_symbol(self):
        """Test that lowercase symbols are accepted."""
        request = CompanyDataRequest(
            data_type="company_overview",
            symbol="ibm",
        )
        assert request.symbol == "ibm"

    @pytest.mark.parametrize(
        "data_type",
        ["company_overview", "etf_profile", "dividends", "splits", "earnings"],
    )
    def test_all_data_types_default_output_flags(self, data_type):
        """Test that all data types have False output flags by default."""
        request = CompanyDataRequest(
            data_type=data_type,
            symbol="IBM",
        )
        assert request.force_inline is False
        assert request.force_file is False

    def test_error_message_quality_for_invalid_data_type(self):
        """Test that error messages are helpful for invalid data types."""
        with pytest.raises(ValidationError) as exc_info:
            CompanyDataRequest(
                data_type="financial_ratios",  # Not a valid type
                symbol="IBM",
            )
        error_str = str(exc_info.value)
        assert "data_type" in error_str.lower()


class TestComprehensiveCombinations:
    """Test comprehensive parameter combinations."""

    @pytest.mark.parametrize(
        "data_type,symbol,datatype,force_inline,force_file",
        [
            ("company_overview", "IBM", "json", False, False),
            ("etf_profile", "QQQ", "json", True, False),
            ("dividends", "AAPL", "csv", False, True),
            ("splits", "TSLA", "json", False, False),
            ("earnings", "MSFT", "json", True, False),
            ("dividends", "GOOGL", "json", False, False),
            ("splits", "AMZN", "csv", False, True),
        ],
    )
    def test_valid_combinations(self, data_type, symbol, datatype, force_inline, force_file):
        """Test various valid parameter combinations."""
        request = CompanyDataRequest(
            data_type=data_type,
            symbol=symbol,
            datatype=datatype,
            force_inline=force_inline,
            force_file=force_file,
        )
        assert request.data_type == data_type
        assert request.symbol == symbol
        assert request.datatype == datatype
        assert request.force_inline == force_inline
        assert request.force_file == force_file
