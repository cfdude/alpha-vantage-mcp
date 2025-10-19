# Alpha Vantage MCP: Output Helper Quick Reference

## Files to Create/Adapt

### 1. `alpha_vantage_mcp/utils/output_config.py` (NEW)
**Based on:** Snowflake's `config.py` OutputConfig class

```python
from typing import Optional
from pydantic import BaseModel, Field, validator

class OutputConfig(BaseModel):
    """Output configuration for Alpha Vantage MCP."""
    
    model_name: str = Field("claude-4-sonnet", description="Model name")
    model_token_limit: int = Field(200000, description="Model context limit")
    safety_margin: float = Field(0.7, description="Safety margin (0.0-1.0)")
    
    default_output: str = Field("auto", description="auto|screen|file")
    default_file_format: str = Field("csv", description="csv|json")
    default_output_dir: str = Field("./av_data", description="Output directory")
    
    client_root: Optional[str] = Field(None, description="MCP_CLIENT_ROOT from env")
    screen_output_row_threshold: int = Field(1000, description="Row limit for screen")
    
    auto_generate_filename: bool = Field(True, description="Auto-generate names")
    filename_pattern: str = Field("av_{date}_{time}", description="Filename pattern")
    
    @validator('default_output')
    def validate_output(cls, v):
        if v not in ['auto', 'screen', 'file']:
            raise ValueError("Must be auto, screen, or file")
        return v
```

### 2. `alpha_vantage_mcp/utils/output_handler.py` (NEW)
**Based on:** Snowflake's `output_handler.py`

Key methods to implement:
- `generate_filename()` - Use {date}, {time}, {timestamp}, {query_hash}
- `resolve_output_path()` - CRITICAL SECURITY checks
- `write_to_file()` - Stream results with chunking
- `_write_csv()` - CSV format
- `_write_json()` - JSON format
- `validate_output_parameters()` - Input validation

### 3. `alpha_vantage_mcp/utils/output_estimator.py` (NEW)
**Based on:** Snowflake's `token_estimator.py`

Key methods:
- `should_use_file_output()` - Simple row-count heuristic (primary)
- `estimate_query_tokens()` - Full estimation (optional advanced feature)

## Configuration Setup

### 1. `.env.example` Entry
```bash
# Output Configuration
MCP_CLIENT_ROOT=/path/to/client/project
MODEL_NAME=claude-4-sonnet
MODEL_CONTEXT_TOKEN_LIMIT=200000
MODEL_SAFETY_MARGIN=0.7

DEFAULT_OUTPUT=auto
DEFAULT_FILE_FORMAT=csv
DEFAULT_OUTPUT_DIR=./av_data
SCREEN_OUTPUT_ROW_THRESHOLD=1000
AUTO_GENERATE_FILENAME=true
FILENAME_PATTERN=av_{date}_{time}
```

### 2. `alpha_vantage_mcp/config.py` (UPDATE)
Add to your config loading:
```python
def load_config() -> ServerConfig:
    # ... existing code ...
    
    output=OutputConfig(
        model_name=get_env("MODEL_NAME", "claude-4-sonnet"),
        model_token_limit=get_env("MODEL_CONTEXT_TOKEN_LIMIT", 200000, int),
        safety_margin=get_env("MODEL_SAFETY_MARGIN", 0.7, float),
        default_output=get_env("DEFAULT_OUTPUT", "auto"),
        default_file_format=get_env("DEFAULT_FILE_FORMAT", "csv"),
        default_output_dir=get_env("DEFAULT_OUTPUT_DIR", "./av_data"),
        client_root=get_env("MCP_CLIENT_ROOT"),
        screen_output_row_threshold=get_env("SCREEN_OUTPUT_ROW_THRESHOLD", 1000, int),
        auto_generate_filename=get_env("AUTO_GENERATE_FILENAME", True, bool),
        filename_pattern=get_env("FILENAME_PATTERN", "av_{date}_{time}"),
    )
```

## Integration Pattern

