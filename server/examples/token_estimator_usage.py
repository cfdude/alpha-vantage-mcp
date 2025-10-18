"""
Example usage of TokenEstimator for intelligent output decision logic.

This script demonstrates:
1. Basic token estimation for CSV and JSON data
2. Automatic file vs. inline decision based on thresholds
3. Override mechanism for AI control
4. Performance characteristics

Run:
    python3 examples/token_estimator_usage.py
"""

import os
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from src.decision.token_estimator import TokenEstimator
from src.utils.output_config import OutputConfig


def example_basic_estimation():
    """Example 1: Basic token estimation."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Token Estimation")
    print("=" * 80)

    estimator = TokenEstimator()

    # Small CSV dataset
    small_data = [
        {"name": "Alice", "age": 30, "city": "New York"},
        {"name": "Bob", "age": 25, "city": "Los Angeles"},
        {"name": "Charlie", "age": 35, "city": "Chicago"},
    ]

    tokens = estimator.estimate_tokens(small_data)
    print(f"\nSmall CSV dataset (3 rows): {tokens} tokens")

    # Medium CSV dataset
    medium_data = [
        {"id": i, "name": f"user_{i}", "email": f"user{i}@test.com", "score": i * 1.5}
        for i in range(100)
    ]

    tokens = estimator.estimate_tokens(medium_data)
    print(f"Medium CSV dataset (100 rows): {tokens:,} tokens")

    # Large CSV dataset
    large_data = [{"id": i, "value": f"item_{i}", "active": i % 2 == 0} for i in range(1000)]

    tokens = estimator.estimate_tokens(large_data)
    print(f"Large CSV dataset (1,000 rows): {tokens:,} tokens")

    # JSON dictionary
    json_data = {
        "project": "Alpha Vantage MCP",
        "version": "0.2.0",
        "description": "Financial data APIs via Model Context Protocol",
        "features": ["Real-time quotes", "Historical data", "Technical indicators"],
    }

    tokens = estimator.estimate_json_tokens(json_data)
    print(f"JSON dictionary: {tokens} tokens")


def example_automatic_decision():
    """Example 2: Automatic file vs. inline decision."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Automatic File vs. Inline Decision")
    print("=" * 80)

    estimator = TokenEstimator()

    # Set up config with temporary directory
    with TemporaryDirectory() as temp_dir:
        os.environ["MCP_OUTPUT_DIR"] = temp_dir
        config = OutputConfig(
            output_token_threshold=1000,  # 1000 tokens threshold
        )

        # Test with small data (should stay inline)
        small_data = [{"id": i, "value": i * 2} for i in range(20)]

        should_file, token_count, reason = estimator.should_output_to_file(small_data, config)

        print(f"\nSmall data (20 rows):")
        print(f"  Token count: {token_count}")
        print(f"  Decision: {'FILE' if should_file else 'INLINE'}")
        print(f"  Reason: {reason}")

        # Test with large data (should go to file)
        large_data = [
            {"id": i, "data": "x" * 100, "extra": f"value_{i}"} for i in range(100)
        ]

        should_file, token_count, reason = estimator.should_output_to_file(large_data, config)

        print(f"\nLarge data (100 rows with long strings):")
        print(f"  Token count: {token_count:,}")
        print(f"  Decision: {'FILE' if should_file else 'INLINE'}")
        print(f"  Reason: {reason}")

        # Clean up env var
        del os.environ["MCP_OUTPUT_DIR"]


def example_override_mechanism():
    """Example 3: Override mechanism for AI control."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Override Mechanism for AI Control")
    print("=" * 80)

    estimator = TokenEstimator()

    with TemporaryDirectory() as temp_dir:
        os.environ["MCP_OUTPUT_DIR"] = temp_dir
        config = OutputConfig(output_token_threshold=1000)

        # Medium-sized data
        data = [{"id": i, "value": f"test_{i}"} for i in range(50)]

        # Normal decision
        should_file, token_count, reason = estimator.should_output_to_file(data, config)
        print(f"\nNormal decision:")
        print(f"  Token count: {token_count}")
        print(f"  Decision: {'FILE' if should_file else 'INLINE'}")
        print(f"  Reason: {reason}")

        # Force inline (AI override)
        should_file, token_count, reason = estimator.should_output_to_file(
            data, config, force_inline=True
        )
        print(f"\nForced inline (AI override):")
        print(f"  Token count: {token_count}")
        print(f"  Decision: {'FILE' if should_file else 'INLINE'}")
        print(f"  Reason: {reason}")

        # Force file (AI override)
        should_file, token_count, reason = estimator.should_output_to_file(
            data, config, force_file=True
        )
        print(f"\nForced file (AI override):")
        print(f"  Token count: {token_count}")
        print(f"  Decision: {'FILE' if should_file else 'INLINE'}")
        print(f"  Reason: {reason}")

        del os.environ["MCP_OUTPUT_DIR"]


def example_performance_characteristics():
    """Example 4: Performance characteristics."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Performance Characteristics")
    print("=" * 80)

    estimator = TokenEstimator()

    # Small dataset
    small_data = [{"id": i, "value": f"item_{i}"} for i in range(10)]
    start = time.perf_counter()
    tokens = estimator.estimate_tokens(small_data)
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"\nSmall dataset (10 rows):")
    print(f"  Tokens: {tokens}")
    print(f"  Time: {elapsed_ms:.2f}ms (target: <10ms)")

    # Medium dataset
    medium_data = [{"id": i, "value": f"item_{i}"} for i in range(1000)]
    start = time.perf_counter()
    tokens = estimator.estimate_tokens(medium_data)
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"\nMedium dataset (1,000 rows):")
    print(f"  Tokens: {tokens:,}")
    print(f"  Time: {elapsed_ms:.2f}ms (target: <100ms)")

    # Large dataset
    large_data = [{"id": i, "value": f"item_{i}"} for i in range(10000)]
    start = time.perf_counter()
    tokens = estimator.estimate_tokens(large_data)
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"\nLarge dataset (10,000 rows):")
    print(f"  Tokens: {tokens:,}")
    print(f"  Time: {elapsed_ms:.2f}ms (target: <500ms)")

    # Huge dataset (triggers fallback)
    huge_data = [{"id": i, "value": i * 2} for i in range(100000)]
    start = time.perf_counter()
    tokens = estimator.estimate_tokens(huge_data)
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"\nHuge dataset (100,000 rows - fallback estimation):")
    print(f"  Tokens: {tokens:,}")
    print(f"  Time: {elapsed_ms:.2f}ms (target: <100ms)")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("TokenEstimator Usage Examples")
    print("=" * 80)

    example_basic_estimation()
    example_automatic_decision()
    example_override_mechanism()
    example_performance_characteristics()

    print("\n" + "=" * 80)
    print("Examples completed successfully!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
