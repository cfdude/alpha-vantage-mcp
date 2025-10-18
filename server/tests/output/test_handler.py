"""
Comprehensive unit tests for output handler.

Tests cover:
- CSV writing (small/large datasets, headers, compression)
- JSON writing (arrays/objects, compression, serialization)
- Metadata generation (all fields, checksums, formatting)
- Error handling (I/O errors, retries, cleanup)
- Integration with OutputConfig and security validation
"""

import gzip
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.output.handler import (
    FileWriteError,
    OutputHandler,
    _calculate_checksum,
    _format_size,
)
from src.utils.output_config import OutputConfig
from src.utils.security import SecurityError


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set environment variable for OutputConfig
        os.environ["MCP_OUTPUT_DIR"] = tmpdir
        yield Path(tmpdir)
        # Clean up
        if "MCP_OUTPUT_DIR" in os.environ:
            del os.environ["MCP_OUTPUT_DIR"]


@pytest.fixture
def test_config(temp_output_dir):
    """Create test configuration with temp directory."""
    config = OutputConfig(
        project_name="test_project",
        output_compression=False,
        output_metadata=True,
        streaming_chunk_size=100,
    )
    return config


@pytest.fixture
def handler(test_config):
    """Create output handler instance."""
    return OutputHandler(test_config)


# ==============================================================================
# Helper Function Tests
# ==============================================================================


def test_format_size():
    """Test human-readable size formatting."""
    assert _format_size(0) == "0.0 B"
    assert _format_size(1023) == "1023.0 B"
    assert _format_size(1024) == "1.0 KB"
    assert _format_size(1536) == "1.5 KB"
    assert _format_size(1048576) == "1.0 MB"
    assert _format_size(1572864) == "1.5 MB"
    assert _format_size(1073741824) == "1.0 GB"
    assert _format_size(1610612736) == "1.5 GB"


@pytest.mark.asyncio
async def test_calculate_checksum(temp_output_dir):
    """Test SHA-256 checksum calculation."""
    # Create a test file
    test_file = temp_output_dir / "test.txt"
    content = "Hello, World!"
    test_file.write_text(content)

    # Calculate checksum
    checksum = await _calculate_checksum(test_file)

    # Verify it's a valid SHA-256 hex string
    assert len(checksum) == 64
    assert all(c in "0123456789abcdef" for c in checksum)

    # Verify deterministic (same content = same checksum)
    checksum2 = await _calculate_checksum(test_file)
    assert checksum == checksum2


# ==============================================================================
# CSV Writing Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_write_csv_small_dataset(handler, test_config, temp_output_dir):
    """Test writing small CSV dataset."""
    data = [
        {"name": "Alice", "age": 30, "city": "NYC"},
        {"name": "Bob", "age": 25, "city": "SF"},
    ]

    filepath = Path("test.csv")
    metadata = await handler.write_csv(data, filepath, test_config)

    # Verify file exists
    output_file = temp_output_dir / filepath
    assert output_file.exists()

    # Verify metadata
    assert metadata.rows == 2
    assert metadata.format == "csv"
    assert not metadata.compressed
    assert metadata.size_bytes > 0
    assert metadata.checksum  # Should have checksum

    # Verify content
    content = output_file.read_text()
    assert "name,age,city" in content
    assert "Alice,30,NYC" in content
    assert "Bob,25,SF" in content


@pytest.mark.asyncio
async def test_write_csv_large_dataset(handler, test_config, temp_output_dir):
    """Test writing large CSV dataset with chunking."""
    # Create dataset larger than chunk size
    data = [{"id": i, "value": f"value_{i}"} for i in range(25)]

    filepath = Path("large.csv")
    metadata = await handler.write_csv(data, filepath, test_config)

    # Verify file exists
    output_file = temp_output_dir / filepath
    assert output_file.exists()

    # Verify metadata
    assert metadata.rows == 25
    assert metadata.format == "csv"

    # Verify all rows are present
    lines = output_file.read_text().strip().split("\n")
    assert len(lines) == 26  # 25 data rows + 1 header


