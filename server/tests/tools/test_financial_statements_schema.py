"""
Unit tests for FinancialStatementsRequest schema validation.

Tests cover:
- Parameter validation for each statement_type
- Output flag validation (force_inline/force_file)
- Invalid parameter combinations
- Edge cases and error messages
- Parameterized tests for efficiency
"""

import pytest
from pydantic import ValidationError

from src.tools.financial_statements_schema import FinancialStatementsRequest


class TestStatementTypes:
    """Test all financial statement types."""

    @pytest.mark.parametrize(
        "statement_type",
        ["income_statement", "balance_sheet", "cash_flow"],
    )
    def test_valid_statement_type(self, statement_type):
        """Test valid requests for all statement types."""
        request = FinancialStatementsRequest(
            statement_type=statement_type,
            symbol="IBM",
        )
        assert request.statement_type == statement_type
        assert request.symbol == "IBM"
        assert request.force_inline is False
        assert request.force_file is False

    def test_invalid_statement_type(self):
        """Test that invalid statement types are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            FinancialStatementsRequest(
                statement_type="invalid_statement",
                symbol="IBM",
            )
        errors = exc_info.value.errors()
        assert any("statement_type" in str(err) for err in errors)

    @pytest.mark.parametrize(
        "statement_type,symbol",
        [
            ("income_statement", "AAPL"),
            ("balance_sheet", "MSFT"),
            ("cash_flow", "GOOGL"),
            ("income_statement", "TSLA"),
            ("balance_sheet", "AMZN"),
        ],
    )
    def test_various_symbols(self, statement_type, symbol):
        """Test various symbols with different statement types."""
        request = FinancialStatementsRequest(
            statement_type=statement_type,
            symbol=symbol,
        )
        assert request.symbol == symbol
        assert request.statement_type == statement_type


class TestSymbolValidation:
    """Test symbol parameter validation."""

    def test_missing_symbol(self):
        """Test that missing symbol is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            FinancialStatementsRequest(
                statement_type="income_statement",
            )
        errors = exc_info.value.errors()
        assert any("symbol" in str(err["loc"]) for err in errors)

    # Note: Empty symbol is technically valid in Pydantic, router will validate

    @pytest.mark.parametrize(
        "symbol",
        ["IBM", "AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA"],
    )
    def test_valid_symbols(self, symbol):
        """Test various valid stock symbols."""
        request = FinancialStatementsRequest(
            statement_type="income_statement",
            symbol=symbol,
        )
        assert request.symbol == symbol


