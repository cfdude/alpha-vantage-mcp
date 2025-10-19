# Snowflake MCP Server: Output Helper Implementation Analysis

## Executive Summary
This document provides a comprehensive analysis of the Snowflake MCP server's output handling architecture, designed as a foundation for implementing similar patterns in the Alpha Vantage MCP server.

---

## 1. Architecture Overview

### File Organization
```
snowflake_mcp_server/
├── config.py                          # Configuration management (Pydantic-based)
├── main.py                            # Main MCP server implementation
└── utils/
    ├── output_handler.py              # Output management (ResultOutputHandler)
    ├── token_estimator.py             # Token counting & output decision logic
    ├── resource_allocator.py           # Fair resource allocation system
    └── [other utilities...]           # Connection, logging, security, etc.
```

### Key Classes & Their Relationships

```
ServerConfig (from config.py)
    └── OutputConfig
            ├── model_token_limit
            ├── safety_margin
            ├── default_output_dir
            ├── client_root (MCP_CLIENT_ROOT)
            ├── filename_pattern
            └── screen_output_row_threshold

ResultOutputHandler (from output_handler.py)
    ├── Uses: OutputConfig
    ├── Uses: TokenEstimator
    └── Methods:
        ├── generate_filename()
        ├── resolve_output_path()
        ├── write_to_file()
        ├── _write_csv()
        ├── _write_json()
        └── validate_output_parameters()

TokenEstimator (from token_estimator.py)
    ├── estimate_query_tokens()
    ├── should_use_file_output()
    └── _estimate_tokens_from_text()
```

---

## 2. Configuration Management

### Environment Variables (from .env.example)

#### Critical Variables
```bash
# Client Project Root - ESSENTIAL for security
MCP_CLIENT_ROOT=/Users/yourname/projects/your-project

# Model Configuration
MODEL_NAME=claude-4-sonnet
MODEL_CONTEXT_TOKEN_LIMIT=200000
MODEL_SAFETY_MARGIN=0.7  # Use only 70% of token limit

# Output Configuration
DEFAULT_OUTPUT=auto               # auto|screen|file
DEFAULT_FILE_FORMAT=csv           # csv|json
DEFAULT_OUTPUT_DIR=./query_results
SCREEN_OUTPUT_ROW_THRESHOLD=1000  # Rows beyond this use file output

# Filename Generation
AUTO_GENERATE_FILENAME=true
FILENAME_PATTERN=query_{date}_{time}  # {date}, {time}, {timestamp}, {query_hash}

# Token Estimation
TOKEN_ESTIMATION_SAMPLE_SIZE=100
LOG_TOKEN_ESTIMATION=false
```

### OutputConfig (from config.py)

```python
class OutputConfig(BaseModel):
    """Output and token management configuration."""
    
    model_name: str = Field("unknown", description="Model name for reference")
    model_token_limit: int = Field(100000, description="Model's token context limit")
    safety_margin: float = Field(0.7, description="Safety margin for token limit")
    default_output: str = Field("auto", description="Default output mode")
    default_file_format: str = Field("csv", description="Default file format")
    default_output_dir: str = Field("./query_results", description="Default output directory")
    client_root: Optional[str] = Field(None, description="Client project root (MCP_CLIENT_ROOT)")
    screen_output_row_threshold: int = Field(1000, description="Max rows for screen output")
    auto_generate_filename: bool = Field(True, description="Auto-generate filenames")
    filename_pattern: str = Field("query_{date}_{time}", description="Filename pattern")
    token_sample_size: int = Field(100, description="Sample size for token estimation")
    log_token_estimation: bool = Field(False, description="Log token estimation details")
```

---

## 3. Token Detection & Output Decision Logic

### TokenEstimator Class

#### Key Method: `should_use_file_output()`

**Purpose:** Determines whether to write results to file or display inline

**Decision Logic:**

```python
async def should_use_file_output(
    self,
    query: str, 
    db_ops,
    force_output: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Returns (use_file, reasoning_dict)
    
    Decision tree:
    1. If force_output='file' -> Use file (forced by user)
    2. If force_output='screen' -> Use screen (forced by user)
    3. If output='auto':
       - Get total row count quickly (fast COUNT(*) query)
       - Compare against screen_output_row_threshold (default: 1000)
       - If rows > threshold -> File output
       - If rows <= threshold -> Screen output (let Claude manage context)
    """
```