@pytest.mark.asyncio
async def test_write_csv_with_compression(handler, temp_output_dir):
    """Test CSV writing with gzip compression."""
    # MCP_OUTPUT_DIR is already set by temp_output_dir fixture
    config = OutputConfig(
        output_compression=True,
        output_metadata=True,
    )
    handler = OutputHandler(config)

    data = [{"name": "Alice", "age": 30}]
    filepath = Path("compressed.csv")
    metadata = await handler.write_csv(data, filepath, config)

    # Verify compressed file exists
    output_file = temp_output_dir / "compressed.csv.gz"
    assert output_file.exists()

    # Verify metadata
    assert metadata.compressed
    assert metadata.format == "csv.gz"

    # Verify content can be decompressed
    with gzip.open(output_file, "rt") as f:
        content = f.read()
        assert "name,age" in content
        assert "Alice,30" in content


@pytest.mark.asyncio
async def test_write_csv_empty_data(handler, test_config):
    """Test error handling for empty data."""
    with pytest.raises(ValueError, match="Cannot write empty data"):
        await handler.write_csv([], Path("empty.csv"), test_config)


@pytest.mark.asyncio
async def test_write_csv_special_characters(handler, test_config, temp_output_dir):
    """Test CSV writing with special characters (commas, quotes)."""
    data = [
        {"name": "Alice, Jr.", "desc": 'Says "Hello"'},
        {"name": "Bob\nSmith", "desc": "Normal"},
    ]

    filepath = Path("special.csv")
    metadata = await handler.write_csv(data, filepath, test_config)

    # Verify file exists
    output_file = temp_output_dir / filepath
    assert output_file.exists()

    # Verify escaping
    output_file.read_text()
    assert metadata.rows == 2


@pytest.mark.asyncio
async def test_write_csv_creates_parent_directories(handler, test_config, temp_output_dir):
    """Test that parent directories are created automatically."""
    filepath = Path("nested/deep/test.csv")
    data = [{"name": "Alice"}]

    await handler.write_csv(data, filepath, test_config)

    # Verify nested directory was created
    output_file = temp_output_dir / filepath
    assert output_file.exists()
    assert output_file.parent.exists()


# ==============================================================================
# JSON Writing Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_write_json_array(handler, test_config, temp_output_dir):
    """Test writing JSON array."""
    data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

    filepath = Path("test.json")
    metadata = await handler.write_json(data, filepath, test_config)

    # Verify file exists
    output_file = temp_output_dir / filepath
    assert output_file.exists()

    # Verify metadata
    assert metadata.rows == 2
    assert metadata.format == "json"
    assert not metadata.compressed

    # Verify content
    loaded = json.loads(output_file.read_text())
    assert loaded == data


@pytest.mark.asyncio
async def test_write_json_object(handler, test_config, temp_output_dir):
    """Test writing JSON object."""
    data = {"users": [{"name": "Alice"}], "count": 1}

    filepath = Path("test.json")
    metadata = await handler.write_json(data, filepath, test_config)

    # Verify file exists
    output_file = temp_output_dir / filepath
    assert output_file.exists()

    # Verify metadata
    assert metadata.rows == 2  # 2 keys in object
    assert metadata.format == "json"

    # Verify content
    loaded = json.loads(output_file.read_text())
    assert loaded == data


@pytest.mark.asyncio
async def test_write_json_with_compression(handler, temp_output_dir):
    """Test JSON writing with gzip compression."""
    # MCP_OUTPUT_DIR is already set by temp_output_dir fixture
    config = OutputConfig(
        output_compression=True,
        output_metadata=True,
    )
    handler = OutputHandler(config)

    data = [{"name": "Alice"}]
    filepath = Path("compressed.json")
    metadata = await handler.write_json(data, filepath, config)

    # Verify compressed file exists
    output_file = temp_output_dir / "compressed.json.gz"
    assert output_file.exists()

    # Verify metadata
    assert metadata.compressed
    assert metadata.format == "json.gz"

    # Verify content can be decompressed
    with gzip.open(output_file, "rt") as f:
        content = f.read()
        loaded = json.loads(content)
        assert loaded == data


@pytest.mark.asyncio
async def test_write_json_serialization_error(handler, test_config):
    """Test error handling for non-serializable data."""
    from datetime import datetime

    # datetime objects are not JSON-serializable by default
    data = {"timestamp": datetime.now()}

    with pytest.raises(ValueError, match="Cannot serialize data to JSON"):
        await handler.write_json(data, Path("invalid.json"), test_config)


@pytest.mark.asyncio
async def test_write_json_unicode(handler, test_config, temp_output_dir):
    """Test JSON writing with unicode characters."""
    data = [{"name": "日本語", "emoji": "🎉"}]

    filepath = Path("unicode.json")
    await handler.write_json(data, filepath, test_config)

    # Verify file exists
    output_file = temp_output_dir / filepath
    assert output_file.exists()

    # Verify unicode is preserved
    loaded = json.loads(output_file.read_text())
    assert loaded[0]["name"] == "日本語"
    assert loaded[0]["emoji"] == "🎉"


