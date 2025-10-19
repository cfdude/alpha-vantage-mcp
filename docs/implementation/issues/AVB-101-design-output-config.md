# AVB-101: Design OutputConfig Pydantic Model

**Issue Type:** Story  
**Epic:** EPIC-1.1.1 Configuration System  
**Priority:** P0 (Critical)  
**Story Points:** 2  
**Assignee:** Unassigned  
**Sprint:** Sprint 1 (Planned)

---

## Story

**As a** developer integrating the output helper  
**I want** a validated configuration model with all settings defined  
**So that** I can load and use configuration safely throughout the codebase

## Acceptance Criteria

- [ ] OutputConfig class created in `server/src/utils/output_config.py`
- [ ] All 12 configuration fields defined with proper types
- [ ] Each field has a description for documentation
- [ ] Default values use environment variables with fallbacks
- [ ] Pydantic model validates successfully on instantiation
- [ ] Code follows project style guidelines (black, ruff)

---

## Technical Specifications

### File Location
`server/src/utils/output_config.py`

### Implementation Requirements

**Required Fields (12 total):**

1. **client_root** (`Path`) - Root directory for output files
   - Environment: `MCP_OUTPUT_DIR`
   - Required: Yes
   - Validation: Must be absolute, must exist or be creatable, must be writable

2. **project_name** (`str`) - Current project for organization
   - Environment: `MCP_PROJECT_NAME`
   - Default: "default"

3. **enable_project_folders** (`bool`) - Enable project-based organization
   - Environment: `MCP_ENABLE_PROJECT_FOLDERS`
   - Default: true

4. **output_auto** (`bool`) - Auto-decide file vs inline
   - Environment: `MCP_OUTPUT_AUTO`
   - Default: true

5. **output_token_threshold** (`int`) - Token threshold for file output
   - Environment: `MCP_OUTPUT_TOKEN_THRESHOLD`
   - Default: 1000
   - Validation: Must be > 0

6. **output_csv_threshold** (`int`) - Row threshold for CSV output
   - Environment: `MCP_OUTPUT_CSV_THRESHOLD`
   - Default: 100
   - Validation: Must be between 1 and 1,000,000

7. **max_inline_rows** (`int`) - Max rows for inline response
   - Environment: `MCP_MAX_INLINE_ROWS`
   - Default: 50
   - Validation: Must be > 0

8. **output_format** (`Literal["csv", "json"]`) - Default output format
   - Environment: `MCP_OUTPUT_FORMAT`
   - Default: "csv"

9. **output_compression** (`bool`) - Enable gzip compression
   - Environment: `MCP_OUTPUT_COMPRESSION`
   - Default: false

10. **output_metadata** (`bool`) - Include metadata in responses
    - Environment: `MCP_OUTPUT_METADATA`
    - Default: true

11. **streaming_chunk_size** (`int`) - Chunk size for streaming
    - Environment: `MCP_STREAMING_CHUNK_SIZE`
    - Default: 10,000
    - Validation: Must be between 100 and 100,000

12. **default_folder_permissions** (`int`) - Folder permission mode
    - Environment: `MCP_DEFAULT_FOLDER_PERMISSIONS`
    - Default: 0o755
    - Parsing: Octal format

---

## Implementation Steps

### Step 1: Create File Structure
```bash
# Create utils directory if needed
mkdir -p server/src/utils
touch server/src/utils/__init__.py
touch server/src/utils/output_config.py
```

### Step 2: Import Dependencies
```python
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field, validator
import os
```

### Step 3: Define OutputConfig Class
```python
class OutputConfig(BaseModel):
    """
    Configuration for Alpha Vantage output management.
    
    Loads configuration from environment variables with sensible defaults.
    All paths are validated for security and accessibility.
    
    Example:
        >>> config = OutputConfig()
        >>> print(config.client_root)
        /Users/username/alpha_vantage_outputs
    """
    
    # Define all 12 fields here...
```

### Step 4: Add Field Definitions
For each field, use this pattern:
```python
field_name: FieldType = Field(
    default_factory=lambda: parse_env("ENV_VAR_NAME", default_value),
    description="Clear description of what this controls",
)
```

### Step 5: Implement Validators
```python
@validator("client_root")
def validate_client_root(cls, v: Path) -> Path:
    """Ensure client_root is absolute and writable"""
    # Validation logic here
    return v
```

### Step 6: Add Config Class
```python
class Config:
    validate_assignment = True  # Re-validate on field assignment
```

---

## Code Template