**Critical Design Insight:**
> "Let Claude handle its own context management. Don't try to estimate tokens; use simple row count heuristics instead."

This is a fundamental shift from token estimation to heuristic-based decisions. The system DOES support full token estimation but uses it sparingly.

#### Token Estimation Method: `estimate_query_tokens()`

```python
async def estimate_query_tokens(
    self, 
    query: str, 
    db_ops,
    sample_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Returns:
    {
        "row_count": 50000,
        "column_count": 17,
        "sample_size": 100,
        "sample_tokens_per_row": 85,
        "estimated_total_tokens": 4_250_000,
        "estimated_size_kb": 17_000,
        "confidence": "high|medium|low",  # Based on variance
        "token_variance": 12.5
    }
    """
```

**Implementation Strategy:**
1. Get exact row count: `SELECT COUNT(*) FROM (...) AS count_subq`
2. Sample N rows (default: 100, max: 1000)
3. For each sampled row:
   - Convert to text: `"column_name: value | column_name: value | ..."`
   - Estimate tokens: `chars / 4.0 * structure_factor`
   - Structure factor = 0.85 if heavily structured (more pipes/colons)
4. Statistical analysis:
   - Calculate mean tokens per row
   - Calculate std dev
   - Confidence = high (CV < 0.2) | medium (CV < 0.5) | low

**Token Estimation Formula:**
```
~1 token ≈ 4 characters
base_tokens = char_count / 4.0
structured_bonus = 0.85  # SQL results compress better
final_tokens = base_tokens * structure_factor
estimated_total = total_rows * avg_tokens_per_row
```

---

## 4. Output Handler Implementation

### ResultOutputHandler Class

#### Initialization
```python
class ResultOutputHandler:
    def __init__(self, config):
        """Initialize with OutputConfig."""
        self.config = config
        self.estimator = TokenEstimator(config)
```

#### Method 1: `generate_filename()`

```python
def generate_filename(self, format: str, query: Optional[str] = None) -> str:
    """
    Generate filename based on pattern.
    
    Supported placeholders:
    - {timestamp}: 20250116_101030
    - {date}: 20250116
    - {time}: 101030
    - {query_hash}: First 8 chars of MD5(query)
    
    Example:
    Pattern: "query_{date}_{time}"
    Result: "query_20250116_101030.csv"
    """
```

#### Method 2: `resolve_output_path()` - CRITICAL SECURITY LOGIC

```python
def resolve_output_path(self, location: Optional[str], filename: str) -> Path:
    """
    Resolve output path with strict security checks.
    
    SECURITY ARCHITECTURE:
    
    1. Path Resolution:
       - If location is absolute path -> use directly
       - If location is relative:
         * Must have MCP_CLIENT_ROOT set
         * Resolve relative to MCP_CLIENT_ROOT
         * If no client_root -> REFUSE (prevent server directory pollution)
    
    2. Safety Checks:
       - Never allow writing to MCP server installation directory
       - Test write permissions with temporary file
       - Validate directory creation
    
    3. Error Handling:
       - Raise ValueError with clear message if:
         * No MCP_CLIENT_ROOT for relative paths
         * Output dir would be inside server directory
         * No write permissions
    """
    
    # Use provided location or default
    base_dir = location or self.config.default_output_dir
    
    # Handle relative vs absolute paths
    if os.path.isabs(base_dir):
        output_dir = Path(base_dir)
    else:
        # Relative to client project root if available
        if self.config.client_root:
            output_dir = Path(self.config.client_root) / base_dir
        else:
            # CRITICAL: Refuse to write if client root not provided
            raise ValueError(
                "Cannot determine output location: MCP_CLIENT_ROOT environment variable not set. "
                "Files cannot be written to the MCP server directory to avoid data pollution. "
                "Please set MCP_CLIENT_ROOT to the calling project's root directory."
            )
    
    # Additional safety check: Never write to the MCP server's installation directory
    server_dir = Path(__file__).parent.parent.parent.resolve()
    resolved_output = output_dir.resolve()
    
    if resolved_output.is_relative_to(server_dir):
        raise ValueError(
            f"SECURITY ERROR: Attempted to write files to MCP server directory ({server_dir}). "
            f"Output directory ({resolved_output}) must be outside the server installation. "
            f"Please set MCP_CLIENT_ROOT environment variable to your project root."
        )
    
    # Create directory if it doesn't exist
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create output directory {output_dir}: {e}")
        raise ValueError(f"Cannot create output directory: {output_dir}")
    
    # Validate write permissions
    try:
        test_file = full_path.with_suffix('.tmp')
        test_file.touch()
        test_file.unlink()
    except OSError as e:
        logger.error(f"No write permission for {full_path}: {e}")
        raise ValueError(f"No write permission for output path: {full_path}")
    
    return full_path
```

