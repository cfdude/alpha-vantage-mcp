"""
Integration helper functions for Alpha Vantage MCP Server output system.

This module provides standardized response helpers that integrate all Sprint 1 components:
- OutputConfig: Configuration management
- TokenEstimator: Intelligent token counting
- OutputHandler: File I/O operations
- Security validation: Path and permission checks
- Logging: Structured logging with context

The helper functions provide a clean, consistent interface for MCP tools to:
1. Decide whether to output data inline or to file
2. Create standardized file reference responses
3. Create standardized inline data responses

Examples:
    >>> from src.integration.helpers import should_use_output_helper, create_file_reference_response
    >>> from src.utils.output_config import OutputConfig
    >>> from pathlib import Path
    >>>
    >>> config = OutputConfig()
    >>> data = [{"id": 1, "value": "test"}]
    >>>
    >>> # Decide output method
    >>> decision = should_use_output_helper(data, config)
    >>> decision.use_file
    False
    >>> decision.reason
    'Below threshold (42 tokens < 1000 token threshold)'
    >>>
    >>> # Create inline response
    >>> if not decision.use_file:
    ...     response = create_inline_response(data, format="json")
    ...     response["type"]
    'inline_data'
"""

import csv
import io
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..decision.token_estimator import TokenEstimator
from ..output.handler import FileMetadata
from ..utils.output_config import OutputConfig
from .logging_config import get_logger, log_decision

# Initialize logger
logger = get_logger()


@dataclass
class OutputDecision:
    """
    Decision about whether to use file output or inline response.

    This dataclass encapsulates all information needed to make an informed
    decision about how to return data to the MCP client.

    Attributes:
        use_file: Whether to write data to file (True) or return inline (False).
        token_count: Estimated token count of the data.
        row_count: Number of rows/elements in the data.
        reason: Human-readable explanation of the decision.
        suggested_filename: Suggested filename if writing to file (based on timestamp and format).

    Examples:
        >>> decision = OutputDecision(
        ...     use_file=True,
        ...     token_count=5000,
        ...     row_count=1000,
        ...     reason="Exceeds token threshold (5000 > 1000)",
        ...     suggested_filename="output_2024-01-15_143022.csv"
        ... )
        >>> decision.use_file
        True
        >>> decision.reason
        'Exceeds token threshold (5000 > 1000)'
    """

    use_file: bool
    token_count: int
    row_count: int
    reason: str
    suggested_filename: str


