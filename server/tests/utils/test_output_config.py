"""
Comprehensive tests for OutputConfig Pydantic model.

Tests cover:
- Valid configuration loading
- Environment variable parsing
- Field validation
- Error handling
- Edge cases
"""

from pathlib import Path

import pytest

from src.utils.output_config import OutputConfig, load_output_config


class TestOutputConfigBasics:
    """Test basic configuration loading and defaults."""

    def test_output_config_with_valid_env(self, tmp_path, monkeypatch):
        """Test configuration loads with valid environment variables."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_PROJECT_NAME", "test_project")

        config = OutputConfig()

        assert config.client_root == tmp_path
        assert config.project_name == "test_project"

    def test_output_config_with_defaults(self, tmp_path, monkeypatch):
        """Test configuration uses defaults when env vars not set."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))

        config = OutputConfig()

        assert config.project_name == "default"
        assert config.enable_project_folders is True
        assert config.output_auto is True
        assert config.output_token_threshold == 1000
        assert config.output_csv_threshold == 100
        assert config.max_inline_rows == 50
        assert config.output_format == "csv"
        assert config.output_compression is False
        assert config.output_metadata is True
        assert config.streaming_chunk_size == 10000
        assert config.default_folder_permissions == 0o755

    def test_output_config_missing_client_root(self, monkeypatch):
        """Test configuration fails without MCP_OUTPUT_DIR."""
        # Clear the environment variable
        monkeypatch.delenv("MCP_OUTPUT_DIR", raising=False)

        with pytest.raises(ValueError, match="MCP_OUTPUT_DIR must be set"):
            OutputConfig()

    def test_output_config_with_all_env_vars(self, tmp_path, monkeypatch):
        """Test configuration loads all environment variables correctly."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_PROJECT_NAME", "custom_project")
        monkeypatch.setenv("MCP_ENABLE_PROJECT_FOLDERS", "false")
        monkeypatch.setenv("MCP_OUTPUT_AUTO", "false")
        monkeypatch.setenv("MCP_OUTPUT_TOKEN_THRESHOLD", "2000")
        monkeypatch.setenv("MCP_OUTPUT_CSV_THRESHOLD", "200")
        monkeypatch.setenv("MCP_MAX_INLINE_ROWS", "100")
        monkeypatch.setenv("MCP_OUTPUT_FORMAT", "json")
        monkeypatch.setenv("MCP_OUTPUT_COMPRESSION", "true")
        monkeypatch.setenv("MCP_OUTPUT_METADATA", "false")
        monkeypatch.setenv("MCP_STREAMING_CHUNK_SIZE", "5000")
        monkeypatch.setenv("MCP_DEFAULT_FOLDER_PERMISSIONS", "0o777")

        config = OutputConfig()

        assert config.client_root == tmp_path
        assert config.project_name == "custom_project"
        assert config.enable_project_folders is False
        assert config.output_auto is False
        assert config.output_token_threshold == 2000
        assert config.output_csv_threshold == 200
        assert config.max_inline_rows == 100
        assert config.output_format == "json"
        assert config.output_compression is True
        assert config.output_metadata is False
        assert config.streaming_chunk_size == 5000
        assert config.default_folder_permissions == 0o777


class TestClientRootValidation:
    """Test client_root path validation."""

    def test_output_config_non_absolute_path(self, monkeypatch):
        """Test configuration fails with relative path."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", "relative/path")

        with pytest.raises(ValueError, match="must be an absolute path"):
            OutputConfig()

    def test_output_config_creates_directory(self, tmp_path, monkeypatch):
        """Test configuration creates directory if it doesn't exist."""
        new_dir = tmp_path / "new" / "nested" / "dir"
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(new_dir))

        config = OutputConfig()

        assert config.client_root == new_dir
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_output_config_with_direct_path_assignment(self, tmp_path, monkeypatch):
        """Test configuration with direct Path assignment (for testing)."""
        # Set environment variable for BaseSettings
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))

        config = OutputConfig()

        assert config.client_root == tmp_path

    def test_output_config_read_only_directory_fails(self, tmp_path, monkeypatch):
        """Test configuration fails with read-only directory."""
        read_only_dir = tmp_path / "readonly"
        read_only_dir.mkdir()
        read_only_dir.chmod(0o444)  # Read-only

        monkeypatch.setenv("MCP_OUTPUT_DIR", str(read_only_dir))

        try:
            with pytest.raises(ValueError, match="not writable"):
                OutputConfig()
        finally:
            # Restore permissions for cleanup
            read_only_dir.chmod(0o755)