#### Method 3: `write_to_file()` - Main File Writing

```python
async def write_to_file(
    self,
    query: str,
    db_ops,
    format: str = "csv",
    location: Optional[str] = None,
    filename: Optional[str] = None,
    chunk_size: int = 10000
) -> Dict[str, Any]:
    """
    Stream query results to file with chunking.
    
    Returns:
    {
        "status": "success",
        "output": "file",
        "file_path": "/absolute/path/to/file.csv",
        "format": "csv",
        "rows_written": 150000,
        "columns_written": 17,
        "file_size_bytes": 4521890,
        "file_size_mb": 4.31,
        "file_size_readable": "4.3 MB"
    }
    
    Process:
    1. Generate filename if not provided
    2. Resolve output path (with security checks)
    3. Execute query
    4. Get column information from cursor description
    5. Stream results in chunks (default: 10,000 rows)
    6. Write to file based on format (CSV or JSON)
    7. Get actual file size from disk
    8. Return metadata
    """
```

#### Method 4: `_write_csv()` - CSV Streaming

```python
async def _write_csv(
    self, 
    cursor, 
    output_path: Path, 
    columns: List[str], 
    chunk_size: int
) -> int:
    """
    Stream results to CSV file.
    
    Features:
    - Minimal quoting (QUOTE_MINIMAL)
    - UTF-8 encoding
    - Chunks data for memory efficiency
    - Converts None -> empty string
    - Handles special types
    
    Row Processing:
    for value in row:
        if value is None:
            output("")
        else:
            output(str(value))  # Convert to string
    """
```

#### Method 5: `_write_json()` - JSON Streaming

```python
async def _write_json(
    self, 
    cursor, 
    output_path: Path, 
    columns: List[str], 
    chunk_size: int
) -> int:
    """
    Stream results to JSON file (array of objects).
    
    Features:
    - Streaming writes (not loading entire result in memory)
    - Pretty-printed with 2-space indent
    - Handles datetime serialization (ISO format)
    - Converts None -> null
    - UTF-8, no escaping
    
    Output Format:
    [
      {"col1": value1, "col2": value2, ...},
      {"col1": value1, "col2": value2, ...},
      ...
    ]
    """
```

#### Method 6: `validate_output_parameters()`

```python
def validate_output_parameters(
    self, 
    output: str, 
    format: str, 
    location: Optional[str], 
    filename: Optional[str]
) -> Tuple[bool, Optional[str]]:
    """
    Validates:
    - output: 'auto', 'screen', or 'file'
    - format: 'csv' or 'json'
    - location: must be directory, not file
    - filename: no invalid characters, not Windows reserved names
    
    Reserved Names Blocked: CON, PRN, AUX, NUL, COM1-9, LPT1-9
    Invalid Chars: < > : " | ? *
    """
```

---

## 5. Integration in main.py

### Query Execution Flow

