"""
End-to-end integration tests for Alpha Vantage MCP Server output system.

This test suite validates that all Sprint 1 components work together correctly:
- OutputConfig: Configuration management
- TokenEstimator: Token counting and decision logic
- OutputHandler: File I/O operations
- Security: Path validation and sanitization
- Integration helpers: Response creation and decision making
- Logging: Structured logging throughout

Test Coverage:
1. Small dataset → inline response workflow
2. Large dataset → file write → file reference workflow
3. Force inline override → inline response
4. Force file override → file write
5. Project-based workflow → create project → write file → list files
6. CSV and JSON formats
7. With and without compression
8. With and without metadata
9. Error scenarios and edge cases

Target Coverage: ≥90% of integration code
"""

import tempfile
from pathlib import Path

import pytest

from src.decision.token_estimator import TokenEstimator
from src.integration import (
    OutputDecision,
    create_file_reference_response,
    create_inline_response,
    should_use_output_helper,
)
from src.output.handler import OutputHandler
from src.utils.output_config import OutputConfig
from src.utils.security import SecurityError


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows with all components integrated."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def test_config(self, temp_output_dir):
        """Create test configuration with temporary directory."""
        # Use model_construct to bypass validation
        config = OutputConfig.model_construct(
            client_root=temp_output_dir,
            output_token_threshold=1000,
            output_csv_threshold=100,
            max_inline_rows=50,
            output_format="csv",
            output_compression=False,
            output_metadata=True,
            project_name="default",
            enable_project_folders=True,
            output_auto=True,
            streaming_chunk_size=10000,
            default_folder_permissions=0o755,
        )
        return config

    @pytest.fixture
    def output_handler(self, test_config):
        """Create OutputHandler instance."""
        return OutputHandler(test_config)

    @pytest.fixture
    def small_dataset(self):
        """Create a small dataset (should stay inline)."""
        return [{"id": i, "value": f"item_{i}"} for i in range(10)]

    @pytest.fixture
    def large_dataset(self):
        """Create a large dataset (should go to file)."""
        return [{"id": i, "data": "x" * 100, "extra": f"value_{i}"} for i in range(200)]

    # Test 1: Small dataset → inline response workflow
    def test_small_dataset_inline_workflow(self, small_dataset, test_config):
        """Test complete workflow for small dataset returning inline."""
        # Step 1: Make decision
        decision = should_use_output_helper(small_dataset, test_config)

        # Verify decision
        assert isinstance(decision, OutputDecision)
        assert decision.use_file is False, "Small dataset should stay inline"
        assert decision.token_count > 0, "Should have token count"
        assert decision.row_count == 10, "Should count 10 rows"
        assert "Below threshold" in decision.reason, "Should explain inline decision"
        assert decision.suggested_filename.endswith(".csv"), "Should suggest CSV filename"

        # Step 2: Create inline response
        response = create_inline_response(small_dataset, format="json")

        # Verify response
        assert response["type"] == "inline_data"
        assert response["format"] == "json"
        assert response["row_count"] == 10
        assert response["data"] == small_dataset
        assert "timestamp" in response

    # Test 2: Large dataset → file write → file reference workflow
    @pytest.mark.asyncio
    async def test_large_dataset_file_workflow(self, large_dataset, test_config, output_handler):
        """Test complete workflow for large dataset writing to file."""
        # Step 1: Make decision
        decision = should_use_output_helper(large_dataset, test_config)

        # Verify decision
        assert decision.use_file is True, "Large dataset should go to file"
        assert decision.token_count > test_config.output_token_threshold
        assert decision.row_count == 200
        assert "Exceeds" in decision.reason or "threshold" in decision.reason.lower()

        # Step 2: Write to file
        filepath = test_config.client_root / decision.suggested_filename
        metadata = await output_handler.write_csv(large_dataset, filepath, test_config)

        # Verify file was written
        assert filepath.exists(), "File should exist"
        assert metadata.rows == 200, "Should have 200 rows"
        assert metadata.format == "csv", "Should be CSV format"
        assert metadata.compressed is False, "Should not be compressed"
        assert metadata.size_bytes > 0, "Should have size"
        assert metadata.checksum, "Should have checksum"

        # Step 3: Create file reference response
        response = create_file_reference_response(filepath, metadata, test_config)

        # Verify response
        assert response["type"] == "file_reference"
        assert response["filename"] == decision.suggested_filename
        assert response["rows"] == 200
        assert response["format"] == "csv"
        assert response["compressed"] is False
        assert response["size"] == metadata.size_bytes
        assert "timestamp" in response
        assert "checksum" in response

    # Test 3: Force inline override → inline response
    def test_force_inline_override(self, large_dataset, test_config):
        """Test forcing inline output for large dataset."""
        # Make decision with force_inline
        decision = should_use_output_helper(large_dataset, test_config, force_inline=True)

        # Verify override worked
        assert decision.use_file is False, "Should force inline"
        assert "Forced to inline" in decision.reason
        assert decision.token_count > test_config.output_token_threshold

        # Create inline response
        response = create_inline_response(large_dataset, format="csv")

        # Verify CSV format
        assert response["type"] == "inline_data"
        assert response["format"] == "csv"
        assert isinstance(response["data"], str), "CSV should be string"
        assert "id,data,extra" in response["data"], "Should have headers"
        assert response["row_count"] == 200

    # Test 4: Force file override → file write
    @pytest.mark.asyncio
    async def test_force_file_override(self, small_dataset, test_config, output_handler):
        """Test forcing file output for small dataset."""
        # Make decision with force_file
        decision = should_use_output_helper(small_dataset, test_config, force_file=True)

        # Verify override worked
        assert decision.use_file is True, "Should force file"
        assert "Forced to file" in decision.reason
        assert decision.token_count < test_config.output_token_threshold

        # Write to file
        filepath = test_config.client_root / decision.suggested_filename
        metadata = await output_handler.write_csv(small_dataset, filepath, test_config)

        # Verify file was written
        assert filepath.exists()
        assert metadata.rows == 10

    # Test 5: Project-based workflow
    @pytest.mark.asyncio
    async def test_project_workflow(self, large_dataset, test_config, output_handler):
        """Test complete project-based workflow."""
        project_name = "test-project"

        # Step 1: Create project
        project_path = await output_handler.create_project_folder(project_name)
        assert project_path.exists()
        assert project_path.name == project_name

        # Step 2: Make decision and write file
        decision = should_use_output_helper(large_dataset, test_config, filename_prefix="data")
        filepath = project_path / decision.suggested_filename
        metadata = await output_handler.write_csv(large_dataset, filepath, test_config)

        # Verify file in project
        assert filepath.exists()
        assert filepath.parent == project_path

        # Step 3: List project files
        files = await output_handler.list_project_files(project_name)
        assert len(files) == 1
        assert files[0].name == decision.suggested_filename
        assert files[0].size > 0

        # Step 4: Create file reference
        response = create_file_reference_response(filepath, metadata, test_config)
        assert project_name in response["filepath"]

    # Test 6: CSV format workflow
    @pytest.mark.asyncio
    async def test_csv_format_workflow(self, large_dataset, test_config, output_handler):
        """Test CSV format end-to-end."""
        test_config.output_format = "csv"

        decision = should_use_output_helper(large_dataset, test_config)
        assert decision.suggested_filename.endswith(".csv")

        filepath = test_config.client_root / decision.suggested_filename
        metadata = await output_handler.write_csv(large_dataset, filepath, test_config)

        assert metadata.format == "csv"
        response = create_file_reference_response(filepath, metadata, test_config)
        assert response["format"] == "csv"

    # Test 7: JSON format workflow
    @pytest.mark.asyncio
    async def test_json_format_workflow(self, large_dataset, test_config, output_handler):
        """Test JSON format end-to-end."""
        test_config.output_format = "json"

        # JSON decision
        decision = should_use_output_helper(large_dataset, test_config)
        assert decision.suggested_filename.endswith(".json")

        # Write JSON
        filepath = test_config.client_root / decision.suggested_filename
        metadata = await output_handler.write_json(large_dataset, filepath, test_config)

        assert metadata.format == "json"
        response = create_file_reference_response(filepath, metadata, test_config)
        assert response["format"] == "json"

    # Test 8: Compression workflow
    @pytest.mark.asyncio
    async def test_compression_workflow(self, large_dataset, test_config, output_handler):
        """Test workflow with compression enabled."""
        test_config.output_compression = True

        decision = should_use_output_helper(large_dataset, test_config)
        assert decision.suggested_filename.endswith(".csv.gz")

        # Remove .gz from suggested filename since OutputHandler will add it
        base_filename = decision.suggested_filename.replace(".gz", "")
        filepath = test_config.client_root / base_filename
        metadata = await output_handler.write_csv(large_dataset, filepath, test_config)

        assert metadata.compressed is True
        assert metadata.format == "csv.gz"
        # Create reference with actual compressed filepath
        actual_filepath = test_config.client_root / decision.suggested_filename
        response = create_file_reference_response(actual_filepath, metadata, test_config)
        assert response["compressed"] is True

    # Test 9: Metadata enabled workflow
    @pytest.mark.asyncio
    async def test_metadata_workflow(self, large_dataset, test_config, output_handler):
        """Test workflow with metadata enabled."""
        test_config.output_metadata = True

        decision = should_use_output_helper(large_dataset, test_config)
        filepath = test_config.client_root / decision.suggested_filename
        metadata = await output_handler.write_csv(large_dataset, filepath, test_config)

        response = create_file_reference_response(filepath, metadata, test_config)
        assert "metadata" in response
        assert response["metadata"]["checksum"]
        assert response["metadata"]["rows"] == 200

    # Test 10: Metadata disabled workflow
    @pytest.mark.asyncio
    async def test_no_metadata_workflow(self, large_dataset, test_config, output_handler):
        """Test workflow with metadata disabled."""
        test_config.output_metadata = False

        decision = should_use_output_helper(large_dataset, test_config)
        filepath = test_config.client_root / decision.suggested_filename
        metadata = await output_handler.write_csv(large_dataset, filepath, test_config)

        # Create file reference and verify checksum behavior
        _ = create_file_reference_response(filepath, metadata, test_config)
        # Checksum should be empty when metadata disabled
        assert metadata.checksum == ""


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def test_config(self, temp_output_dir):
        """Create test configuration with temporary directory."""
        config = OutputConfig.model_construct(client_root=temp_output_dir)
        return config

    def test_empty_dataset_error(self, test_config):
        """Test that empty dataset raises error."""
        with pytest.raises(ValueError, match="empty"):
            should_use_output_helper([], test_config)

    def test_none_dataset_error(self, test_config):
        """Test that None dataset raises error."""
        with pytest.raises(ValueError, match="cannot be None"):
            should_use_output_helper(None, test_config)

    def test_conflicting_overrides_error(self, test_config):
        """Test that conflicting overrides raise error."""
        data = [{"id": 1}]
        with pytest.raises(ValueError, match="both force_inline.*and force_file"):
            should_use_output_helper(data, test_config, force_inline=True, force_file=True)

    def test_invalid_csv_format_error(self, test_config):
        """Test that invalid data for CSV format raises error."""
        data = {"key": "value"}  # Not a list of dicts
        with pytest.raises(ValueError, match="CSV format requires"):
            create_inline_response(data, format="csv")

    def test_invalid_format_error(self, test_config):
        """Test that invalid format raises error."""
        data = [{"id": 1}]
        with pytest.raises(ValueError, match="Invalid format"):
            create_inline_response(data, format="xml")

    def test_single_item_data(self, test_config):
        """Test handling of single-item dataset."""
        data = [{"id": 1}]
        decision = should_use_output_helper(data, test_config)
        assert decision.row_count == 1
        assert decision.use_file is False

    def test_dict_data(self, test_config):
        """Test handling of dict data."""
        data = {"key": "value", "number": 42}
        decision = should_use_output_helper(data, test_config)
        assert decision.row_count == 2  # Number of keys
        assert decision.use_file is False

        response = create_inline_response(data, format="json")
        assert response["data"] == data

    def test_custom_filename_prefix(self, test_config):
        """Test custom filename prefix."""
        data = [{"id": 1}]
        decision = should_use_output_helper(data, test_config, filename_prefix="stocks")
        assert decision.suggested_filename.startswith("stocks_")


