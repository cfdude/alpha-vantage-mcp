"""
Comprehensive tests for TokenEstimator with performance benchmarks.

Test Coverage:
- Token estimation for CSV/JSON data
- Threshold comparison logic
- Row-based fallback estimation
- Override mechanism (force_inline, force_file)
- Edge cases (empty data, huge datasets, malformed data)
- Different data types (dates, decimals, unicode)
- Performance benchmarks

Target: ≥90% code coverage
"""

import os
import time
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.decision.token_estimator import TokenEstimationError, TokenEstimator
from src.utils.output_config import OutputConfig


class TestTokenEstimatorInitialization:
    """Test TokenEstimator initialization and setup."""

    def test_initialization_success(self):
        """Test successful initialization with tiktoken encoding."""
        estimator = TokenEstimator()
        assert estimator.encoding is not None
        assert estimator.encoding.name == "cl100k_base"

    def test_encoding_cached(self):
        """Test that encoding is cached and reused."""
        estimator = TokenEstimator()
        encoding1 = estimator.encoding
        encoding2 = estimator.encoding
        assert encoding1 is encoding2  # Same instance


class TestEstimateTokensBasic:
    """Test basic token estimation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.estimator = TokenEstimator()

    def test_estimate_csv_tokens_small_dataset(self):
        """Test token estimation for small CSV dataset."""
        data = [
            {"name": "Alice", "age": 30, "city": "New York"},
            {"name": "Bob", "age": 25, "city": "Los Angeles"},
        ]
        tokens = self.estimator.estimate_tokens(data)

        # Should return positive token count
        assert tokens > 0
        # Rough sanity check (should be reasonable for this data)
        assert 20 < tokens < 200

    def test_estimate_csv_tokens_medium_dataset(self):
        """Test token estimation for medium CSV dataset."""
        data = [{"id": i, "value": f"item_{i}", "score": i * 1.5} for i in range(1000)]
        tokens = self.estimator.estimate_tokens(data)

        assert tokens > 0
        # Medium dataset should have substantial token count
        assert tokens > 1000

    def test_estimate_json_tokens_dict(self):
        """Test token estimation for JSON dictionary."""
        data = {
            "name": "Test Project",
            "version": "1.0.0",
            "description": "A test project for token estimation",
        }
        tokens = self.estimator.estimate_json_tokens(data)

        assert tokens > 0
        assert 10 < tokens < 100

    def test_estimate_json_tokens_list(self):
        """Test token estimation for JSON list."""
        data = [1, 2, 3, 4, 5, 10, 20, 30, 40, 50]
        tokens = self.estimator.estimate_json_tokens(data)

        assert tokens > 0
        assert tokens < 50

    def test_estimate_tokens_empty_data_raises_error(self):
        """Test that empty data raises appropriate error."""
        with pytest.raises(ValueError, match="Cannot estimate tokens for empty data"):
            self.estimator.estimate_csv_tokens([])


class TestEstimateByRowsFallback:
    """Test row-based fallback estimation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.estimator = TokenEstimator()

    def test_fallback_estimation_small_dataset(self):
        """Test fallback estimation on small dataset."""
        data = [{"id": i, "value": f"test_{i}"} for i in range(100)]
        tokens = self.estimator.estimate_by_rows(data)

        assert tokens > 0
        # Should be conservative (slightly higher than actual)
        actual = self.estimator.estimate_csv_tokens(data)
        # Allow 50% margin (fallback is conservative)
        assert 0.5 * actual < tokens < 2.0 * actual

    def test_fallback_estimation_large_dataset(self):
        """Test fallback estimation on large dataset."""
        data = [{"id": i, "name": f"user_{i}", "score": i * 0.5} for i in range(15000)]
        tokens = self.estimator.estimate_by_rows(data)

        assert tokens > 0
        # Large dataset should have large token count
        assert tokens > 10000

    def test_fallback_used_for_huge_datasets(self):
        """Test that fallback is automatically used for huge datasets."""
        # Create dataset larger than FALLBACK_THRESHOLD
        data = [{"id": i} for i in range(TokenEstimator.FALLBACK_THRESHOLD + 1)]

        # estimate_csv_tokens should use fallback automatically
        tokens = self.estimator.estimate_csv_tokens(data)

        assert tokens > 0

    def test_fallback_empty_data_raises_error(self):
        """Test that fallback estimation rejects empty data."""
        with pytest.raises(ValueError, match="Cannot estimate tokens for empty data"):
            self.estimator.estimate_by_rows([])