```python
@with_request_isolation("execute_query")
async def handle_execute_query(
    name: str, 
    arguments: Optional[Dict[str, Any]] = None,
    request_ctx: RequestContext = None
) -> Sequence[Union[mcp_types.TextContent, ...]]:
    """
    PARAMETER HANDLING (All AI-provided parameters override env vars):
    
    Input Parameters:
    - query: SQL to execute (required)
    - database: Target database (optional)
    - schema: Target schema (optional)
    - limit: Row limit for screen output (default: 100)
    - output: 'auto|screen|file' (overrides DEFAULT_OUTPUT)
    - format: 'csv|json' (overrides DEFAULT_FILE_FORMAT)
    - location: Output dir (overrides DEFAULT_OUTPUT_DIR)
    - filename: Custom filename (overrides auto-generation)
    - use_transaction: Enable transaction boundary management
    - auto_commit: Auto-commit when use_transaction=true
    
    PRECEDENCE RULES:
    1. User-provided parameters take priority
    2. Environment variables are fallback defaults
    3. Hard-coded defaults are last resort
    
    EXAMPLE PRECEDENCE:
    If user provides: {"query": "...", "format": "json"}
    - format = "json" (user override)
    - location = DEFAULT_OUTPUT_DIR (env fallback)
    - filename = auto-generated (hard default)
    """
    
    # Load configuration
    config = get_config()
    output_config = config.output
    
    # Apply defaults from environment ONLY if AI didn't specify
    if output_mode is None:
        output_mode = output_config.default_output
    if file_format is None:
        file_format = output_config.default_file_format
    if location is None:
        location = output_config.default_output_dir
    
    # Initialize output handler
    output_handler = ResultOutputHandler(output_config)
    
    # Validate output parameters
    is_valid, error_msg = output_handler.validate_output_parameters(
        output_mode, file_format, location, filename
    )
    if not is_valid:
        return [mcp_types.TextContent(type="text", text=f"Error: {error_msg}")]
    
    # Determine output strategy
    use_file, reasoning = await output_handler.estimator.should_use_file_output(
        original_query, db_ops, 
        force_output=None if output_mode == "auto" else output_mode
    )
    
    if use_file:
        # FILE OUTPUT PATH
        result = await output_handler.write_to_file(
            original_query, db_ops, file_format, location, filename
        )
        
        response_text = f"""Query executed and saved to file.

**Configuration:** {output_handler.config.model_name} (limit: {output_handler.config.model_token_limit:,} tokens)
**Output Decision:** {reasoning['reason']}

**Parameters Used:**
- Filename: {result['file_path'].split('/')[-1]}
- Location: {location}
- Format: {file_format}

**File Details:**
- Full Path: `{result['file_path']}`
- Format: {result['format'].upper()}
- Rows: {result['rows_written']:,}
- Columns: {result['columns_written']}
- Size: {result['file_size_readable']}

**Database Context:** {current_db}.{current_schema}
**Request ID:** {request_ctx.request_id}

File saved successfully. You can read this file for analysis."""
        
        return [mcp_types.TextContent(type="text", text=response_text)]
    
    else:
        # SCREEN OUTPUT PATH (existing logic)
        # ... format results as markdown table ...
        return [mcp_types.TextContent(type="text", text=result)]
```

---

## 6. Project Folder Management Patterns

### Note: Snowflake MCP Doesn't Have Explicit Folder Management

The Snowflake MCP server does NOT implement explicit project folder creation/listing/removal utilities. Instead:

**Architecture Pattern:**
1. **Folder Creation is Implicit**
   - `resolve_output_path()` calls `output_dir.mkdir(parents=True, exist_ok=True)`
   - Folders created on-demand during first file write
   - No separate "create folder" command needed

2. **Folder Listing**
   - Not implemented (not needed for output handling)
   - If Alpha Vantage needs it, implement custom utilities

3. **Folder Removal**
   - Not implemented (files are left for user management)
   - Security-first: don't delete user data

### Recommended Pattern for Alpha Vantage

If you need project folder management (for data folders, cache, etc.):

```python
class ProjectFolderManager:
    """Manage project-specific folders."""
    
    def __init__(self, client_root: str):
        self.client_root = Path(client_root)
    
    async def create_folder(self, relative_path: str) -> Dict[str, Any]:
        """Create a project folder."""
        folder_path = (self.client_root / relative_path).resolve()
        
        # Security: Ensure it's under client_root
        if not folder_path.is_relative_to(self.client_root):
            raise ValueError(f"Path outside client root: {relative_path}")
        
        folder_path.mkdir(parents=True, exist_ok=True)
        return {"path": str(folder_path), "created": True}
    
    async def list_folders(self, relative_path: str = ".") -> List[Dict]:
        """List folders in project."""
        folder_path = (self.client_root / relative_path).resolve()
        
        if not folder_path.is_relative_to(self.client_root):
            raise ValueError(f"Path outside client root: {relative_path}")
        
        folders = [
            {
                "name": item.name,
                "path": str(item.relative_to(self.client_root)),
                "size_bytes": sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
            }
            for item in folder_path.iterdir() if item.is_dir()
        ]
        return folders
    
    async def remove_folder(self, relative_path: str, recursive: bool = False) -> Dict[str, Any]:
        """Remove a project folder."""
        folder_path = (self.client_root / relative_path).resolve()
        
        # Security checks
        if not folder_path.is_relative_to(self.client_root):
            raise ValueError(f"Path outside client root: {relative_path}")
        
        if not folder_path.exists():
            raise ValueError(f"Folder does not exist: {relative_path}")
        
        if recursive:
            import shutil
            shutil.rmtree(folder_path)
        else:
            folder_path.rmdir()  # Only works if empty
        
        return {"path": str(folder_path), "removed": True}
```