class TestOutputFlags:
    """Test force_inline and force_file parameter validation."""

    def test_force_inline_only(self):
        """Test force_inline=True without force_file."""
        request = FinancialStatementsRequest(
            statement_type="income_statement",
            symbol="IBM",
            force_inline=True,
        )
        assert request.force_inline is True
        assert request.force_file is False

    def test_force_file_only(self):
        """Test force_file=True without force_inline."""
        request = FinancialStatementsRequest(
            statement_type="income_statement",
            symbol="IBM",
            force_file=True,
        )
        assert request.force_file is True
        assert request.force_inline is False

    def test_both_flags_false(self):
        """Test default behavior with both flags False."""
        request = FinancialStatementsRequest(
            statement_type="income_statement",
            symbol="IBM",
        )
        assert request.force_inline is False
        assert request.force_file is False

    def test_both_flags_true_rejected(self):
        """Test that setting both force_inline and force_file is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            FinancialStatementsRequest(
                statement_type="income_statement",
                symbol="IBM",
                force_inline=True,
                force_file=True,
            )
        errors = exc_info.value.errors()
        assert any("mutually exclusive" in str(err) for err in errors)

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
            request = FinancialStatementsRequest(
                statement_type="income_statement",
                symbol="IBM",
                force_inline=force_inline,
                force_file=force_file,
            )
            assert request.force_inline == force_inline
            assert request.force_file == force_file
        else:
            with pytest.raises(ValidationError):
                FinancialStatementsRequest(
                    statement_type="income_statement",
                    symbol="IBM",
                    force_inline=force_inline,
                    force_file=force_file,
                )


class TestIncomeStatement:
    """Test income_statement specific behavior."""

    def test_basic_income_statement(self):
        """Test basic income statement request."""
        request = FinancialStatementsRequest(
            statement_type="income_statement",
            symbol="IBM",
        )
        assert request.statement_type == "income_statement"

    def test_income_statement_with_force_inline(self):
        """Test income statement with force_inline."""
        request = FinancialStatementsRequest(
            statement_type="income_statement",
            symbol="AAPL",
            force_inline=True,
        )
        assert request.force_inline is True

    def test_income_statement_with_force_file(self):
        """Test income statement with force_file."""
        request = FinancialStatementsRequest(
            statement_type="income_statement",
            symbol="MSFT",
            force_file=True,
        )
        assert request.force_file is True


class TestBalanceSheet:
    """Test balance_sheet specific behavior."""

    def test_basic_balance_sheet(self):
        """Test basic balance sheet request."""
        request = FinancialStatementsRequest(
            statement_type="balance_sheet",
            symbol="GOOGL",
        )
        assert request.statement_type == "balance_sheet"

    def test_balance_sheet_with_force_inline(self):
        """Test balance sheet with force_inline."""
        request = FinancialStatementsRequest(
            statement_type="balance_sheet",
            symbol="TSLA",
            force_inline=True,
        )
        assert request.force_inline is True

    def test_balance_sheet_with_force_file(self):
        """Test balance sheet with force_file."""
        request = FinancialStatementsRequest(
            statement_type="balance_sheet",
            symbol="AMZN",
            force_file=True,
        )
        assert request.force_file is True


class TestCashFlow:
    """Test cash_flow specific behavior."""

    def test_basic_cash_flow(self):
        """Test basic cash flow request."""
        request = FinancialStatementsRequest(
            statement_type="cash_flow",
            symbol="META",
        )
        assert request.statement_type == "cash_flow"

    def test_cash_flow_with_force_inline(self):
        """Test cash flow with force_inline."""
        request = FinancialStatementsRequest(
            statement_type="cash_flow",
            symbol="NVDA",
            force_inline=True,
        )
        assert request.force_inline is True

    def test_cash_flow_with_force_file(self):
        """Test cash flow with force_file."""
        request = FinancialStatementsRequest(
            statement_type="cash_flow",
            symbol="NFLX",
            force_file=True,
        )
        assert request.force_file is True


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_lowercase_symbol(self):
        """Test that lowercase symbols are accepted."""
        request = FinancialStatementsRequest(
            statement_type="income_statement",
            symbol="ibm",
        )
        assert request.symbol == "ibm"

    def test_mixed_case_symbol(self):
        """Test that mixed case symbols are accepted."""
        request = FinancialStatementsRequest(
            statement_type="income_statement",
            symbol="IbM",
        )
        assert request.symbol == "IbM"

    @pytest.mark.parametrize(
        "statement_type",
        ["income_statement", "balance_sheet", "cash_flow"],
    )
    def test_all_statements_default_output_flags(self, statement_type):
        """Test that all statement types have False output flags by default."""
        request = FinancialStatementsRequest(
            statement_type=statement_type,
            symbol="IBM",
        )
        assert request.force_inline is False
        assert request.force_file is False

    def test_error_message_quality_for_invalid_statement(self):
        """Test that error messages are helpful for invalid statement types."""
        with pytest.raises(ValidationError) as exc_info:
            FinancialStatementsRequest(
                statement_type="profit_loss",  # Common mistake
                symbol="IBM",
            )
        error_str = str(exc_info.value)
        # Should mention valid options
        assert "statement_type" in error_str.lower()

    def test_error_message_quality_for_mutual_exclusion(self):
        """Test that error messages are helpful for mutually exclusive flags."""
        with pytest.raises(ValidationError) as exc_info:
            FinancialStatementsRequest(
                statement_type="income_statement",
                symbol="IBM",
                force_inline=True,
                force_file=True,
            )
        error_str = str(exc_info.value)
        assert "mutually exclusive" in error_str.lower()


class TestModelValidation:
    """Test overall model validation behavior."""

    def test_model_fields_are_set_correctly(self):
        """Test that all model fields are set correctly."""
        request = FinancialStatementsRequest(
            statement_type="income_statement",
            symbol="IBM",
            force_inline=True,
        )
        assert hasattr(request, "statement_type")
        assert hasattr(request, "symbol")
        assert hasattr(request, "force_inline")
        assert hasattr(request, "force_file")

    # Note: Pydantic v2 models are mutable by default unless configured otherwise

    @pytest.mark.parametrize(
        "statement_type,symbol,force_inline,force_file",
        [
            ("income_statement", "IBM", False, False),
            ("balance_sheet", "AAPL", True, False),
            ("cash_flow", "MSFT", False, True),
            ("income_statement", "GOOGL", False, False),
            ("balance_sheet", "TSLA", True, False),
        ],
    )
    def test_comprehensive_valid_combinations(
        self, statement_type, symbol, force_inline, force_file
    ):
        """Test various valid parameter combinations."""
        request = FinancialStatementsRequest(
            statement_type=statement_type,
            symbol=symbol,
            force_inline=force_inline,
            force_file=force_file,
        )
        assert request.statement_type == statement_type
        assert request.symbol == symbol
        assert request.force_inline == force_inline
        assert request.force_file == force_file