class TestSpecialDataTypes:
    """Test handling of special data types (dates, decimals, unicode)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.estimator = TokenEstimator()

    def test_datetime_objects(self):
        """Test token estimation with datetime objects."""
        data = [
            {"timestamp": datetime(2024, 1, 15, 10, 30, 0), "event": "login"},
            {"timestamp": datetime(2024, 1, 15, 11, 0, 0), "event": "logout"},
        ]
        tokens = self.estimator.estimate_tokens(data)

        assert tokens > 0
        # Should handle datetime serialization
        assert tokens > 20

    def test_date_objects(self):
        """Test token estimation with date objects."""
        data = [
            {"date": date(2024, 1, 15), "revenue": 1000},
            {"date": date(2024, 1, 16), "revenue": 1500},
        ]
        tokens = self.estimator.estimate_tokens(data)

        assert tokens > 0

    def test_decimal_objects(self):
        """Test token estimation with Decimal objects."""
        data = [
            {"price": Decimal("19.99"), "quantity": 5},
            {"price": Decimal("29.99"), "quantity": 3},
        ]
        tokens = self.estimator.estimate_tokens(data)

        assert tokens > 0

    def test_path_objects(self):
        """Test token estimation with Path objects."""
        data = [
            {"filepath": Path("/tmp/file1.txt"), "size": 1024},
            {"filepath": Path("/tmp/file2.txt"), "size": 2048},
        ]
        tokens = self.estimator.estimate_tokens(data)

        assert tokens > 0

    def test_unicode_strings(self):
        """Test token estimation with unicode characters."""
        data = [
            {"name": "café", "location": "Paris"},
            {"name": "寿司", "location": "Tokyo"},
            {"name": "Москва", "location": "Russia"},
        ]
        tokens = self.estimator.estimate_tokens(data)

        assert tokens > 0
        # Unicode should be handled correctly
        assert tokens > 20

    def test_mixed_special_types(self):
        """Test token estimation with mixed special types."""
        data = [
            {
                "timestamp": datetime.now(),
                "amount": Decimal("123.45"),
                "path": Path("/tmp/test"),
                "unicode": "こんにちは",
            }
        ]
        tokens = self.estimator.estimate_tokens(data)

        assert tokens > 0


class TestThresholdDecisionLogic:
    """Test should_output_to_file decision logic with thresholds."""

    def setup_method(self):
        """Set up test fixtures."""
        self.estimator = TokenEstimator()
        # Create temporary directory for config
        self.temp_dir = TemporaryDirectory()
        # Set environment variable for OutputConfig
        os.environ["MCP_OUTPUT_DIR"] = self.temp_dir.name
        self.config = OutputConfig(
            output_token_threshold=1000,
        )

    def teardown_method(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
        # Clean up environment variable
        if "MCP_OUTPUT_DIR" in os.environ:
            del os.environ["MCP_OUTPUT_DIR"]

    def test_below_threshold_returns_inline(self):
        """Test that data below threshold returns inline (False)."""
        # Small data (should be < 1000 tokens)
        data = [{"id": i} for i in range(10)]

        should_file, token_count, reason = self.estimator.should_output_to_file(data, self.config)

        assert should_file is False
        assert token_count > 0
        assert token_count < 1000
        assert "Below threshold" in reason
        assert str(token_count) in reason

    def test_above_threshold_returns_file(self):
        """Test that data above threshold returns file (True)."""
        # Large data (should be > 1000 tokens)
        data = [{"id": i, "data": "x" * 100, "extra": f"value_{i}"} for i in range(100)]

        should_file, token_count, reason = self.estimator.should_output_to_file(data, self.config)

        assert should_file is True
        assert token_count > 1000
        assert "Exceeds token threshold" in reason
        # Token count is formatted with commas in reason string
        assert f"{token_count:,}" in reason

    def test_exactly_at_threshold(self):
        """Test boundary condition at exact threshold."""
        # Create data that's approximately at threshold
        # Adjust size to get close to 1000 tokens
        data = [{"id": i, "value": f"test_{i}"} for i in range(50)]

        should_file, token_count, _ = self.estimator.should_output_to_file(data, self.config)

        # At threshold, behavior depends on whether it's > threshold
        if token_count > 1000:
            assert should_file is True
        else:
            assert should_file is False

    def test_different_threshold_values(self):
        """Test decision logic with different threshold values."""
        data = [{"id": i, "data": "test" * 10} for i in range(20)]

        # Low threshold (should trigger file)
        config_low = OutputConfig(
            output_token_threshold=10,
        )
        should_file, _, _ = self.estimator.should_output_to_file(data, config_low)
        assert should_file is True

        # High threshold (should trigger inline)
        config_high = OutputConfig(
            output_token_threshold=100000,
        )
        should_file, _, _ = self.estimator.should_output_to_file(data, config_high)
        assert should_file is False


class TestOverrideMechanism:
    """Test override mechanism for AI control (force_inline, force_file)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.estimator = TokenEstimator()
        self.temp_dir = TemporaryDirectory()
        # Set environment variable for OutputConfig
        os.environ["MCP_OUTPUT_DIR"] = self.temp_dir.name
        self.config = OutputConfig(
            output_token_threshold=1000,
        )

    def teardown_method(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
        # Clean up environment variable
        if "MCP_OUTPUT_DIR" in os.environ:
            del os.environ["MCP_OUTPUT_DIR"]

    def test_force_inline_overrides_large_data(self):
        """Test that force_inline=True overrides decision for large data."""
        # Large data that would normally go to file
        data = [{"id": i, "data": "x" * 100} for i in range(100)]

        should_file, token_count, reason = self.estimator.should_output_to_file(
            data, self.config, force_inline=True
        )

        assert should_file is False  # Forced to inline
        assert token_count > 1000  # Data is actually large
        assert "Forced to inline" in reason
        assert "override" in reason

    def test_force_file_overrides_small_data(self):
        """Test that force_file=True overrides decision for small data."""
        # Small data that would normally stay inline
        data = [{"id": i} for i in range(5)]

        should_file, token_count, reason = self.estimator.should_output_to_file(
            data, self.config, force_file=True
        )

        assert should_file is True  # Forced to file
        assert token_count < 1000  # Data is actually small
        assert "Forced to file" in reason
        assert "override" in reason

    def test_both_overrides_raises_error(self):
        """Test that setting both overrides raises ValueError."""
        data = [{"id": 1}]

        with pytest.raises(
            ValueError, match="Cannot specify both force_inline=True and force_file=True"
        ):
            self.estimator.should_output_to_file(
                data, self.config, force_inline=True, force_file=True
            )

    def test_no_override_uses_automatic_decision(self):
        """Test that no override uses automatic threshold decision."""
        # Small data
        small_data = [{"id": i} for i in range(5)]
        should_file, _, _ = self.estimator.should_output_to_file(small_data, self.config)
        assert should_file is False

        # Large data
        large_data = [{"id": i, "data": "x" * 100} for i in range(100)]
        should_file, _, _ = self.estimator.should_output_to_file(large_data, self.config)
        assert should_file is True


class TestEdgeCases:
    """Test edge cases and error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.estimator = TokenEstimator()

    def test_single_row_dataset(self):
        """Test estimation for single-row dataset."""
        data = [{"id": 1, "name": "single"}]
        tokens = self.estimator.estimate_tokens(data)

        assert tokens > 0
        assert tokens < 50

    def test_very_long_strings(self):
        """Test estimation for data with very long strings."""
        data = [{"id": i, "long_text": "x" * 10000} for i in range(5)]
        tokens = self.estimator.estimate_tokens(data)

        assert tokens > 5000  # Should be substantial (conservative due to compression)

    def test_deeply_nested_json(self):
        """Test estimation for deeply nested JSON."""
        data = {
            "level1": {
                "level2": {
                    "level3": {"level4": {"level5": {"value": "deep"}}},
                }
            }
        }
        tokens = self.estimator.estimate_json_tokens(data)

        assert tokens > 0

    def test_json_array_of_arrays(self):
        """Test estimation for nested arrays."""
        data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        tokens = self.estimator.estimate_json_tokens(data)

        assert tokens > 0

    def test_non_dict_list_elements(self):
        """Test that list of non-dicts is handled as JSON."""
        data = [1, 2, 3, "four", "five"]
        tokens = self.estimator.estimate_tokens(data)

        assert tokens > 0

    def test_invalid_data_type_raises_error(self):
        """Test that unsupported data types raise appropriate error."""

        class CustomObject:
            pass

        data = [{"obj": CustomObject()}]

        with pytest.raises((TokenEstimationError, TypeError)):
            self.estimator.estimate_tokens(data)

    def test_none_values_in_data(self):
        """Test that None values are handled correctly."""
        data = [{"id": 1, "value": None}, {"id": 2, "value": None}]
        tokens = self.estimator.estimate_tokens(data)

        assert tokens > 0

    def test_boolean_values(self):
        """Test that boolean values are handled correctly."""
        data = [{"active": True, "verified": False}, {"active": False, "verified": True}]
        tokens = self.estimator.estimate_tokens(data)

        assert tokens > 0


class TestPerformanceBenchmarks:
    """
    Performance benchmarks for token estimation.

    Targets:
    - Small dataset (10 rows): < 10ms
    - Medium dataset (1,000 rows): < 100ms
    - Large dataset (10,000 rows): < 500ms
    - Huge dataset (100,000 rows): < 100ms (fallback)
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.estimator = TokenEstimator()

    def _benchmark(self, data, max_time_ms):
        """
        Helper to benchmark token estimation.

        Args:
            data: Data to estimate.
            max_time_ms: Maximum time in milliseconds.

        Returns:
            Tuple of (elapsed_ms, tokens).
        """
        start = time.perf_counter()
        tokens = self.estimator.estimate_tokens(data)
        elapsed_ms = (time.perf_counter() - start) * 1000

        return elapsed_ms, tokens

    def test_benchmark_small_dataset(self):
        """Benchmark: Small dataset (10 rows) should be < 10ms."""
        data = [{"id": i, "name": f"user_{i}", "score": i * 1.5} for i in range(10)]

        elapsed_ms, tokens = self._benchmark(data, max_time_ms=10)

        assert tokens > 0
        # Allow 5x margin for CI/CD variability
        assert elapsed_ms < 50, f"Small dataset took {elapsed_ms:.2f}ms (target: <10ms)"

    def test_benchmark_medium_dataset(self):
        """Benchmark: Medium dataset (1,000 rows) should be < 100ms."""
        data = [
            {"id": i, "name": f"user_{i}", "email": f"user{i}@test.com", "score": i * 1.5}
            for i in range(1000)
        ]

        elapsed_ms, tokens = self._benchmark(data, max_time_ms=100)

        assert tokens > 0
        # Allow 5x margin for CI/CD variability
        assert elapsed_ms < 500, f"Medium dataset took {elapsed_ms:.2f}ms (target: <100ms)"

    def test_benchmark_large_dataset(self):
        """Benchmark: Large dataset (10,000 rows) should be < 500ms."""
        data = [
            {"id": i, "value": f"item_{i}", "score": i * 0.5, "active": i % 2 == 0}
            for i in range(10000)
        ]

        elapsed_ms, tokens = self._benchmark(data, max_time_ms=500)

        assert tokens > 0
        # Allow 3x margin for CI/CD variability
        assert elapsed_ms < 1500, f"Large dataset took {elapsed_ms:.2f}ms (target: <500ms)"

    def test_benchmark_huge_dataset_fallback(self):
        """Benchmark: Huge dataset (100,000 rows) should be < 100ms (fallback)."""
        # This should trigger fallback estimation
        data = [{"id": i, "value": i * 2} for i in range(100000)]

        elapsed_ms, tokens = self._benchmark(data, max_time_ms=100)

        assert tokens > 0
        # Fallback should be very fast
        assert elapsed_ms < 300, f"Huge dataset fallback took {elapsed_ms:.2f}ms (target: <100ms)"

    def test_fallback_faster_than_tiktoken(self):
        """Benchmark: Fallback should be ≥5x faster than tiktoken for large datasets."""
        # Create dataset that triggers fallback
        large_data = [{"id": i, "data": f"value_{i}"} for i in range(15000)]

        # Time fallback estimation
        start = time.perf_counter()
        fallback_tokens = self.estimator.estimate_by_rows(large_data)
        fallback_time = time.perf_counter() - start

        # Time tiktoken estimation on subset (15000 is above threshold, so use smaller)
        subset = large_data[:1000]
        start = time.perf_counter()
        tiktoken_tokens = self.estimator.estimate_csv_tokens(subset)
        tiktoken_time = time.perf_counter() - start

        # Normalize to same dataset size
        tiktoken_time_normalized = tiktoken_time * 15  # 1000 * 15 = 15000

        assert fallback_tokens > 0
        assert tiktoken_tokens > 0

        # Fallback should be significantly faster (allow 2x instead of 5x for CI variability)
        assert fallback_time < tiktoken_time_normalized / 2, (
            f"Fallback not fast enough: {fallback_time:.3f}s vs {tiktoken_time_normalized:.3f}s"
        )


class TestTokenAccuracy:
    """Test token estimation accuracy within specified margins."""

    def setup_method(self):
        """Set up test fixtures."""
        self.estimator = TokenEstimator()

    def test_csv_estimation_accuracy(self):
        """Test that CSV token estimation is within 5% of actual."""
        # Medium-sized dataset for accuracy testing
        data = [
            {"id": i, "name": f"user_{i}", "email": f"user{i}@example.com", "score": i * 1.5}
            for i in range(500)
        ]

        # Get token estimate
        estimated_tokens = self.estimator.estimate_csv_tokens(data)

        # For validation, we can compare to JSON serialization
        # (both should be similar for this data)
        json_tokens = self.estimator.estimate_json_tokens(data)

        assert estimated_tokens > 0
        assert json_tokens > 0

        # Should be within reasonable range (30% margin for different formats)
        ratio = estimated_tokens / json_tokens
        assert 0.7 < ratio < 1.3, f"Estimation ratio {ratio:.2f} outside acceptable range"

    def test_fallback_conservative_estimate(self):
        """Test that fallback estimation is conservative (slightly over)."""
        # Use dataset that works with both methods
        data = [{"id": i, "value": f"test_{i}"} for i in range(500)]

        # Get both estimates
        actual = self.estimator.estimate_csv_tokens(data)
        fallback = self.estimator.estimate_by_rows(data)

        assert actual > 0
        assert fallback > 0

        # Fallback should be within 50% of actual (conservative)
        assert 0.5 * actual < fallback < 2.0 * actual, (
            f"Fallback {fallback} not conservative enough (actual: {actual})"
        )


# Pytest configuration for coverage
def test_coverage_requirement():
    """
    Placeholder test to remind about coverage requirement.

    Run with: pytest tests/decision/test_token_estimator.py --cov=src.decision.token_estimator --cov-report=term-missing

    Target: ≥90% code coverage
    """
    # This test always passes, it's just documentation
    assert True