---

## 7. Key Code Patterns to Adopt

### Pattern 1: Configuration with Pydantic

**Why:** Type-safe, validated configuration with automatic defaults and type coercion

```python
from pydantic import BaseModel, Field, validator

class MyConfig(BaseModel):
    """Configuration class."""
    
    param1: str = Field("default", description="Parameter description")
    param2: int = Field(100, description="Another parameter")
    
    @validator('param1')
    def validate_param1(cls, v):
        if not v:
            raise ValueError("param1 cannot be empty")
        return v
```

### Pattern 2: Environment Variable Loading

```python
def get_env(key: str, default=None, type_func=str):
    """Get environment variable with type coercion."""
    value = os.getenv(key, default)
    if value is None:
        return default
    if type_func is bool:
        return str(value).lower() in ('true', '1', 'yes', 'on')
    return type_func(value)

# Usage
config = MyConfig(
    param1=get_env("MY_PARAM1", "default_value"),
    param2=get_env("MY_PARAM2", 100, int),
)
```

### Pattern 3: Security - Path Validation

```python
def validate_client_path(user_path: str, client_root: str) -> Path:
    """Validate user path is within client root."""
    resolved_path = (Path(client_root) / user_path).resolve()
    client_root_resolved = Path(client_root).resolve()
    
    # Check if path is within client root
    if not resolved_path.is_relative_to(client_root_resolved):
        raise ValueError(f"Path outside client root: {user_path}")
    
    return resolved_path
```

### Pattern 4: Async Streaming for Large Data

```python
async def stream_results(cursor, output_file, chunk_size: int = 10000):
    """Stream database results to file."""
    rows_written = 0
    
    while True:
        rows = await cursor.fetchmany(chunk_size)
        if not rows:
            break
        
        for row in rows:
            # Process and write each row
            output_file.write(format_row(row))
            rows_written += 1
    
    return rows_written
```

### Pattern 5: Metadata Enrichment

```python
def get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """Get comprehensive file metadata."""
    stat = os.stat(file_path)
    return {
        "file_path": str(file_path.absolute()),
        "file_size_bytes": stat.st_size,
        "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
        "file_size_readable": format_bytes(stat.st_size),
        "created_time": datetime.fromtimestamp(stat.st_ctime),
        "modified_time": datetime.fromtimestamp(stat.st_mtime),
    }

def format_bytes(bytes_count: int) -> str:
    """Format bytes into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"
```

### Pattern 6: Rich Error Messages

```python
try:
    result = await operation()
except ValueError as e:
    return [mcp_types.TextContent(
        type="text",
        text=f"Configuration Error: {str(e)}\n\n"
             f"Please ensure MCP_CLIENT_ROOT is set correctly.\n"
             f"Current value: {os.getenv('MCP_CLIENT_ROOT', 'NOT SET')}"
    )]
```

### Pattern 7: Tool Registration Pattern

```python
def create_server() -> Server:
    server = Server(
        name="my-mcp-server",
        version="0.1.0",
        instructions="Server instructions for AI"
    )
    
    # Tool implementations
    @server.call_tool()
    async def call_tool(
        name: str, 
        arguments: Optional[Dict[str, Any]] = None
    ) -> Sequence[Union[mcp_types.TextContent, ...]]:
        if name == "tool1":
            return await handle_tool1(name, arguments)
        elif name == "tool2":
            return await handle_tool2(name, arguments)
        else:
            return [mcp_types.TextContent(type="text", text=f"Unknown tool: {name}")]
    
    # Tool definitions
    @server.list_tools()
    async def list_tools() -> List[mcp_types.Tool]:
        """Return available tools."""
        return [
            mcp_types.Tool(
                name="tool1",
                description="Tool 1 description",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "param": {"type": "string", "description": "Parameter"}
                    },
                    "required": ["param"]
                }
            ),
            # ... more tools
        ]
    
    return server
```

---

## 8. Critical Lessons for Alpha Vantage Implementation