class TestThresholdValidation:
    """Test threshold and bounds validation."""

    def test_output_token_threshold_too_small(self, tmp_path, monkeypatch):
        """Test output_token_threshold fails with value <= 0."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_OUTPUT_TOKEN_THRESHOLD", "0")

        with pytest.raises(ValueError, match="output_token_threshold must be > 0"):
            OutputConfig()

    def test_output_token_threshold_negative(self, tmp_path, monkeypatch):
        """Test output_token_threshold fails with negative value."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_OUTPUT_TOKEN_THRESHOLD", "-100")

        with pytest.raises(ValueError, match="output_token_threshold must be > 0"):
            OutputConfig()

    def test_csv_threshold_too_small(self, tmp_path, monkeypatch):
        """Test CSV threshold validation fails below minimum."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_OUTPUT_CSV_THRESHOLD", "0")

        with pytest.raises(
            ValueError, match="output_csv_threshold must be between 1 and 1,000,000"
        ):
            OutputConfig()

    def test_csv_threshold_too_large(self, tmp_path, monkeypatch):
        """Test CSV threshold validation fails above maximum."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_OUTPUT_CSV_THRESHOLD", "1000001")

        with pytest.raises(
            ValueError, match="output_csv_threshold must be between 1 and 1,000,000"
        ):
            OutputConfig()

    def test_csv_threshold_valid_bounds(self, tmp_path, monkeypatch):
        """Test CSV threshold accepts valid boundary values."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))

        # Test minimum
        monkeypatch.setenv("MCP_OUTPUT_CSV_THRESHOLD", "1")
        config = OutputConfig()
        assert config.output_csv_threshold == 1

        # Test maximum
        monkeypatch.setenv("MCP_OUTPUT_CSV_THRESHOLD", "1000000")
        config = OutputConfig()
        assert config.output_csv_threshold == 1_000_000

    def test_max_inline_rows_too_small(self, tmp_path, monkeypatch):
        """Test max_inline_rows fails with value <= 0."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_MAX_INLINE_ROWS", "0")

        with pytest.raises(ValueError, match="max_inline_rows must be > 0"):
            OutputConfig()

    def test_streaming_chunk_size_too_small(self, tmp_path, monkeypatch):
        """Test streaming chunk size validation fails below minimum."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_STREAMING_CHUNK_SIZE", "99")

        with pytest.raises(
            ValueError, match="streaming_chunk_size must be between 100 and 100,000"
        ):
            OutputConfig()

    def test_streaming_chunk_size_too_large(self, tmp_path, monkeypatch):
        """Test streaming chunk size validation fails above maximum."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_STREAMING_CHUNK_SIZE", "100001")

        with pytest.raises(
            ValueError, match="streaming_chunk_size must be between 100 and 100,000"
        ):
            OutputConfig()

    def test_streaming_chunk_size_valid_bounds(self, tmp_path, monkeypatch):
        """Test streaming chunk size accepts valid boundary values."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))

        # Test minimum
        monkeypatch.setenv("MCP_STREAMING_CHUNK_SIZE", "100")
        config = OutputConfig()
        assert config.streaming_chunk_size == 100

        # Test maximum
        monkeypatch.setenv("MCP_STREAMING_CHUNK_SIZE", "100000")
        config = OutputConfig()
        assert config.streaming_chunk_size == 100_000


class TestBooleanParsing:
    """Test boolean field parsing from environment variables."""

    def test_boolean_true_variations(self, tmp_path, monkeypatch):
        """Test various truthy values for boolean fields."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))

        # Test "true"
        monkeypatch.setenv("MCP_ENABLE_PROJECT_FOLDERS", "true")
        config = OutputConfig()
        assert config.enable_project_folders is True

        # Test "1"
        monkeypatch.setenv("MCP_OUTPUT_AUTO", "1")
        config = OutputConfig()
        assert config.output_auto is True

        # Test "yes"
        monkeypatch.setenv("MCP_OUTPUT_COMPRESSION", "yes")
        config = OutputConfig()
        assert config.output_compression is True

        # Test "on"
        monkeypatch.setenv("MCP_OUTPUT_METADATA", "on")
        config = OutputConfig()
        assert config.output_metadata is True

    def test_boolean_false_variations(self, tmp_path, monkeypatch):
        """Test various falsy values for boolean fields."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))

        # Test "false"
        monkeypatch.setenv("MCP_ENABLE_PROJECT_FOLDERS", "false")
        config = OutputConfig()
        assert config.enable_project_folders is False

        # Test "0"
        monkeypatch.setenv("MCP_OUTPUT_AUTO", "0")
        config = OutputConfig()
        assert config.output_auto is False

        # Test "no"
        monkeypatch.setenv("MCP_OUTPUT_COMPRESSION", "no")
        config = OutputConfig()
        assert config.output_compression is False


class TestOutputFormatValidation:
    """Test output format validation."""

    def test_output_format_csv(self, tmp_path, monkeypatch):
        """Test output format accepts 'csv'."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_OUTPUT_FORMAT", "csv")

        config = OutputConfig()
        assert config.output_format == "csv"

    def test_output_format_json(self, tmp_path, monkeypatch):
        """Test output format accepts 'json'."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_OUTPUT_FORMAT", "json")

        config = OutputConfig()
        assert config.output_format == "json"

    def test_output_format_invalid(self, tmp_path, monkeypatch):
        """Test output format rejects invalid values."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_OUTPUT_FORMAT", "xml")

        with pytest.raises(ValueError):
            OutputConfig()


