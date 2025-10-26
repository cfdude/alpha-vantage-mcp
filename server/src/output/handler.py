"""
Output handler for Alpha Vantage MCP server.

This module provides async file I/O operations with:
- Streaming CSV/JSON writing for large datasets
- Optional gzip compression
- Comprehensive metadata generation
- Robust error handling with retries
- Path security validation
"""

import asyncio
import csv
import gzip
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.os

from ..utils.output_config import OutputConfig
from ..utils.security import SecurityError, sanitize_filename, validate_safe_path


class OutputHandlerError(Exception):
    """Base exception for output handler errors."""

    pass


class FileWriteError(OutputHandlerError):
    """Exception raised when file write operations fail."""

    pass


@dataclass
class FileMetadata:
    """
    Metadata for output files.

    Attributes:
        filepath: Path to the file (relative to client_root for portability).
        timestamp: ISO-format timestamp with timezone.
        size_bytes: File size in bytes.
        size_human: Human-readable file size (KB, MB, GB).
        format: File format (csv, json, csv.gz, json.gz).
        compressed: Whether file is gzip compressed.
        rows: Number of data rows (CSV) or elements (JSON).
        checksum: SHA-256 checksum for data integrity.
    """

    filepath: str
    timestamp: str
    size_bytes: int
    size_human: str
    format: str
    compressed: bool
    rows: int
    checksum: str = ""


@dataclass
class FileInfo:
    """
    Information about a file in a project.

    Attributes:
        name: Name of the file.
        size: File size in bytes.
        modified_time: Last modified time (ISO format).
        format: File format (csv, json, csv.gz, json.gz).
    """

    name: str
    size: int
    modified_time: str
    format: str


@dataclass
class ProjectInfo:
    """
    Information about a project folder.

    Attributes:
        name: Project name.
        file_count: Number of files in the project.
        total_size: Total size of all files in bytes.
        last_modified: Last modified time (ISO format).
    """

    name: str
    file_count: int
    total_size: int
    last_modified: str


def _format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Human-readable size string (e.g., "1.5 MB").

    Examples:
        >>> _format_size(1024)
        '1.0 KB'
        >>> _format_size(1536000)
        '1.5 MB'
        >>> _format_size(1610612736)
        '1.5 GB'
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


async def _calculate_checksum(filepath: Path) -> str:
    """
    Calculate SHA-256 checksum for a file.

    Args:
        filepath: Path to the file.

    Returns:
        Hex-encoded SHA-256 checksum.
    """
    sha256_hash = hashlib.sha256()
    async with aiofiles.open(filepath, "rb") as f:
        while chunk := await f.read(8192):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


async def _retry_operation(operation, max_retries: int = 3, backoff_base: float = 0.5):
    """
    Retry an async operation with exponential backoff.

    Args:
        operation: Async callable to retry.
        max_retries: Maximum number of retry attempts.
        backoff_base: Base delay in seconds (doubles each retry).

    Returns:
        Result of the operation.

    Raises:
        The last exception encountered if all retries fail.
    """
    last_exception = None
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = backoff_base * (2**attempt)
                await asyncio.sleep(delay)

    raise last_exception