### 8.1 Security First
- Always validate MCP_CLIENT_ROOT is set
- Never allow writing outside client project directory
- Use `is_relative_to()` for path validation
- Test write permissions before attempting writes

### 8.2 Configuration Strategy
- Use environment variables for deployment-time config
- Use Pydantic for type-safe configuration
- Apply "parameter override" pattern (AI params > env vars > hard defaults)
- Document all config options in .env.example

### 8.3 Output Management
- Use simple heuristics (row count) rather than complex token estimation
- Let Claude manage its own context window
- Implement three-tier output: (1) AI requests it, (2) heuristic decision, (3) fallback
- Always provide metadata about what happened and why

### 8.4 Error Handling
- Rich error messages that explain what went wrong AND how to fix it
- Include current configuration state in error responses
- Use structured logging with request IDs for debugging

### 8.5 Async Patterns
- Use chunked streaming for large data sets
- Context managers for resource cleanup
- Proper error handling in async contexts
- Don't block on I/O operations

### 8.6 File Management
- Auto-generate filenames with timestamps/hashes
- Lazy folder creation (mkdir on first write)
- Human-readable file paths and formats
- Metadata enrichment (size, row count, timestamp, etc.)

---

## 9. Environment Configuration Template for Alpha Vantage

```bash
# ============================================================================
# Alpha Vantage MCP Server Output Configuration
# ============================================================================

# CRITICAL: Client project root (must be set by MCP client)
MCP_CLIENT_ROOT=/Users/yourname/projects/your-project

# Model Configuration (adjust based on your model)
MODEL_NAME=claude-4-sonnet
MODEL_CONTEXT_TOKEN_LIMIT=200000
MODEL_SAFETY_MARGIN=0.7

# Output Management
DEFAULT_OUTPUT=auto                    # auto|screen|file
DEFAULT_FILE_FORMAT=csv                # csv|json
DEFAULT_OUTPUT_DIR=./av_data          # Relative to MCP_CLIENT_ROOT

# Data Management
SCREEN_OUTPUT_ROW_THRESHOLD=1000      # Use file output for larger results
AUTO_GENERATE_FILENAME=true
FILENAME_PATTERN=av_{date}_{time}    # Available: {date}, {time}, {timestamp}, {query_hash}

# Advanced Options
TOKEN_ESTIMATION_SAMPLE_SIZE=100
LOG_TOKEN_ESTIMATION=false
```

---

## 10. Testing the Implementation

### Test Case 1: Output Decision Logic
```python
async def test_output_decision():
    config = OutputConfig(
        model_token_limit=100000,
        safety_margin=0.7,
        screen_output_row_threshold=1000
    )
    estimator = TokenEstimator(config)
    
    # Test 1: Small result (should use screen)
    use_file, reasoning = await estimator.should_use_file_output(
        "SELECT * FROM small_table",  # 500 rows
        db_ops,
        force_output="auto"
    )
    assert use_file == False
    
    # Test 2: Large result (should use file)
    use_file, reasoning = await estimator.should_use_file_output(
        "SELECT * FROM large_table",  # 5000 rows
        db_ops,
        force_output="auto"
    )
    assert use_file == True
    
    # Test 3: Forced file output
    use_file, reasoning = await estimator.should_use_file_output(
        "SELECT * FROM table",
        db_ops,
        force_output="file"
    )
    assert use_file == True
```

### Test Case 2: Path Security
```python
def test_path_security():
    handler = ResultOutputHandler(config)
    
    # Should fail: relative path without client_root
    try:
        handler.resolve_output_path("./data/file.csv", "data.csv")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "MCP_CLIENT_ROOT" in str(e)
    
    # Should succeed: client_root provided
    config.client_root = "/Users/rob/projects/myproject"
    handler = ResultOutputHandler(config)
    path = handler.resolve_output_path("./data", "results.csv")
    assert str(path).startswith("/Users/rob/projects/myproject")
```

---

## Summary

The Snowflake MCP output helper is a production-grade system designed around:
1. **Security** - Never pollute server directory, validate all paths
2. **Configuration** - Environment-driven, type-safe, with AI override capability
3. **Efficiency** - Streaming writes, chunked processing, minimal memory
4. **User Experience** - Rich metadata, clear error messages, human-readable outputs
5. **Simplicity** - Heuristic-based decisions, not complex token estimation

These patterns are directly applicable to the Alpha Vantage MCP server for data output management.