```python
# File: server/src/utils/output_config.py
"""
Output configuration management for Alpha Vantage MCP server.

This module provides Pydantic-based configuration loading from environment
variables with validation and helpful error messages.
"""

from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field, validator
import os


class OutputConfig(BaseModel):
    """
    Configuration for Alpha Vantage output management.
    
    Loads all settings from environment variables with sensible defaults.
    Validates paths for security and accessibility.
    
    Environment Variables:
        MCP_OUTPUT_DIR: Required. Root directory for output files.
        MCP_PROJECT_NAME: Optional. Current project name (default: "default").
        MCP_ENABLE_PROJECT_FOLDERS: Optional. Enable project folders (default: true).
        ...additional variables documented in .env.example
    
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
    
    # TODO: Add all 12 field definitions
    
    # TODO: Add validators for critical fields
    
    class Config:
        validate_assignment = True


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
        raise ValueError(f"Invalid output configuration: {e}")
```

---

## Testing Requirements

### Unit Tests to Write

Create `server/tests/utils/test_output_config.py`:

```python
import pytest
from pathlib import Path
from server.src.utils.output_config import OutputConfig, load_output_config


def test_output_config_with_valid_env(tmp_path, monkeypatch):
    """Test configuration loads with valid environment variables"""
    monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("MCP_PROJECT_NAME", "test_project")
    
    config = OutputConfig()
    
    assert config.client_root == tmp_path
    assert config.project_name == "test_project"


def test_output_config_missing_client_root():
    """Test configuration fails without MCP_OUTPUT_DIR"""
    with pytest.raises(ValueError, match="MCP_OUTPUT_DIR must be set"):
        OutputConfig()


def test_output_config_non_absolute_path(monkeypatch):
    """Test configuration fails with relative path"""
    monkeypatch.setenv("MCP_OUTPUT_DIR", "relative/path")
    
    with pytest.raises(ValueError, match="must be absolute"):
        OutputConfig()


def test_csv_threshold_validation():
    """Test CSV threshold validation bounds"""
    # Test too small
    # Test too large
    # Test valid values


def test_load_output_config_success(tmp_path, monkeypatch):
    """Test load_output_config() helper function"""
    monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))
    
    config = load_output_config()
    
    assert isinstance(config, OutputConfig)
    assert config.client_root.exists()
```

**Coverage Target:** ≥90% for this module

---

## Definition of Done

- [ ] Code written and follows style guide
- [ ] All 12 fields defined correctly
- [ ] Validators implemented for critical fields
- [ ] Unit tests written and passing
- [ ] Code coverage ≥90%
- [ ] Code reviewed by team member
- [ ] Documentation complete (docstrings)
- [ ] Manual testing completed
- [ ] Merged to dev branch

---

## Review Checklist

**Code Quality:**
- [ ] Follows Pydantic best practices
- [ ] Type hints complete and accurate
- [ ] Docstrings follow Google style
- [ ] No security vulnerabilities

**Testing:**
- [ ] All test cases passing
- [ ] Edge cases covered
- [ ] Error cases tested
- [ ] Coverage target met

**Documentation:**
- [ ] Class and method docstrings complete
- [ ] Examples provided in docstrings
- [ ] Env var names documented

---

## Dependencies

**Requires:**
- Pydantic ≥2.0 (already in pyproject.toml)
- python-dotenv ≥1.1.1 (already in pyproject.toml)

**Blocks:**
- AVB-102: Environment variable loading
- AVB-103: Configuration validation
- All other output helper work

**Depends On:**
- None (this is the starting point)

---

## Time Estimates

- **Design & Implementation:** 1.5 hours
- **Unit Tests:** 0.5 hours
- **Code Review:** 0.25 hours
- **Documentation:** 0.25 hours
- **Total:** ~2.5 hours

---

## Notes & Considerations

**Design Decisions:**
- Use Pydantic for automatic validation and type coercion
- Default to environment variables for 12-factor app compliance
- Provide sensible defaults for optional settings
- Validate security-critical settings (paths, permissions)

**Security Considerations:**
- Path must be absolute to prevent relative path issues
- Must validate write permissions before accepting path
- Don't expose sensitive paths in error messages

**Future Enhancements:**
- Support configuration file (config.yaml) in addition to env vars
- Add configuration hot-reloading
- Support per-tool configuration overrides

---

## References

**Source Material:**
- Snowflake MCP `config.py`: `/Users/robsherman/Servers/snowflake-mcp-server/snowflake_mcp_server/config.py`
- Pydantic docs: https://docs.pydantic.dev/latest/
- 12-factor app config: https://12factor.net/config

**Related Issues:**
- AVB-102: Environment variable loading (follows this)
- AVB-103: Configuration validation (extends this)
- AVB-104: .env.example creation (uses this)

---

**Created:** 2025-10-16  
**Last Updated:** 2025-10-16  
**Status:** Ready for Development
