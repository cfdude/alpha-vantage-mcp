"""
Integration utilities for Alpha Vantage MCP Server.

This module provides the final integration layer for Sprint 1, tying together:
- OutputConfig: Configuration management
- TokenEstimator: Intelligent token counting
- OutputHandler: File I/O operations
- Security validation: Path and permission checks
- Logging: Structured logging with context

Main exports:
    OutputDecision: Dataclass for output decisions
    should_use_output_helper: Decide file vs inline output
    create_file_reference_response: Create standardized file reference
    create_inline_response: Create standardized inline data response
    get_logger: Get configured logger instance
    log_decision: Log output decisions
    log_file_operation: Log file operations
    log_security_event: Log security events
    log_performance_metric: Log performance metrics

Examples:
    >>> from src.integration import (
    ...     should_use_output_helper,
    ...     create_inline_response,
    ...     create_file_reference_response,
    ...     get_logger
    ... )
    >>> from src.utils.output_config import OutputConfig
    >>>
    >>> config = OutputConfig()
    >>> logger = get_logger()
    >>> data = [{"id": 1, "value": "test"}]
    >>>
    >>> # Make decision
    >>> decision = should_use_output_helper(data, config)
    >>> logger.info("Decision made", use_file=decision.use_file)
    >>>
    >>> # Create response based on decision
    >>> if decision.use_file:
    ...     # Write to file and create reference
    ...     pass
    ... else:
    ...     response = create_inline_response(data)
"""

from .helpers import (
    OutputDecision,
    create_file_reference_response,
    create_inline_response,
    should_use_output_helper,
)
from .logging_config import (
    get_logger,
    log_decision,
    log_file_operation,
    log_performance_metric,
    log_security_event,
)

__all__ = [
    # Decision helpers
    "OutputDecision",
    "should_use_output_helper",
    "create_file_reference_response",
    "create_inline_response",
    # Logging
    "get_logger",
    "log_decision",
    "log_file_operation",
    "log_security_event",
    "log_performance_metric",
]
