"""
Output configuration management for Alpha Vantage MCP server.

This module provides Pydantic-based configuration loading from environment
variables with validation and helpful error messages.
"""

import os
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_client_root_from_env():
    """Factory function to get client_root from environment."""
    output_dir = os.getenv("MCP_OUTPUT_DIR")
    if not output_dir:
        return None  # Will be validated by model_validator

    path = Path(output_dir)

    # Validate path is absolute
    if not path.is_absolute():
        raise ValueError(
            f"client_root must be an absolute path. Got: {path}. "
            "Please provide a full path starting from root (e.g., /Users/username/outputs)."
        )

    # Ensure directory exists or can be created
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise ValueError(
            f"Cannot create directory at {path}: {e}. "
            "Please ensure the path is valid and you have write permissions."
        ) from e

    # Validate write permissions
    if not os.access(path, os.W_OK):
        raise ValueError(
            f"Directory {path} is not writable. "
            "Please check file permissions and ensure you have write access."
        )

    return path


class OutputConfig(BaseSettings):
    """
    Configuration for Alpha Vantage output management.

    Loads all settings from environment variables with sensible defaults.
    Validates paths for security and accessibility.

    Environment Variables:
        MCP_OUTPUT_DIR: Required. Root directory for output files.
        MCP_PROJECT_NAME: Optional. Current project name (default: "default").
        MCP_ENABLE_PROJECT_FOLDERS: Optional. Enable project folders (default: true).
        MCP_OUTPUT_AUTO: Optional. Auto-decide file vs inline (default: true).
        MCP_OUTPUT_TOKEN_THRESHOLD: Optional. Token threshold for file output (default: 1000).
        MCP_OUTPUT_CSV_THRESHOLD: Optional. Row threshold for CSV output (default: 100).
        MCP_MAX_INLINE_ROWS: Optional. Max rows for inline response (default: 50).
        MCP_OUTPUT_FORMAT: Optional. Default output format (default: "csv").
        MCP_OUTPUT_COMPRESSION: Optional. Enable gzip compression (default: false).
        MCP_OUTPUT_METADATA: Optional. Include metadata in responses (default: true).
        MCP_STREAMING_CHUNK_SIZE: Optional. Chunk size for streaming (default: 10000).
        MCP_DEFAULT_FOLDER_PERMISSIONS: Optional. Folder permission mode (default: 0o755).

    Example:
        >>> config = OutputConfig()
        >>> config.client_root
        PosixPath('/Users/username/alpha_vantage_outputs')

        >>> config.output_format
        'csv'

    Raises:
        ValueError: If MCP_OUTPUT_DIR is not set or invalid.
        ValueError: If any validation fails (with helpful message).
    """

    client_root: Path | None = Field(
        default_factory=_get_client_root_from_env,
        description="Root directory for output files. Must be absolute and writable.",
        validation_alias="MCP_OUTPUT_DIR",
    )

    project_name: str = Field(default="default", description="Current project for organization.")

    enable_project_folders: bool = Field(
        default=True, description="Enable project-based organization."
    )

    output_auto: bool = Field(default=True, description="Auto-decide file vs inline output.")

    output_token_threshold: int = Field(
        default=1000, description="Token threshold for file output. Must be > 0."
    )

    output_csv_threshold: int = Field(
        default=100, description="Row threshold for CSV output. Must be between 1 and 1,000,000."
    )

    max_inline_rows: int = Field(
        default=50, description="Maximum rows for inline response. Must be > 0."
    )

    output_format: Literal["csv", "json"] = Field(
        default="csv", description="Default output format."
    )

    output_compression: bool = Field(
        default=False, description="Enable gzip compression for output files."
    )

    output_metadata: bool = Field(default=True, description="Include metadata in responses.")

    streaming_chunk_size: int = Field(
        default=10000, description="Chunk size for streaming. Must be between 100 and 100,000."
    )

    default_folder_permissions: int = Field(
        default=0o755, description="Folder permission mode in octal format."
    )

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        extra="allow",  # Allow direct assignment for testing
    )

    @field_validator("client_root", mode="before")
    @classmethod
    def validate_client_root(cls, v):
        """
        Validate client_root when directly assigned (for testing).

        Args:
            v: Value from direct assignment.

        Returns:
            Path: Validated absolute path.

        Raises:
            ValueError: If path is invalid.
        """
        # Direct assignment (used in tests) - validate the provided path
        if v is None:
            return v  # Let default_factory handle it

        if isinstance(v, Path):
            path = v
        elif isinstance(v, str):
            path = Path(v)
        else:
            raise ValueError(f"client_root must be a Path or string, got: {type(v)}")

        # Validate path is absolute
        if not path.is_absolute():
            raise ValueError(
                f"client_root must be an absolute path. Got: {path}. "
                "Please provide a full path starting from root (e.g., /Users/username/outputs)."
            )

        # Ensure directory exists or can be created
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValueError(
                f"Cannot create directory at {path}: {e}. "
                "Please ensure the path is valid and you have write permissions."
            ) from e

        # Validate write permissions
        if not os.access(path, os.W_OK):
            raise ValueError(
                f"Directory {path} is not writable. "
                "Please check file permissions and ensure you have write access."
            )

        return path

    @field_validator("output_token_threshold")
    @classmethod
    def validate_output_token_threshold(cls, v):
        """Validate token threshold is positive."""
        if v <= 0:
            raise ValueError(f"output_token_threshold must be > 0. Got: {v}")
        return v

    @field_validator("output_csv_threshold")
    @classmethod
    def validate_output_csv_threshold(cls, v):
        """Validate CSV threshold is within bounds."""
        if not (1 <= v <= 1_000_000):
            raise ValueError(f"output_csv_threshold must be between 1 and 1,000,000. Got: {v}")
        return v

    @field_validator("max_inline_rows")
    @classmethod
    def validate_max_inline_rows(cls, v):
        """Validate max inline rows is positive."""
        if v <= 0:
            raise ValueError(f"max_inline_rows must be > 0. Got: {v}")
        return v

    @field_validator("streaming_chunk_size")
    @classmethod
    def validate_streaming_chunk_size(cls, v):
        """Validate streaming chunk size is within bounds."""
        if not (100 <= v <= 100_000):
            raise ValueError(f"streaming_chunk_size must be between 100 and 100,000. Got: {v}")
        return v

    @field_validator("default_folder_permissions", mode="before")
    @classmethod
    def validate_default_folder_permissions(cls, v):
        """Parse and validate folder permissions from octal string or int."""
        # Handle octal string format (e.g., "0o755")
        if isinstance(v, str):
            if v.startswith("0o") or v.startswith("0O"):
                v = int(v, 8)
            else:
                v = int(v)
        return int(v)

    @model_validator(mode="after")
    def validate_client_root_not_none(self):
        """Ensure client_root was successfully set."""
        if self.client_root is None:
            raise ValueError(
                "MCP_OUTPUT_DIR must be set. Please set the environment variable "
                "to an absolute path for output files."
            )
        return self


def load_output_config() -> OutputConfig:
    """
    Load and validate output configuration.

    Returns:
        Validated OutputConfig instance.

    Raises:
        ValueError: If configuration is invalid with helpful error message.

    Example:
        >>> config = load_output_config()
        >>> config.client_root.exists()
        True
    """
    try:
        return OutputConfig()
    except Exception as e:
        raise ValueError(f"Invalid output configuration: {e}") from e
