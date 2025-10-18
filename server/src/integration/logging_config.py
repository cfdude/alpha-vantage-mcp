"""
Logging configuration for Alpha Vantage MCP Server.

This module sets up structured logging with loguru, providing:
- Configurable log levels via MCP_LOG_LEVEL environment variable
- Contextual logging with decision metadata
- File and console output
- Performance metrics tracking
- Security event logging integration

Examples:
    >>> from src.integration.logging_config import get_logger
    >>> logger = get_logger()
    >>> logger.info("Processing request", request_id="abc123", tokens=1500)
    >>> logger.debug("Token estimation", tokens=1500, time_ms=23.5)
"""

import os
import sys
from pathlib import Path
from typing import Any

from loguru import logger


class LoggingConfig:
    """
    Configuration and setup for MCP server logging.

    This class configures loguru for the Alpha Vantage MCP server with:
    - Environment-based log level control
    - Dual output (console + file)
    - Structured logging with context
    - Performance and security event tracking

    Attributes:
        log_level: Log level from MCP_LOG_LEVEL env var (default: INFO).
        log_dir: Directory for log files (default: logs/).
        log_file: Path to log file (default: logs/mcp_server.log).
        console_format: Format string for console output.
        file_format: Format string for file output.
    """

    # Valid log levels
    VALID_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    # Default log level
    DEFAULT_LEVEL = "INFO"

    # Log directory and file
    DEFAULT_LOG_DIR = Path("logs")
    DEFAULT_LOG_FILE = "mcp_server.log"

    # Format strings
    CONSOLE_FORMAT = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    FILE_FORMAT = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message} | "
        "{extra}"
    )

    def __init__(self):
        """Initialize logging configuration."""
        # Get log level from environment
        self.log_level = os.getenv("MCP_LOG_LEVEL", self.DEFAULT_LEVEL).upper()

        # Validate log level
        if self.log_level not in self.VALID_LEVELS:
            print(
                f"Warning: Invalid MCP_LOG_LEVEL '{self.log_level}'. "
                f"Using default: {self.DEFAULT_LEVEL}",
                file=sys.stderr,
            )
            self.log_level = self.DEFAULT_LEVEL

        # Set up log directory
        self.log_dir = self.DEFAULT_LOG_DIR
        self.log_file = self.log_dir / self.DEFAULT_LOG_FILE

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Configure loguru
        self._configure_loguru()

    def _configure_loguru(self):
        """
        Configure loguru with console and file handlers.

        Sets up:
        - Console handler with colored output
        - File handler with rotation and retention
        - Structured logging with extra fields
        """
        # Remove default handler
        logger.remove()

        # Add console handler with colors
        logger.add(
            sys.stderr,
            format=self.CONSOLE_FORMAT,
            level=self.log_level,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )

        # Add file handler with rotation
        logger.add(
            self.log_file,
            format=self.FILE_FORMAT,
            level=self.log_level,
            rotation="10 MB",  # Rotate when file reaches 10 MB
            retention="30 days",  # Keep logs for 30 days
            compression="zip",  # Compress rotated logs
            backtrace=True,
            diagnose=True,
            enqueue=True,  # Thread-safe logging
        )

    def get_logger(self):
        """
        Get configured logger instance.

        Returns:
            Configured loguru logger.

        Examples:
            >>> config = LoggingConfig()
            >>> logger = config.get_logger()
            >>> logger.info("Test message")
        """
        return logger


# Global logging configuration instance
_config = None


def get_logger():
    """
    Get the global MCP server logger.

    This function ensures logging is configured only once and returns
    the same logger instance for all modules.

    Returns:
        Configured loguru logger with MCP server settings.

    Examples:
        >>> from src.integration.logging_config import get_logger
        >>> logger = get_logger()
        >>> logger.info("Processing data", rows=1000, tokens=5000)
        >>> logger.debug("Token estimation", time_ms=23.5, result="file")
        >>> logger.warning("Large dataset", rows=50000, action="writing to file")
        >>> logger.error("File write failed", path="/tmp/data.csv", error="Permission denied")
    """
    global _config
    if _config is None:
        _config = LoggingConfig()
    return _config.get_logger()


