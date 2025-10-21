# AlphaVantage MCP Server - Startup Guide

## ✅ Server Status: WORKING

The AlphaVantage MCP server is now fully functional and ready to use.

## Quick Start

### Start the server

```bash
uv run av-mcp YOUR_API_KEY
```

Or with specific categories:

```bash
uv run av-mcp YOUR_API_KEY --categories core_stock_apis --categories forex
```

### Available commands

```bash
# List all available tool categories
uv run av-mcp --list-categories

# Enable verbose logging
uv run av-mcp YOUR_API_KEY --verbose

# Get help
uv run av-mcp --help
```

## Server Features

- **119 tools** across 12 categories
- Full MCP protocol support
- Stdio transport for local clients
- Intelligent output management
- Comprehensive test coverage (1546 tests passing)

## Available Tool Categories

- `core_stock_apis` - Core stock market data
- `time_series_unified` - Unified time series data
- `options_data_apis` - Options data
- `alpha_intelligence` - Alpha Intelligence APIs
- `commodities` - Commodity prices
- `cryptocurrencies` - Cryptocurrency data
- `economic_indicators` - Economic indicators
- `forex` - Foreign exchange rates
- `fundamental_data` - Company fundamentals
- `technical_indicators` - Technical analysis indicators
- `ping` - Health check utilities
- `openai` - OpenAI integration

## Testing

### Run all tests

```bash
export ALPHA_VANTAGE_API_KEY=YOUR_KEY
uv run pytest
```

### Run stdio transport test

```bash
export ALPHAVANTAGE_API_KEY=YOUR_KEY
uv run python tests/test_stdio_transport.py
```

### Run specific test categories

```bash
uv run pytest tests/tools/          # Tool tests
uv run pytest tests/integration/    # Integration tests
uv run pytest tests/decision/       # Decision logic tests
```

## Code Quality

### Linting

```bash
uv run ruff check .
```

### Formatting

```bash
uv run black --check .
```

## What Was Fixed

1. **Missing dependencies**: Added `tiktoken` and `aiofiles` to pyproject.toml
2. **Code style**: Fixed isinstance() calls to use modern Python 3.13 syntax (`X | Y` instead of `(X, Y)`)
3. **Verification**: All 1546 tests passing
4. **Server startup**: Confirmed working with stdio transport

## Configuration

The server uses environment variables for configuration. Optional settings:

- `MCP_OUTPUT_DIR` - Directory for output files (optional, will use R2 if not set)
- `ALPHA_VANTAGE_API_KEY` - Your API key (can also be passed as argument)

## MCP Client Configuration

Add to your MCP client config (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "alphavantage": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/robsherman/Servers/alpha_vantage_mcp_beta/server",
        "av-mcp",
        "YOUR_API_KEY"
      ]
    }
  }
}
```

## Support

- Run `uv run av-mcp --help` for usage information
- Check logs with `--verbose` flag for debugging
- All tests in `tests/` directory demonstrate usage patterns