class TestComponentIntegration:
    """Test that all components work together correctly."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def test_config(self, temp_output_dir):
        """Create test configuration."""
        config = OutputConfig.model_construct(
            client_root=temp_output_dir, output_token_threshold=500
        )
        return config

    def test_token_estimator_integration(self, test_config):
        """Test TokenEstimator integration."""
        estimator = TokenEstimator()
        data = [{"id": i, "value": f"test_{i}"} for i in range(50)]

        # TokenEstimator should work
        token_count = estimator.estimate_tokens(data)
        assert token_count > 0

        # Integration helper should use same estimator logic
        decision = should_use_output_helper(data, test_config)
        assert decision.token_count == token_count

    @pytest.mark.asyncio
    async def test_security_validation_integration(self, test_config):
        """Test that security validation is applied."""
        handler = OutputHandler(test_config)
        data = [{"id": 1}]

        # Security should prevent path traversal
        filepath = test_config.client_root / "../etc/passwd"
        with pytest.raises(SecurityError):
            await handler.write_csv(data, filepath, test_config)

    @pytest.mark.asyncio
    async def test_output_config_integration(self, test_config):
        """Test OutputConfig integration throughout workflow."""
        handler = OutputHandler(test_config)
        data = [{"id": i} for i in range(10)]

        # Config should affect decision
        test_config.output_token_threshold = 10  # Very low threshold
        decision = should_use_output_helper(data, test_config)
        assert decision.use_file is True  # Should exceed threshold

        # Config should affect file writing
        test_config.output_compression = True
        filepath = test_config.client_root / "test.csv"
        metadata = await handler.write_csv(data, filepath, test_config)
        assert metadata.compressed is True

    def test_all_response_fields_present(self, test_config):
        """Test that all expected response fields are present."""
        data = [{"id": 1}]

        # Test inline response fields
        inline_resp = create_inline_response(data, format="json")
        required_inline_fields = ["type", "format", "data", "row_count", "timestamp"]
        for field in required_inline_fields:
            assert field in inline_resp, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_file_reference_fields_present(self, test_config):
        """Test that all file reference fields are present."""
        handler = OutputHandler(test_config)
        data = [{"id": 1}]

        filepath = test_config.client_root / "test.csv"
        metadata = await handler.write_csv(data, filepath, test_config)

        # Test file reference response fields
        file_resp = create_file_reference_response(filepath, metadata, test_config)
        required_file_fields = [
            "type",
            "filepath",
            "filename",
            "size",
            "size_formatted",
            "format",
            "compressed",
            "rows",
            "timestamp",
            "checksum",
        ]
        for field in required_file_fields:
            assert field in file_resp, f"Missing field: {field}"


class TestPerformance:
    """Test performance characteristics of integrated system."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def test_config(self, temp_output_dir):
        """Create test configuration."""
        config = OutputConfig.model_construct(client_root=temp_output_dir)
        return config

    def test_decision_speed(self, test_config):
        """Test that decision making is fast."""
        import time

        data = [{"id": i, "data": "x" * 50} for i in range(1000)]

        start = time.time()
        decision = should_use_output_helper(data, test_config)
        duration = time.time() - start

        assert duration < 1.0, f"Decision took {duration}s, should be < 1s"
        assert decision.token_count > 0

    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, test_config):
        """Test that large datasets are handled efficiently."""
        handler = OutputHandler(test_config)
        # Create 10,000 row dataset
        large_data = [{"id": i, "value": f"item_{i}" * 10} for i in range(10000)]

        import time

        start = time.time()
        decision = should_use_output_helper(large_data, test_config)
        decision_time = time.time() - start

        assert decision_time < 2.0, f"Decision took {decision_time}s, should be < 2s"
        assert decision.use_file is True

        # File write should also be fast
        start = time.time()
        filepath = test_config.client_root / decision.suggested_filename
        await handler.write_csv(large_data, filepath, test_config)
        write_time = time.time() - start

        assert write_time < 5.0, f"Write took {write_time}s, should be < 5s"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.integration", "--cov-report=term-missing"])


class TestLogging:
    """Test logging functionality."""

    def test_logging_functions(self):
        """Test that logging functions work without errors."""
        from src.integration.logging_config import (
            get_logger,
            log_decision,
            log_file_operation,
            log_performance_metric,
            log_security_event,
        )

        # Get logger (this initializes logging config)
        logger = get_logger()
        assert logger is not None

        # Test log_decision
        log_decision(
            decision_type="automatic",
            use_file=True,
            token_count=5000,
            row_count=1000,
            reason="Test reason",
            extra_field="value",
        )

        # Test log_file_operation
        log_file_operation(
            operation="write",
            filepath="/tmp/test.csv",
            success=True,
            size_bytes=1024,
            duration_ms=50.5,
            format="csv",
        )

        # Test log_security_event
        log_security_event(
            event_type="test_event",
            message="Test security message",
            severity="warning",
            path="/tmp/test.csv",
            user="test_user",
        )

        # Test log_performance_metric
        log_performance_metric(
            metric_name="test_metric",
            value=123.45,
            unit="ms",
            operation="test",
        )

        # Test invalid severity (should default to warning)
        log_security_event(
            event_type="test",
            message="Test",
            severity="invalid",  # Will be defaulted to warning
        )