def log_decision(
    decision_type: str,
    use_file: bool,
    token_count: int,
    row_count: int,
    reason: str,
    **kwargs: Any,
):
    """
    Log an output decision with structured context.

    Args:
        decision_type: Type of decision ("automatic", "forced_inline", "forced_file").
        use_file: Whether output will be written to file.
        token_count: Estimated token count.
        row_count: Number of rows/elements.
        reason: Human-readable reason for the decision.
        **kwargs: Additional context to log.

    Examples:
        >>> log_decision(
        ...     "automatic",
        ...     use_file=True,
        ...     token_count=5000,
        ...     row_count=1000,
        ...     reason="Exceeds token threshold",
        ...     threshold=1000
        ... )
    """
    logger = get_logger()
    logger.info(
        f"Output decision: {decision_type}",
        decision_type=decision_type,
        use_file=use_file,
        token_count=token_count,
        row_count=row_count,
        reason=reason,
        **kwargs,
    )


def log_file_operation(
    operation: str,
    filepath: str,
    success: bool,
    size_bytes: int | None = None,
    duration_ms: float | None = None,
    **kwargs: Any,
):
    """
    Log a file operation with metrics.

    Args:
        operation: Type of operation ("write", "read", "delete", "list").
        filepath: Path to the file.
        success: Whether operation succeeded.
        size_bytes: File size in bytes (optional).
        duration_ms: Operation duration in milliseconds (optional).
        **kwargs: Additional context to log.

    Examples:
        >>> log_file_operation(
        ...     "write",
        ...     filepath="/tmp/data.csv",
        ...     success=True,
        ...     size_bytes=1048576,
        ...     duration_ms=245.3,
        ...     format="csv",
        ...     compressed=False
        ... )
    """
    logger = get_logger()
    level = "info" if success else "error"

    extra = {
        "operation": operation,
        "filepath": filepath,
        "success": success,
    }

    if size_bytes is not None:
        extra["size_bytes"] = size_bytes

    if duration_ms is not None:
        extra["duration_ms"] = duration_ms

    extra.update(kwargs)

    log_func = getattr(logger, level)
    log_func(f"File {operation}: {filepath}", **extra)


def log_security_event(
    event_type: str,
    message: str,
    severity: str = "warning",
    path: str | None = None,
    **kwargs: Any,
):
    """
    Log a security event for audit trail.

    Args:
        event_type: Type of security event (e.g., "path_traversal", "permission_denied").
        message: Detailed message about the event.
        severity: Severity level ("info", "warning", "error", "critical").
        path: Optional path related to the event.
        **kwargs: Additional context to log.

    Examples:
        >>> log_security_event(
        ...     "path_traversal",
        ...     "Attempted to access file outside base directory",
        ...     severity="warning",
        ...     path="../etc/passwd",
        ...     user="unknown"
        ... )
    """
    logger = get_logger()

    # Validate severity
    valid_severities = ["info", "warning", "error", "critical"]
    if severity not in valid_severities:
        severity = "warning"

    extra = {
        "event_type": event_type,
        "severity": severity,
    }

    if path is not None:
        extra["path"] = path

    extra.update(kwargs)

    log_func = getattr(logger, severity)
    log_func(f"[SECURITY] {event_type}: {message}", **extra)


def log_performance_metric(
    metric_name: str,
    value: float,
    unit: str = "ms",
    **kwargs: Any,
):
    """
    Log a performance metric.

    Args:
        metric_name: Name of the metric (e.g., "token_estimation_time", "file_write_time").
        value: Metric value.
        unit: Unit of measurement (default: "ms" for milliseconds).
        **kwargs: Additional context to log.

    Examples:
        >>> log_performance_metric(
        ...     "token_estimation_time",
        ...     23.5,
        ...     unit="ms",
        ...     rows=1000,
        ...     method="tiktoken"
        ... )
        >>> log_performance_metric(
        ...     "file_write_time",
        ...     245.3,
        ...     unit="ms",
        ...     size_bytes=1048576,
        ...     format="csv"
        ... )
    """
    logger = get_logger()
    logger.debug(
        f"Performance: {metric_name} = {value}{unit}",
        metric_name=metric_name,
        value=value,
        unit=unit,
        **kwargs,
    )