def should_use_output_helper(
    data: Any,
    config: OutputConfig,
    force_inline: bool = False,
    force_file: bool = False,
    filename_prefix: str = "output",
    **kwargs: Any,
) -> OutputDecision:
    """
    Determine whether data should be written to file or returned inline.

    This function integrates TokenEstimator to make intelligent decisions based on:
    - Estimated token count vs configured threshold
    - Number of rows/elements vs configured limits
    - Override flags (force_inline, force_file)
    - Data format and complexity

    The function logs all decisions with structured context for debugging and auditing.

    Args:
        data: Data to evaluate (list of dicts for CSV, any JSON-serializable for JSON).
        config: Output configuration with thresholds and settings.
        force_inline: Force inline output regardless of size (default: False).
        force_file: Force file output regardless of size (default: False).
        filename_prefix: Prefix for suggested filename (default: "output").
        **kwargs: Additional context for logging.

    Returns:
        OutputDecision with all decision information.

    Raises:
        ValueError: If both force_inline and force_file are True.
        ValueError: If data is None or invalid.

    Examples:
        >>> from src.utils.output_config import OutputConfig
        >>> config = OutputConfig()
        >>>
        >>> # Small dataset - stays inline
        >>> data = [{"id": 1}, {"id": 2}]
        >>> decision = should_use_output_helper(data, config)
        >>> decision.use_file
        False
        >>> "Below threshold" in decision.reason
        True
        >>>
        >>> # Large dataset - goes to file
        >>> large_data = [{"id": i, "data": "x" * 100} for i in range(100)]
        >>> decision = should_use_output_helper(large_data, config)
        >>> decision.use_file
        True
        >>>
        >>> # Force inline override
        >>> decision = should_use_output_helper(large_data, config, force_inline=True)
        >>> decision.use_file
        False
        >>> "Forced to inline" in decision.reason
        True
        >>>
        >>> # Custom filename prefix
        >>> decision = should_use_output_helper(data, config, filename_prefix="stocks")
        >>> decision.suggested_filename.startswith("stocks_")
        True
    """
    # Validate data
    if data is None:
        raise ValueError("data cannot be None")

    # Check for empty data
    if isinstance(data, list | dict) and len(data) == 0:
        raise ValueError("Cannot process empty data")

    # Validate override flags
    if force_inline and force_file:
        raise ValueError(
            "Cannot specify both force_inline=True and force_file=True. "
            "Choose one override or neither for automatic decision."
        )

    # Initialize token estimator
    estimator = TokenEstimator()

    # Get token estimation and decision from TokenEstimator
    should_file, token_count, reason = estimator.should_output_to_file(
        data, config, force_inline=force_inline, force_file=force_file
    )

    # Calculate row/element count
    row_count = 0
    if isinstance(data, list):
        row_count = len(data)
    elif isinstance(data, dict):
        row_count = len(data)
    else:
        row_count = 1

    # Determine format for filename suggestion
    if isinstance(data, list) and data and isinstance(data[0], dict):
        format_ext = config.output_format  # csv or json
    else:
        format_ext = "json"

    # Generate suggested filename with timestamp
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M%S")
    suggested_filename = f"{filename_prefix}_{timestamp}.{format_ext}"

    # Add compression extension if enabled
    if config.output_compression:
        suggested_filename += ".gz"

    # Create decision object
    decision = OutputDecision(
        use_file=should_file,
        token_count=token_count,
        row_count=row_count,
        reason=reason,
        suggested_filename=suggested_filename,
    )

    # Determine decision type for logging
    if force_inline:
        decision_type = "forced_inline"
    elif force_file:
        decision_type = "forced_file"
    else:
        decision_type = "automatic"

    # Log the decision with structured context
    log_decision(
        decision_type=decision_type,
        use_file=should_file,
        token_count=token_count,
        row_count=row_count,
        reason=reason,
        threshold=config.output_token_threshold,
        suggested_filename=suggested_filename,
        **kwargs,
    )

    return decision


def create_file_reference_response(
    filepath: Path,
    metadata: FileMetadata,
    config: OutputConfig,
) -> dict[str, Any]:
    """
    Create a standardized file reference response for MCP tools.

    This function generates a consistent response format when data has been
    written to a file. The response includes all necessary metadata for the
    client to access and understand the file.

    Args:
        filepath: Path to the file (can be absolute or relative to client_root).
        metadata: File metadata from OutputHandler.
        config: Output configuration for path resolution.

    Returns:
        Dictionary with standardized file reference format:
        - type: "file_reference" (identifies response type)
        - filepath: str (relative path from client_root for portability)
        - filename: str (just the filename for display)
        - size: int (file size in bytes)
        - size_formatted: str (human-readable size like "1.5 MB")
        - format: str (csv, json, csv.gz, json.gz)
        - compressed: bool (whether file is gzipped)
        - rows: int (number of rows/elements)
        - timestamp: str (ISO format timestamp)
        - checksum: str (SHA-256 hash for data integrity)
        - metadata: dict (optional full metadata if config.output_metadata=True)

    Examples:
        >>> from pathlib import Path
        >>> from src.output.handler import FileMetadata
        >>> from src.utils.output_config import OutputConfig
        >>>
        >>> config = OutputConfig()
        >>> metadata = FileMetadata(
        ...     filepath="output.csv",
        ...     timestamp="2024-01-15T14:30:22Z",
        ...     size_bytes=1048576,
        ...     size_human="1.0 MB",
        ...     format="csv",
        ...     compressed=False,
        ...     rows=1000,
        ...     checksum="abc123..."
        ... )
        >>> filepath = config.client_root / "output.csv"
        >>>
        >>> response = create_file_reference_response(filepath, metadata, config)
        >>> response["type"]
        'file_reference'
        >>> response["filename"]
        'output.csv'
        >>> response["rows"]
        1000
    """
    # Get relative path from client_root for portability
    try:
        relative_path = filepath.relative_to(config.client_root)
    except ValueError:
        # If path is not relative to client_root, use the path as-is
        relative_path = Path(metadata.filepath)

    # Build response
    response = {
        "type": "file_reference",
        "filepath": str(relative_path),
        "filename": filepath.name,
        "size": metadata.size_bytes,
        "size_formatted": metadata.size_human,
        "format": metadata.format,
        "compressed": metadata.compressed,
        "rows": metadata.rows,
        "timestamp": metadata.timestamp,
        "checksum": metadata.checksum,
    }

    # Include full metadata if enabled
    if config.output_metadata:
        response["metadata"] = {
            "filepath": metadata.filepath,
            "timestamp": metadata.timestamp,
            "size_bytes": metadata.size_bytes,
            "size_human": metadata.size_human,
            "format": metadata.format,
            "compressed": metadata.compressed,
            "rows": metadata.rows,
            "checksum": metadata.checksum,
        }

    logger.debug(
        "Created file reference response",
        filepath=str(relative_path),
        size=metadata.size_bytes,
        rows=metadata.rows,
        format=metadata.format,
    )

    return response