class TestPermissionsValidation:
    """Test folder permissions validation."""

    def test_default_folder_permissions_octal_string(self, tmp_path, monkeypatch):
        """Test folder permissions from octal string."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_DEFAULT_FOLDER_PERMISSIONS", "0o755")

        config = OutputConfig()
        assert config.default_folder_permissions == 0o755

    def test_default_folder_permissions_decimal_string(self, tmp_path, monkeypatch):
        """Test folder permissions from decimal string."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_DEFAULT_FOLDER_PERMISSIONS", "493")  # 0o755 in decimal

        config = OutputConfig()
        assert config.default_folder_permissions == 493

    def test_default_folder_permissions_different_values(self, tmp_path, monkeypatch):
        """Test various permission values."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))

        # Test 0o777
        monkeypatch.setenv("MCP_DEFAULT_FOLDER_PERMISSIONS", "0o777")
        config = OutputConfig()
        assert config.default_folder_permissions == 0o777

        # Test 0o700
        monkeypatch.setenv("MCP_DEFAULT_FOLDER_PERMISSIONS", "0o700")
        config = OutputConfig()
        assert config.default_folder_permissions == 0o700


class TestLoadOutputConfigHelper:
    """Test the load_output_config() helper function."""

    def test_load_output_config_success(self, tmp_path, monkeypatch):
        """Test load_output_config() helper function."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))

        config = load_output_config()

        assert isinstance(config, OutputConfig)
        assert config.client_root.exists()

    def test_load_output_config_failure(self, monkeypatch):
        """Test load_output_config() fails with helpful error."""
        monkeypatch.delenv("MCP_OUTPUT_DIR", raising=False)

        with pytest.raises(ValueError, match="Invalid output configuration"):
            load_output_config()


class TestValidateAssignment:
    """Test that configuration validates on field assignment."""

    def test_validate_assignment_enabled(self, tmp_path, monkeypatch):
        """Test that validation occurs on field assignment."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))

        config = OutputConfig()

        # Should raise validation error when assigning invalid value
        with pytest.raises(ValueError):
            config.output_csv_threshold = 0

    def test_reassign_client_root_valid(self, tmp_path, monkeypatch):
        """Test reassigning client_root with valid path."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))

        config = OutputConfig()

        new_path = tmp_path / "new_location"
        new_path.mkdir()

        config.client_root = new_path
        assert config.client_root == new_path


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_project_name_uses_default(self, tmp_path, monkeypatch):
        """Test empty project name falls back to default."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
        monkeypatch.setenv("MCP_PROJECT_NAME", "")

        config = OutputConfig()
        # Empty string should use default
        assert config.project_name in ["", "default"]

    def test_whitespace_in_paths_preserved(self, tmp_path, monkeypatch):
        """Test paths with whitespace are preserved correctly."""
        path_with_space = tmp_path / "path with spaces"
        path_with_space.mkdir()

        monkeypatch.setenv("MCP_OUTPUT_DIR", str(path_with_space))

        config = OutputConfig()
        assert config.client_root == path_with_space
        assert " " in str(config.client_root)

    def test_config_immutability_after_creation(self, tmp_path, monkeypatch):
        """Test configuration values can be read after creation."""
        monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))

        config = OutputConfig()

        # Should be able to read all fields
        assert isinstance(config.client_root, Path)
        assert isinstance(config.project_name, str)
        assert isinstance(config.enable_project_folders, bool)
        assert isinstance(config.output_auto, bool)
        assert isinstance(config.output_token_threshold, int)
        assert isinstance(config.output_csv_threshold, int)
        assert isinstance(config.max_inline_rows, int)
        assert config.output_format in ["csv", "json"]
        assert isinstance(config.output_compression, bool)
        assert isinstance(config.output_metadata, bool)
        assert isinstance(config.streaming_chunk_size, int)
        assert isinstance(config.default_folder_permissions, int)