### In your MCP tool handler:
```python
from alpha_vantage_mcp.utils.output_handler import ResultOutputHandler
from alpha_vantage_mcp.config import get_config

async def handle_get_data(
    name: str,
    arguments: Optional[Dict[str, Any]] = None,
    request_ctx: RequestContext = None
) -> Sequence[mcp_types.TextContent]:
    
    # Get parameters
    data_query = arguments.get("query") if arguments else None
    output_mode = arguments.get("output")  # Could be None (will use default)
    file_format = arguments.get("format")
    location = arguments.get("location")
    filename = arguments.get("filename")
    
    # Load config
    config = get_config()
    output_config = config.output
    
    # Apply defaults
    if output_mode is None:
        output_mode = output_config.default_output
    if file_format is None:
        file_format = output_config.default_file_format
    if location is None:
        location = output_config.default_output_dir
    
    # Initialize handler
    output_handler = ResultOutputHandler(output_config)
    
    # Validate
    is_valid, error_msg = output_handler.validate_output_parameters(
        output_mode, file_format, location, filename
    )
    if not is_valid:
        return [mcp_types.TextContent(type="text", text=f"Error: {error_msg}")]
    
    # Decide output strategy
    use_file, reasoning = await output_handler.estimator.should_use_file_output(
        data_query,
        api_client,  # or whatever you use to fetch data
        force_output=None if output_mode == "auto" else output_mode
    )
    
    if use_file:
        # Write to file
        result = await output_handler.write_to_file(
            data_query, api_client, file_format, location, filename
        )
        response = f"""Data saved to file.
        
**File:** {result['file_path']}
**Format:** {result['format'].upper()}
**Rows:** {result['rows_written']:,}
**Size:** {result['file_size_readable']}

Decision: {reasoning['reason']}"""
        return [mcp_types.TextContent(type="text", text=response)]
    else:
        # Screen output
        data = await api_client.fetch_data(data_query)
        # Format as markdown table or text
        return [mcp_types.TextContent(type="text", text=formatted_data)]
```

## Security Checklist

- [ ] MCP_CLIENT_ROOT validation in resolve_output_path()
- [ ] Never allow writing to server installation directory
- [ ] Use `Path.is_relative_to()` for path validation
- [ ] Test write permissions before writing
- [ ] Sanitize filenames (block < > : " | ? * and Windows reserved names)
- [ ] Create directories with strict permissions
- [ ] Log all file operations with context

## Testing

```python
import pytest

@pytest.mark.asyncio
async def test_output_file_writing():
    config = OutputConfig(
        client_root="/tmp/test_project",
        default_output_dir="./data"
    )
    handler = ResultOutputHandler(config)
    
    # Test path resolution
    path = handler.resolve_output_path("./data", "test.csv")
    assert "/tmp/test_project/data" in str(path)
    
    # Test filename generation
    filename = handler.generate_filename("csv", "SELECT * FROM test")
    assert filename.endswith(".csv")
    assert "av_" in filename or "query_" in filename

@pytest.mark.asyncio
async def test_output_decision():
    config = OutputConfig(screen_output_row_threshold=1000)
    estimator = OutputEstimator(config)
    
    # Small dataset -> screen
    use_file, _ = await estimator.should_use_file_output(
        "small_data", mock_api, force_output="auto"
    )
    assert use_file == False
    
    # Large dataset -> file
    use_file, _ = await estimator.should_use_file_output(
        "large_data", mock_api, force_output="auto"
    )
    assert use_file == True
```

## Deployment Checklist

- [ ] Add OutputConfig to config.py
- [ ] Create output_handler.py with ResultOutputHandler
- [ ] Create output_estimator.py with OutputEstimator
- [ ] Update .env.example with all output variables
- [ ] Update main.py to use output handler in tools
- [ ] Test with MCP_CLIENT_ROOT set
- [ ] Test with MCP_CLIENT_ROOT not set (should error gracefully)
- [ ] Verify file outputs go to correct location
- [ ] Add output parameters to MCP tool schemas
- [ ] Document in README

## Performance Hints

1. Use chunked writes for large datasets (10,000 row chunks)
2. Stream JSON with immediate writes, not loading entire dataset
3. Use fast row counting for auto-detection (avoid full token estimation)
4. Cache config object, don't reload on every request
5. Test write permissions once at startup, not per-request

## Common Issues & Solutions

**Issue:** "MCP_CLIENT_ROOT environment variable not set"
- **Solution:** Ensure MPC client passes MCP_CLIENT_ROOT before starting server

**Issue:** Relative paths not working
- **Solution:** Check MCP_CLIENT_ROOT is absolute and writable

**Issue:** Files written to wrong location
- **Solution:** Debug resolve_output_path() - check both absolute and relative path handling

**Issue:** Large files consuming memory
- **Solution:** Ensure you're using chunked streaming, not loading entire result set

**Issue:** Filenames have invalid characters
- **Solution:** Call validate_output_parameters() before generating filename
