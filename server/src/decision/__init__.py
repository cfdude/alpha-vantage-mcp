"""
Decision logic for intelligent output handling in Alpha Vantage MCP server.

This module provides token estimation and automatic decision logic for
determining when to output data inline vs. write to files.
"""

from .token_estimator import TokenEstimator

__all__ = ["TokenEstimator"]