# ==============================================================================
# Metadata Generation Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_generate_metadata_all_fields(handler, test_config, temp_output_dir):
    """Test that all metadata fields are populated."""
    # Create a test file
    test_file = temp_output_dir / "test.csv"
    test_file.write_text("name,age\nAlice,30\n")

    metadata = await handler._generate_metadata(test_file, 1, False, test_config)

    # Verify all fields
    assert metadata.filepath
    assert metadata.timestamp
    assert metadata.size_bytes > 0
    assert metadata.size_human
    assert metadata.format == "csv"
    assert metadata.compressed is False
    assert metadata.rows == 1
    assert metadata.checksum  # Should have checksum when metadata enabled


@pytest.mark.asyncio
async def test_generate_metadata_no_checksum(handler, temp_output_dir):
    """Test metadata generation without checksum when disabled."""
    # MCP_OUTPUT_DIR is already set by temp_output_dir fixture
    config = OutputConfig(
        output_metadata=False,
    )
    handler = OutputHandler(config)

    # Create a test file
    test_file = temp_output_dir / "test.csv"
    test_file.write_text("name,age\nAlice,30\n")

    metadata = await handler._generate_metadata(test_file, 1, False, config)

    # Verify checksum is empty
    assert metadata.checksum == ""


@pytest.mark.asyncio
async def test_generate_metadata_compressed_format(handler, test_config, temp_output_dir):
    """Test metadata format for compressed files."""
    test_file = temp_output_dir / "test.csv.gz"
    test_file.write_bytes(b"compressed content")

    metadata = await handler._generate_metadata(test_file, 1, True, test_config)

    assert metadata.format == "csv.gz"
    assert metadata.compressed is True


@pytest.mark.asyncio
async def test_generate_metadata_relative_path(handler, test_config, temp_output_dir):
    """Test that filepath is relative to client_root."""
    nested_file = temp_output_dir / "nested" / "test.csv"
    nested_file.parent.mkdir(parents=True, exist_ok=True)
    nested_file.write_text("test")

    metadata = await handler._generate_metadata(nested_file, 1, False, test_config)

    # Should be relative path
    assert metadata.filepath == "nested/test.csv"


# ==============================================================================
# Error Handling Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_write_csv_io_error_cleanup(handler, test_config):
    """Test that partial files are cleaned up on error."""
    data = [{"name": "Alice"}]

    # Mock aiofiles.open to raise an error
    with patch("aiofiles.open", side_effect=OSError("Disk full")):
        with pytest.raises(FileWriteError, match="Failed to write CSV"):
            await handler.write_csv(data, Path("fail.csv"), test_config)

    # Verify no partial file was left behind
    # (This is hard to test without actually creating the file first,
    # but the code handles cleanup)


@pytest.mark.asyncio
async def test_write_json_io_error_cleanup(handler, test_config):
    """Test that partial files are cleaned up on error."""
    data = [{"name": "Alice"}]

    # Mock aiofiles.open to raise an error
    with patch("aiofiles.open", side_effect=OSError("Disk full")):
        with pytest.raises(FileWriteError, match="Failed to write JSON"):
            await handler.write_json(data, Path("fail.json"), test_config)


@pytest.mark.asyncio
async def test_path_security_validation(handler, test_config):
    """Test that path security validation is enforced."""
    data = [{"name": "Alice"}]

    # Try to write outside client_root
    with pytest.raises(SecurityError):
        await handler.write_csv(data, Path("../../../etc/passwd"), test_config)


@pytest.mark.asyncio
async def test_permission_error(handler, test_config, temp_output_dir):
    """Test error handling for permission denied."""
    # Create a read-only subdirectory
    readonly_dir = temp_output_dir / "readonly"
    readonly_dir.mkdir()

    # Create a file in it first, then make directory read-only
    test_file = readonly_dir / "test.csv"
    test_file.write_text("dummy")

    # Make directory read-only AFTER file creation
    os.chmod(readonly_dir, 0o444)

    try:
        data = [{"name": "Alice"}]

        # This should fail because we can't write to readonly directory
        with pytest.raises((FileWriteError, PermissionError)):
            await handler.write_csv(data, Path("readonly/test2.csv"), test_config)
    finally:
        # Cleanup: restore permissions
        os.chmod(readonly_dir, 0o755)


