"""
Security validation utilities for Alpha Vantage MCP server.

This module provides comprehensive security validation for file operations including:
- Path containment validation (prevent directory traversal attacks)
- Filename sanitization (remove dangerous characters)
- Permission checking (verify read/write access)

All functions raise appropriate exceptions with actionable error messages.
"""

import os
import re
from datetime import UTC
from pathlib import Path


class SecurityError(Exception):
    """
    Custom exception for security violations.

    Raised when a security check fails (path traversal, invalid filename, etc.).
    Always includes an actionable error message explaining what went wrong.
    """

    pass


def validate_path_contained(path: Path, base_dir: Path) -> bool:
    """
    Validate that a path is contained within a base directory.

    This function prevents directory traversal attacks by ensuring that the
    resolved path stays within the allowed base directory boundaries. It handles:
    - Relative path components (../)
    - Symlinks (resolves to actual target)
    - Absolute paths (rejects them)
    - Mixed path separators

    Args:
        path: The path to validate. Can be relative or absolute.
        base_dir: The base directory that must contain the path.

    Returns:
        bool: True if the path is safely contained within base_dir.

    Raises:
        SecurityError: If the path escapes base_dir boundaries or is invalid.
        ValueError: If base_dir is not absolute or doesn't exist.

    Examples:
        >>> base = Path("/var/data")
        >>> validate_path_contained(Path("user/file.csv"), base)
        True

        >>> validate_path_contained(Path("../etc/passwd"), base)
        SecurityError: Path traversal detected: path escapes base directory

        >>> validate_path_contained(Path("/etc/passwd"), base)
        SecurityError: Absolute paths not allowed for security

    Security Features:
        - Uses Path.resolve() to normalize and expand all path components
        - Uses Path.is_relative_to() for safe containment checking
        - Rejects absolute paths that aren't already within base_dir
        - Handles symlinks by resolving to actual target path
    """
    # Validate base_dir is absolute
    if not base_dir.is_absolute():
        raise ValueError(
            f"base_dir must be an absolute path. Got: {base_dir}. "
            "Please provide a full path starting from root."
        )

    # Validate base_dir exists (or can be created)
    if not base_dir.exists():
        try:
            base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValueError(
                f"Cannot create base directory {base_dir}: {e}. "
                "Please ensure the path is valid and you have permissions."
            ) from e

    # Resolve both paths to their absolute, normalized forms
    # This handles symlinks, relative components (.., .), and normalizes separators
    try:
        resolved_base = base_dir.resolve(strict=True)
    except Exception as e:
        raise ValueError(
            f"Cannot resolve base directory {base_dir}: {e}. "
            "Please ensure the directory exists and is accessible."
        ) from e

    # If path is absolute and NOT already within base_dir, reject it
    if path.is_absolute():
        try:
            resolved_path = path.resolve(strict=False)
        except Exception as e:
            raise SecurityError(
                f"Cannot resolve path {path}: {e}. This may indicate a malformed path."
            ) from e

        if not resolved_path.is_relative_to(resolved_base):
            raise SecurityError(
                f"Absolute paths not allowed for security. "
                f"Path {path} is outside base directory {base_dir}. "
                f"Please use a relative path instead."
            )
    else:
        # For relative paths, resolve from base_dir
        full_path = base_dir / path
        try:
            resolved_path = full_path.resolve(strict=False)
        except Exception as e:
            raise SecurityError(
                f"Cannot resolve path {path}: {e}. This may indicate a malformed path."
            ) from e

    # Final containment check using is_relative_to (Python 3.9+)
    if not resolved_path.is_relative_to(resolved_base):
        raise SecurityError(
            f"Path traversal detected: path escapes base directory. "
            f"Attempted path: {path} "
            f"Resolved to: {resolved_path} "
            f"Base directory: {resolved_base}. "
            f"This is a security violation. Please ensure your path stays "
            f"within the allowed directory."
        )

    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing dangerous characters.

    This function ensures filenames are safe for use across different operating
    systems and don't contain characters that could be exploited for attacks.

    Dangerous characters removed:
        - Path separators: / \\
        - Invalid filename chars: : * ? " < > |
        - Control characters: 0x00-0x1F, 0x7F
        - Null bytes: \\x00
        - Path traversal sequences: .. (dots)

    Reserved names handled (Windows):
        - CON, PRN, AUX, NUL, COM1-COM9, LPT1-LPT9

    Unicode characters are preserved to support international filenames.

    Args:
        filename: The filename to sanitize.

    Returns:
        str: Sanitized filename safe for use on any filesystem.
             Never returns empty string (uses "unnamed_file" fallback).
             Limited to 255 characters (filesystem maximum).

    Examples:
        >>> sanitize_filename("report.csv")
        'report.csv'

        >>> sanitize_filename("../etc/passwd")
        'etcpasswd'

        >>> sanitize_filename("file:name?.csv")
        'filename.csv'

        >>> sanitize_filename("CON")
        'CON_file'

        >>> sanitize_filename("")
        'unnamed_file'

        >>> sanitize_filename("日本語ファイル.csv")
        '日本語ファイル.csv'

    Security Features:
        - Removes all path separators (prevents directory traversal)
        - Removes shell-dangerous characters
        - Handles Windows reserved names
        - Prevents null byte injection
        - Never returns empty strings (security default)
        - Preserves unicode for international support
    """
    if not filename or not isinstance(filename, str):
        return "unnamed_file"

    # Remove null bytes (security risk)
    filename = filename.replace("\x00", "")

    # Remove control characters (0x00-0x1F and 0x7F)
    filename = "".join(char for char in filename if ord(char) >= 32 and ord(char) != 127)

    # Remove or replace dangerous characters
    # Path separators: / \
    # Invalid filename chars: : * ? " < > |
    dangerous_chars = r'[/\\:*?"<>|]'
    filename = re.sub(dangerous_chars, "", filename)

    # Remove path traversal sequences (..)
    # This prevents filenames like ".." from being used
    filename = filename.replace("..", "")

    # Strip leading/trailing whitespace and dots (security best practice)
    filename = filename.strip().strip(".")

    # Handle Windows reserved names
    # CON, PRN, AUX, NUL, COM1-COM9, LPT1-LPT9
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    # Check if filename (without extension) is a reserved name
    name_without_ext = filename.rsplit(".", 1)[0].upper()
    if name_without_ext in reserved_names:
        filename = f"{filename}_file"

    # Fallback if filename becomes empty after sanitization
    if not filename:
        filename = "unnamed_file"

    # Limit filename length to 255 characters (filesystem maximum)
    if len(filename) > 255:
        # If there's an extension, preserve it
        if "." in filename:
            name, ext = filename.rsplit(".", 1)
            max_name_length = 255 - len(ext) - 1  # -1 for the dot
            filename = f"{name[:max_name_length]}.{ext}"
        else:
            filename = filename[:255]

    return filename


def check_directory_permissions(directory: Path) -> None:
    """
    Check that a directory has appropriate read/write permissions.

    This function verifies that:
    1. Directory exists OR parent exists for creation
    2. Directory is writable (for file creation)
    3. Directory is readable (for listing files)

    Args:
        directory: The directory path to check.

    Raises:
        PermissionError: If directory lacks required permissions.
        ValueError: If directory path is invalid or cannot be accessed.

    Examples:
        >>> check_directory_permissions(Path("/var/data"))
        None  # Success - no exception raised

        >>> check_directory_permissions(Path("/root/protected"))
        PermissionError: Directory /root/protected is not writable

        >>> check_directory_permissions(Path("/nonexistent/deeply/nested"))
        ValueError: Parent directory does not exist: /nonexistent/deeply

    Security Features:
        - Uses os.access() for permission checking (not try/except)
        - Checks both read and write permissions
        - Provides actionable error messages
        - Validates parent directory for new directory creation
    """
    if not isinstance(directory, Path):
        raise ValueError(
            f"directory must be a Path object, got {type(directory)}. Please convert to Path first."
        )

    # Check if directory exists (handle permission errors during check)
    try:
        dir_exists = directory.exists()
    except PermissionError as e:
        raise PermissionError(
            f"Cannot access directory {directory}: {e}. "
            "Permission denied while checking directory existence."
        ) from e

    # If directory exists, check its permissions
    if dir_exists:
        if not directory.is_dir():
            raise ValueError(
                f"Path exists but is not a directory: {directory}. "
                "Please provide a valid directory path."
            )

        # Check write permissions
        if not os.access(directory, os.W_OK):
            raise PermissionError(
                f"Directory {directory} is not writable. "
                f"Please check file permissions (current: {oct(directory.stat().st_mode)[-3:]}) "
                f"and ensure you have write access. "
                f"You may need to run: chmod u+w {directory}"
            )

        # Check read permissions
        if not os.access(directory, os.R_OK):
            raise PermissionError(
                f"Directory {directory} is not readable. "
                f"Please check file permissions (current: {oct(directory.stat().st_mode)[-3:]}) "
                f"and ensure you have read access. "
                f"You may need to run: chmod u+r {directory}"
            )

    else:
        # Directory doesn't exist - check if parent exists and is writable
        parent = directory.parent

        if not parent.exists():
            raise ValueError(
                f"Parent directory does not exist: {parent}. "
                f"Cannot create {directory}. "
                f"Please create parent directories first or ensure the path is correct."
            )

        if not os.access(parent, os.W_OK):
            raise PermissionError(
                f"Cannot create directory {directory}: parent {parent} is not writable. "
                f"Please check parent directory permissions and ensure you have write access. "
                f"You may need to run: chmod u+w {parent}"
            )


def validate_safe_path(path: Path, base_dir: Path, check_permissions: bool = True) -> Path:
    """
    Comprehensive path validation combining all security checks.

    This is a convenience function that combines path containment validation,
    filename sanitization, and permission checking into a single call.

    Args:
        path: The path to validate and sanitize.
        base_dir: The base directory that must contain the path.
        check_permissions: Whether to check directory permissions (default: True).

    Returns:
        Path: Validated and sanitized path safe for use.

    Raises:
        SecurityError: If path fails containment validation.
        PermissionError: If directory lacks required permissions.
        ValueError: If inputs are invalid.

    Examples:
        >>> base = Path("/var/data")
        >>> validate_safe_path(Path("user/report.csv"), base)
        PosixPath('/var/data/user/report.csv')

        >>> validate_safe_path(Path("../etc/passwd"), base)
        SecurityError: Path traversal detected

    Usage:
        This is the recommended function for validating user-provided paths
        in the OutputHandler system. It provides defense-in-depth security.
    """
    # Sanitize the filename component
    if path.name:
        sanitized_name = sanitize_filename(path.name)
        path = path.parent / sanitized_name

    # Validate path containment (this resolves the path and checks it's within base_dir)
    validate_path_contained(path, base_dir)

    # Build full path and resolve it to get the actual target path
    full_path = base_dir / path if not path.is_absolute() else path

    # Resolve to handle any .. or . components
    # Use strict=False because the file doesn't exist yet
    try:
        resolved_full_path = full_path.resolve(strict=False)
    except Exception as e:
        raise SecurityError(
            f"Cannot resolve path {full_path}: {e}. This may indicate a malformed path."
        ) from e

    # Check permissions if requested
    if check_permissions:
        # Check parent directory permissions (where file will be created)
        # Use the resolved path to get the actual parent
        parent_dir = resolved_full_path.parent
        check_directory_permissions(parent_dir)

    return resolved_full_path


# Logging helper for security events (for audit trail)
def log_security_event(event_type: str, message: str, path: Path | None = None) -> None:
    """
    Log security-related events for audit trail.

    This function provides a centralized logging point for security events.
    In production, this would integrate with a proper logging system.

    Args:
        event_type: Type of security event (e.g., "path_traversal", "permission_denied").
        message: Detailed message about the event.
        path: Optional path related to the event.

    Examples:
        >>> log_security_event("path_traversal", "Attempted to access /etc/passwd", Path("../etc/passwd"))
        # Logs: [SECURITY] path_traversal: Attempted to access /etc/passwd (path: ../etc/passwd)

    Note:
        Currently logs to stderr. In production, integrate with proper logging system
        (e.g., Python logging module, syslog, external security monitoring).
    """
    import sys
    from datetime import datetime

    timestamp = datetime.now(UTC).isoformat()
    path_str = f" (path: {path})" if path else ""
    log_entry = f"[{timestamp}] [SECURITY] {event_type}: {message}{path_str}"

    # In production, this would go to a proper logging system
    # For now, log to stderr
    print(log_entry, file=sys.stderr)