def create_inline_response(
    data: Any,
    format: str = "json",
) -> dict[str, Any]:
    """
    Create a standardized inline data response for MCP tools.

    This function generates a consistent response format when returning data
    directly to the client (not written to file). Handles both JSON and CSV formats.

    For CSV format, converts list of dicts to CSV string with headers.
    For JSON format, returns data directly (client handles serialization).

    Args:
        data: Data to include in response (list, dict, or JSON-serializable).
        format: Output format - "json" or "csv" (default: "json").

    Returns:
        Dictionary with standardized inline response format:
        - type: "inline_data" (identifies response type)
        - format: str (json or csv)
        - data: Any (the actual data - list/dict for JSON, string for CSV)
        - row_count: int (number of rows/elements)
        - timestamp: str (ISO format timestamp)

    Raises:
        ValueError: If format is invalid or data cannot be converted.

    Examples:
        >>> # JSON format - returns data directly
        >>> data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        >>> response = create_inline_response(data, format="json")
        >>> response["type"]
        'inline_data'
        >>> response["format"]
        'json'
        >>> response["data"]
        [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
        >>> response["row_count"]
        2
        >>>
        >>> # CSV format - converts to CSV string
        >>> response = create_inline_response(data, format="csv")
        >>> response["format"]
        'csv'
        >>> "id,name" in response["data"]
        True
        >>> "Alice" in response["data"]
        True
        >>>
        >>> # Works with dicts
        >>> data = {"key": "value", "number": 42}
        >>> response = create_inline_response(data)
        >>> response["data"]["key"]
        'value'
    """
    # Validate format
    valid_formats = ["json", "csv"]
    if format not in valid_formats:
        raise ValueError(f"Invalid format: {format}. Must be one of: {', '.join(valid_formats)}")

    # Calculate row count
    row_count = 0
    if isinstance(data, list):
        row_count = len(data)
    elif isinstance(data, dict):
        row_count = len(data)
    else:
        row_count = 1

    # Convert to CSV if requested
    if format == "csv":
        if not isinstance(data, list) or not data or not isinstance(data[0], dict):
            raise ValueError(
                "CSV format requires data to be a non-empty list of dictionaries. "
                f"Got: {type(data)}"
            )

        # Convert list of dicts to CSV string
        output = io.StringIO()
        headers = list(data[0].keys())
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        csv_string = output.getvalue()

        response_data = csv_string
    else:
        # JSON format - return data as-is (client handles serialization)
        response_data = data

    # Build response
    response = {
        "type": "inline_data",
        "format": format,
        "data": response_data,
        "row_count": row_count,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    logger.debug(
        "Created inline response",
        format=format,
        row_count=row_count,
        data_type=type(data).__name__,
    )

    return response