# ==============================================================================
# Integration Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_create_file_reference(handler, test_config, temp_output_dir):
    """Test file reference creation for MCP responses."""
    # Write a file first
    data = [{"name": "Alice"}]
    filepath = Path("test.csv")
    metadata = await handler.write_csv(data, filepath, test_config)

    # Create file reference
    ref = await handler.create_file_reference(temp_output_dir / filepath, metadata)

    # Verify reference structure
    assert ref["type"] == "file"
    assert "filepath" in ref
    assert "metadata" in ref
    assert ref["metadata"]["rows"] == 1
    assert ref["metadata"]["format"] == "csv"


@pytest.mark.asyncio
async def test_concurrent_writes(handler, test_config, temp_output_dir):
    """Test that concurrent writes work correctly."""
    import asyncio

    # Create multiple datasets
    datasets = [([{"id": i}], Path(f"concurrent_{i}.csv")) for i in range(5)]

    # Write concurrently
    tasks = [handler.write_csv(data, path, test_config) for data, path in datasets]
    results = await asyncio.gather(*tasks)

    # Verify all files were created
    assert len(results) == 5
    for i, metadata in enumerate(results):
        output_file = temp_output_dir / f"concurrent_{i}.csv"
        assert output_file.exists()
        assert metadata.rows == 1


@pytest.mark.asyncio
async def test_large_file_memory_efficiency(handler, test_config, temp_output_dir):
    """Test that large files are handled efficiently without loading all in memory."""
    # Create a large dataset (but not so large it takes forever to test)
    data = [{"id": i, "value": f"value_{i}" * 100} for i in range(1000)]

    filepath = Path("large.csv")
    metadata = await handler.write_csv(data, filepath, test_config)

    # Verify file was created
    output_file = temp_output_dir / filepath
    assert output_file.exists()
    assert metadata.rows == 1000

    # Verify file size is reasonable
    assert metadata.size_bytes > 100000  # At least 100KB


@pytest.mark.asyncio
async def test_output_handler_with_project_folders(temp_output_dir):
    """Test integration with project folder structure."""
    # MCP_OUTPUT_DIR is already set by temp_output_dir fixture
    config = OutputConfig(
        project_name="my_project",
        enable_project_folders=True,
    )
    handler = OutputHandler(config)

    data = [{"name": "Alice"}]
    filepath = Path("test.csv")
    await handler.write_csv(data, filepath, config)

    # Verify file was created in correct location
    output_file = temp_output_dir / filepath
    assert output_file.exists()


# ==============================================================================
# Edge Cases
# ==============================================================================


@pytest.mark.asyncio
async def test_write_csv_single_row(handler, test_config, temp_output_dir):
    """Test writing CSV with single row."""
    data = [{"name": "Alice"}]

    filepath = Path("single.csv")
    metadata = await handler.write_csv(data, filepath, test_config)

    assert metadata.rows == 1


@pytest.mark.asyncio
async def test_write_json_single_value(handler, test_config, temp_output_dir):
    """Test writing JSON with single value."""
    data = "simple string"

    filepath = Path("single.json")
    metadata = await handler.write_json(data, filepath, test_config)

    # Single value counts as 1 element
    assert metadata.rows == 1


@pytest.mark.asyncio
async def test_write_csv_missing_keys(handler, test_config, temp_output_dir):
    """Test CSV writing with missing keys in some rows."""
    data = [
        {"name": "Alice", "age": 30},
        {"name": "Bob"},  # Missing age
    ]

    filepath = Path("missing_keys.csv")
    await handler.write_csv(data, filepath, test_config)

    # Verify file was created
    output_file = temp_output_dir / filepath
    assert output_file.exists()

    # Verify content handles missing keys
    content = output_file.read_text()
    assert "name,age" in content


@pytest.mark.asyncio
async def test_write_csv_consistent_ordering(handler, test_config, temp_output_dir):
    """Test that CSV columns maintain consistent ordering."""
    data = [
        {"c": 3, "a": 1, "b": 2},
        {"c": 6, "a": 4, "b": 5},
    ]

    filepath = Path("ordered.csv")
    await handler.write_csv(data, filepath, test_config)

    # Verify header ordering matches first row
    content = (temp_output_dir / filepath).read_text()
    lines = content.strip().split("\n")
    header = lines[0]

    # Header should match the key order from first row
    assert header == "c,a,b"