class OutputHandler:
    """
    Async file output handler with streaming, compression, and metadata.

    This handler provides:
    - Async CSV/JSON writing with streaming for large datasets
    - Optional gzip compression
    - Comprehensive metadata generation
    - Error handling with retry logic
    - Security validation for all paths

    Examples:
        >>> config = OutputConfig()
        >>> handler = OutputHandler(config)
        >>> data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        >>> metadata = await handler.write_csv(data, Path("output.csv"), config)
        >>> metadata.rows
        2
        >>> metadata.format
        'csv'
    """

    def __init__(self, config: OutputConfig):
        """
        Initialize output handler.

        Args:
            config: Output configuration.
        """
        self.config = config

    async def write_csv(
        self, data: list[dict], filepath: Path, config: OutputConfig
    ) -> FileMetadata:
        """
        Write data to CSV file with async streaming.

        Features:
        - Async file I/O using aiofiles
        - Streaming for large datasets (chunked writing)
        - Optional gzip compression
        - Automatic header generation from dict keys
        - Memory efficient (doesn't load all data in memory)

        Args:
            data: List of dictionaries to write.
            filepath: Target file path (relative to client_root).
            config: Output configuration.

        Returns:
            FileMetadata with file information.

        Raises:
            FileWriteError: If write operation fails after retries.
            ValueError: If data is empty or invalid.

        Examples:
            >>> data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
            >>> metadata = await handler.write_csv(data, Path("users.csv"), config)
            >>> metadata.rows
            2
        """
        if not data:
            raise ValueError("Cannot write empty data to CSV")

        # Validate and secure the path (without permission check yet)
        safe_path = validate_safe_path(filepath, config.client_root, check_permissions=False)

        # Ensure parent directory exists
        safe_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine if we should compress
        compress = config.output_compression
        output_path = safe_path.with_suffix(safe_path.suffix + ".gz") if compress else safe_path

        try:
            # Write CSV with retry logic
            async def _write():
                if compress:
                    # Write to gzip file
                    with gzip.open(output_path, "wt", encoding="utf-8") as f:
                        # Get headers from first row
                        headers = list(data[0].keys())
                        writer = csv.DictWriter(f, fieldnames=headers)
                        writer.writeheader()

                        # Write data in chunks
                        chunk_size = config.streaming_chunk_size
                        for i in range(0, len(data), chunk_size):
                            chunk = data[i : i + chunk_size]
                            writer.writerows(chunk)
                else:
                    # Write to regular file with async I/O
                    async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
                        # Get headers from first row
                        headers = list(data[0].keys())

                        # Write header
                        await f.write(",".join(headers) + "\n")

                        # Write data in chunks
                        chunk_size = config.streaming_chunk_size
                        for i in range(0, len(data), chunk_size):
                            chunk = data[i : i + chunk_size]
                            # Convert chunk to CSV lines
                            lines = []
                            for row in chunk:
                                values = [str(row.get(h, "")) for h in headers]
                                # Escape commas and quotes
                                escaped_values = []
                                for v in values:
                                    if "," in v or '"' in v or "\n" in v:
                                        escaped_values.append(
                                            f'"{v.replace(chr(34), chr(34) + chr(34))}"'
                                        )
                                    else:
                                        escaped_values.append(v)
                                lines.append(",".join(escaped_values))
                            await f.write("\n".join(lines) + "\n")

            await _retry_operation(_write, max_retries=3)

            # Generate metadata
            metadata = await self._generate_metadata(output_path, len(data), compress, config)
            return metadata

        except Exception as e:
            # Cleanup partial file on error
            if output_path.exists():
                try:
                    await aiofiles.os.remove(output_path)
                except Exception:
                    pass  # Best effort cleanup

            raise FileWriteError(
                f"Failed to write CSV file {output_path}: {e}. Check disk space and permissions."
            ) from e

    async def write_json(self, data: Any, filepath: Path, config: OutputConfig) -> FileMetadata:
        """
        Write data to JSON file with async streaming.

        Features:
        - Async file I/O using aiofiles
        - Supports both array and object data
        - Pretty-printed JSON (indent=2)
        - Optional gzip compression
        - Proper JSON serialization error handling

        Args:
            data: Data to write (list, dict, or any JSON-serializable object).
            filepath: Target file path (relative to client_root).
            config: Output configuration.

        Returns:
            FileMetadata with file information.

        Raises:
            FileWriteError: If write operation fails after retries.
            ValueError: If data cannot be serialized to JSON.

        Examples:
            >>> data = [{"name": "Alice"}, {"name": "Bob"}]
            >>> metadata = await handler.write_json(data, Path("users.json"), config)
            >>> metadata.format
            'json'
        """
        # Validate and secure the path (without permission check yet)
        safe_path = validate_safe_path(filepath, config.client_root, check_permissions=False)

        # Ensure parent directory exists
        safe_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine if we should compress
        compress = config.output_compression
        output_path = safe_path.with_suffix(safe_path.suffix + ".gz") if compress else safe_path

        try:
            # Serialize data first to catch serialization errors early
            try:
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
            except (TypeError, ValueError) as e:
                raise ValueError(
                    f"Cannot serialize data to JSON: {e}. "
                    "Ensure all data is JSON-serializable (no datetime, Decimal, etc.)."
                ) from e

            # Write JSON with retry logic
            async def _write():
                if compress:
                    # Write to gzip file
                    with gzip.open(output_path, "wt", encoding="utf-8") as f:
                        f.write(json_str)
                else:
                    # Write to regular file with async I/O
                    async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
                        await f.write(json_str)

            await _retry_operation(_write, max_retries=3)

            # Count elements
            element_count = 0
            if isinstance(data, list):
                element_count = len(data)
            elif isinstance(data, dict):
                element_count = len(data)
            else:
                element_count = 1

            # Generate metadata
            metadata = await self._generate_metadata(output_path, element_count, compress, config)
            return metadata

        except ValueError:
            # Re-raise serialization errors as-is
            raise
        except Exception as e:
            # Cleanup partial file on error
            if output_path.exists():
                try:
                    await aiofiles.os.remove(output_path)
                except Exception:
                    pass  # Best effort cleanup

            raise FileWriteError(
                f"Failed to write JSON file {output_path}: {e}. Check disk space and permissions."
            ) from e

    async def _generate_metadata(
        self, filepath: Path, row_count: int, compressed: bool, config: OutputConfig
    ) -> FileMetadata:
        """
        Generate comprehensive metadata for a file.

        Args:
            filepath: Path to the file.
            row_count: Number of rows/elements in the file.
            compressed: Whether file is compressed.
            config: Output configuration.

        Returns:
            FileMetadata with all information.
        """
        # Get file size
        stat = await aiofiles.os.stat(filepath)
        size_bytes = stat.st_size

        # Calculate checksum if metadata is enabled
        checksum = ""
        if config.output_metadata:
            checksum = await _calculate_checksum(filepath)

        # Determine format
        suffix = filepath.suffix
        if compressed:
            # Remove .gz to get the actual format
            base_suffix = filepath.stem.split(".")[-1]
            format_str = f"{base_suffix}.gz"
        else:
            format_str = suffix.lstrip(".")

        # Get relative path for portability
        try:
            relative_path = filepath.relative_to(config.client_root)
        except ValueError:
            # If path is not relative to client_root, use absolute path
            relative_path = filepath

        return FileMetadata(
            filepath=str(relative_path),
            timestamp=datetime.now(UTC).isoformat(),
            size_bytes=size_bytes,
            size_human=_format_size(size_bytes),
            format=format_str,
            compressed=compressed,
            rows=row_count,
            checksum=checksum,
        )

    async def create_file_reference(self, filepath: Path, metadata: FileMetadata) -> dict:
        """
        Create a file reference dictionary for MCP responses.

        Args:
            filepath: Path to the file.
            metadata: File metadata.

        Returns:
            Dictionary with file reference information.

        Examples:
            >>> ref = await handler.create_file_reference(Path("output.csv"), metadata)
            >>> ref["type"]
            'file'
            >>> "filepath" in ref
            True
        """
        return {
            "type": "file",
            "filepath": str(filepath),
            "metadata": {
                "timestamp": metadata.timestamp,
                "size_bytes": metadata.size_bytes,
                "size_human": metadata.size_human,
                "format": metadata.format,
                "compressed": metadata.compressed,
                "rows": metadata.rows,
                "checksum": metadata.checksum,
            },
        }

    async def create_project_folder(self, project_name: str) -> Path:
        """
        Create a project subdirectory under client_root.

        This method is idempotent - it will succeed even if the folder already exists.
        All project names are sanitized for security to prevent directory traversal attacks.

        Args:
            project_name: Name of the project (will be sanitized).

        Returns:
            Path: The created project folder path.

        Raises:
            ValueError: If project_name is empty or invalid.
            PermissionError: If unable to create folder due to permissions.
            OutputHandlerError: If folder creation fails for other reasons.

        Examples:
            >>> handler = OutputHandler(config)
            >>> project_path = await handler.create_project_folder("my-project")
            >>> project_path.exists()
            True

            >>> # Idempotent - calling again returns same path
            >>> project_path2 = await handler.create_project_folder("my-project")
            >>> project_path == project_path2
            True

            >>> # Dangerous names are sanitized
            >>> path = await handler.create_project_folder("../etc/passwd")
            >>> path.name
            'etcpasswd'
        """
        if not project_name or not isinstance(project_name, str):
            raise ValueError("project_name must be a non-empty string")

        # Sanitize project name for security
        safe_name = sanitize_filename(project_name)
        if not safe_name:
            raise ValueError(f"Invalid project name after sanitization: {project_name}")

        # Create full project path
        project_path = self.config.client_root / safe_name

        try:
            # Create directory with configured permissions (idempotent with exist_ok=True)
            project_path.mkdir(
                mode=self.config.default_folder_permissions,
                parents=True,
                exist_ok=True,
            )
            return project_path

        except PermissionError as e:
            raise PermissionError(
                f"Cannot create project folder {project_path}: {e}. "
                "Check directory permissions and ensure you have write access."
            ) from e
        except Exception as e:
            raise OutputHandlerError(
                f"Failed to create project folder {project_path}: {e}. "
                "Check disk space and path validity."
            ) from e

    async def list_project_files(self, project_name: str, pattern: str = "*") -> list[FileInfo]:
        """
        List all files in a project folder with optional pattern filtering.

        Files are listed recursively and sorted by modified time (newest first).
        Supports glob patterns for filtering (e.g., "*.csv", "2024-*.json").

        Args:
            project_name: Name of the project.
            pattern: Glob pattern for filtering files (default: "*" for all files).

        Returns:
            List of FileInfo objects sorted by modified time (newest first).
            Returns empty list if project doesn't exist or has no matching files.

        Raises:
            ValueError: If project_name is empty or invalid.
            PermissionError: If unable to access project folder.

        Examples:
            >>> files = await handler.list_project_files("my-project")
            >>> len(files)
            5

            >>> # Filter by pattern
            >>> csv_files = await handler.list_project_files("my-project", "*.csv")
            >>> all(f.format.startswith("csv") for f in csv_files)
            True

            >>> # Get files from specific time period
            >>> jan_files = await handler.list_project_files("stocks", "2024-01-*.csv")
        """
        if not project_name or not isinstance(project_name, str):
            raise ValueError("project_name must be a non-empty string")

        # Sanitize project name
        safe_name = sanitize_filename(project_name)
        project_path = self.config.client_root / safe_name

        # Return empty list if project doesn't exist
        if not project_path.exists():
            return []

        if not project_path.is_dir():
            raise ValueError(f"Path exists but is not a directory: {project_path}")

        try:
            # Collect all matching files
            file_infos = []

            # Use rglob for recursive glob matching
            for file_path in project_path.rglob(pattern):
                if file_path.is_file():
                    stat = await aiofiles.os.stat(file_path)

                    # Determine file format
                    suffix = file_path.suffix.lstrip(".")
                    if file_path.suffixes and len(file_path.suffixes) >= 2:
                        # Handle .csv.gz, .json.gz
                        if file_path.suffixes[-1] == ".gz":
                            suffix = f"{file_path.suffixes[-2].lstrip('.')}.gz"

                    file_info = FileInfo(
                        name=str(file_path.relative_to(project_path)),
                        size=stat.st_size,
                        modified_time=datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
                        format=suffix,
                    )
                    file_infos.append((stat.st_mtime, file_info))

            # Sort by modified time (newest first) and return FileInfo objects
            file_infos.sort(key=lambda x: x[0], reverse=True)
            return [info for _, info in file_infos]

        except PermissionError as e:
            raise PermissionError(
                f"Cannot access project folder {project_path}: {e}. Check directory permissions."
            ) from e

    async def delete_project_file(self, project_name: str, filename: str) -> bool:
        """
        Delete a specific file from a project folder.

        This method includes security validation to prevent path traversal attacks.
        It will not delete directories, only files.

        Args:
            project_name: Name of the project.
            filename: Name of the file to delete (relative to project folder).

        Returns:
            bool: True if file was deleted, False if file didn't exist.

        Raises:
            ValueError: If project_name or filename is empty/invalid.
            SecurityError: If filename attempts to escape project folder.
            PermissionError: If unable to delete file due to permissions.
            OutputHandlerError: If deletion fails for other reasons.

        Examples:
            >>> # Delete a file
            >>> deleted = await handler.delete_project_file("stocks", "old_data.csv")
            >>> deleted
            True

            >>> # Deleting non-existent file returns False
            >>> deleted = await handler.delete_project_file("stocks", "missing.csv")
            >>> deleted
            False

            >>> # Works with compressed files
            >>> deleted = await handler.delete_project_file("stocks", "data.csv.gz")
            >>> deleted
            True

            >>> # Security: Path traversal is blocked
            >>> await handler.delete_project_file("stocks", "../other/file.csv")
            SecurityError: Path escapes project folder
        """
        if not project_name or not isinstance(project_name, str):
            raise ValueError("project_name must be a non-empty string")

        if not filename or not isinstance(filename, str):
            raise ValueError("filename must be a non-empty string")

        # Sanitize project name and filename
        safe_project_name = sanitize_filename(project_name)
        safe_filename = sanitize_filename(filename)

        project_path = self.config.client_root / safe_project_name

        # Construct file path and validate it's contained within project
        file_path = project_path / safe_filename

        # Security validation - ensure file path is within project folder
        try:
            resolved_file = file_path.resolve(strict=False)
            resolved_project = project_path.resolve(strict=True)

            if not resolved_file.is_relative_to(resolved_project):
                raise SecurityError(
                    f"Path traversal detected: {filename} escapes project folder {project_name}"
                )
        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise ValueError(f"Cannot resolve file path: {e}") from e

        # Return False if file doesn't exist
        if not file_path.exists():
            return False

        # Don't delete directories
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {filename}")

        try:
            await aiofiles.os.remove(file_path)
            return True

        except PermissionError as e:
            raise PermissionError(
                f"Cannot delete file {file_path}: {e}. Check file permissions."
            ) from e
        except Exception as e:
            raise OutputHandlerError(f"Failed to delete file {file_path}: {e}") from e

    async def list_projects(self) -> list[ProjectInfo]:
        """
        List all project folders under client_root.

        Projects are sorted by last modified time (newest first).
        Hidden folders (starting with '.') are excluded.

        Returns:
            List of ProjectInfo objects with metadata about each project.
            Returns empty list if no projects exist.

        Raises:
            PermissionError: If unable to access client_root.

        Examples:
            >>> projects = await handler.list_projects()
            >>> len(projects)
            3

            >>> # Projects are sorted by last modified
            >>> projects[0].last_modified > projects[1].last_modified
            True

            >>> # Each project has metadata
            >>> project = projects[0]
            >>> project.name
            'stock-analysis'
            >>> project.file_count
            15
            >>> project.total_size
            1048576
        """
        try:
            project_infos = []

            # Iterate through directories in client_root
            for item in self.config.client_root.iterdir():
                # Skip non-directories and hidden folders
                if not item.is_dir() or item.name.startswith("."):
                    continue

                # Calculate project stats
                file_count = 0
                total_size = 0
                last_modified = 0

                # Recursively count files and sizes
                for file_path in item.rglob("*"):
                    if file_path.is_file():
                        stat = await aiofiles.os.stat(file_path)
                        file_count += 1
                        total_size += stat.st_size
                        last_modified = max(last_modified, stat.st_mtime)

                # Use directory's mtime if no files found
                if last_modified == 0:
                    stat = await aiofiles.os.stat(item)
                    last_modified = stat.st_mtime

                project_info = ProjectInfo(
                    name=item.name,
                    file_count=file_count,
                    total_size=total_size,
                    last_modified=datetime.fromtimestamp(last_modified, UTC).isoformat(),
                )

                project_infos.append((last_modified, project_info))

            # Sort by last modified time (newest first) and return ProjectInfo objects
            project_infos.sort(key=lambda x: x[0], reverse=True)
            return [info for _, info in project_infos]

        except PermissionError as e:
            raise PermissionError(
                f"Cannot access client_root {self.config.client_root}: {e}. "
                "Check directory permissions."
            ) from e
