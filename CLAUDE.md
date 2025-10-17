# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Alpha Vantage MCP Server is a Model Context Protocol (MCP) implementation that provides LLMs and agentic workflows access to real-time and historical financial market data via Alpha Vantage APIs. It can be deployed as:
- AWS Lambda function with CloudFront distribution (production)
- Local HTTP server for development/testing
- Standalone stdio server (for local MCP client connections via `uvx av-mcp`)

## Architecture

### Core Components

**MCP Handler (`server/lambda_function.py`)**
- Entry point for Lambda and HTTP requests
- OAuth 2.1 authentication flow handling
- Dynamic tool registration based on requested categories
- Analytics logging for tool usage tracking

**Tool System (`server/src/tools/`)**
- Tools organized by category (core_stock_apis, options_data_apis, technical_indicators, etc.)
- Registry-based lazy loading of tools to reduce cold start times
- Custom decorator system with automatic entitlement parameter injection
- 90+ financial data tools mapping to Alpha Vantage API endpoints

**Response Handling (`server/src/common.py`)**
- Automatic token estimation for API responses
- Large response (>50k tokens) handling via Cloudflare R2 upload
- Preview generation with sample data for oversized responses
- Environment-configurable response size limits (`MAX_RESPONSE_TOKENS`)

**Authentication (`server/src/oauth.py`)**
- OAuth 2.1 metadata discovery (`/.well-known/oauth-authorization-server`)
- Authorization endpoint (`/authorize`)
- Token exchange endpoint (`/token`)
- Client registration endpoint (`/register`)

### Deployment Architecture

**AWS Infrastructure:**
- Lambda function with VPC support (Python 3.13 runtime)
- API Gateway for HTTP endpoints
- CloudFront distribution with custom domain
- S3 bucket for static web assets
- IAM roles with least privilege access

**External Services:**
- Cloudflare R2 for large response storage
- Alpha Vantage API for financial data

## Development Workflow

### Local Development Setup

**First-time setup:**
```bash
cd server
uv sync
```

This installs all dependencies into a local virtual environment at `.venv/`.

**Configure Claude Code to use local version:**

The `.mcp.json` file is configured to run the local development version:
```json
{
  "mcpServers": {
    "alphavantage": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/robsherman/Documents/Repos/alpha_vantage_mcp/server",
        "av-mcp",
        "NG0HJC4DLXU6BKPV"
      ]
    }
  }
}
```

This ensures any changes to the code are immediately reflected without needing to publish/reinstall.

**Start local HTTP server:**
```bash
cd server
python local_http_server.py --port 8000
```

The local server wraps `lambda_function.lambda_handler()` to simulate AWS Lambda locally. It accepts the same requests and returns the same responses as the deployed Lambda function.

**Test stdio server directly:**
```bash
uv run av-mcp YOUR_API_KEY
uv run av-mcp YOUR_API_KEY --list-categories
uv run av-mcp YOUR_API_KEY --categories core_stock_apis forex
```

This runs the MCP server in stdio mode for local Claude Desktop, Cursor, or other MCP clients.

### Testing

**Run all tests:**
```bash
cd server
pytest tests/
```

**Key test files:**
- `test_handler_direct.py` - Direct lambda handler invocation tests
- `test_http_transport.py` - HTTP transport layer tests
- `test_stdio_transport.py` - Stdio transport tests
- `test_large_response.py` - Large response handling and R2 upload tests
- `test_openai_schema.py` - OpenAI Actions schema validation
- `test_rate_limit.py` - Rate limiting behavior tests

### Building and Deployment

**Deploy to AWS (complete stack):**
```bash
./scripts/deploy.sh
```

This automated script:
1. Loads environment variables from `.env`
2. Generates `requirements.txt` from `pyproject.toml`
3. Runs `sam build` to package dependencies
4. Deploys infrastructure, Lambda function, and web assets
5. Configures CloudFront distribution

**Deploy web assets only:**
```bash
./scripts/deploy-web.sh
```

**Deploy infrastructure only:**
```bash
./scripts/deploy-infra.sh
```

**Manual SAM build and deploy:**
```bash
cd server
uv export --no-hashes --format requirements-txt > requirements.txt
cd ..
sam build
sam deploy --guided
```

### Web Frontend Development

**Development server:**
```bash
cd web
npm run dev
```

**Build for production:**
```bash
cd web
npm run build
```

The web frontend is a Next.js application with:
- Interactive API documentation viewer
- Code artifact rendering with Monaco editor
- Tailwind CSS + shadcn/ui components
- Deployed to S3 and served via CloudFront

## Tool Development

### Adding New Tools

1. Choose appropriate category file in `server/src/tools/` or create new category
2. Import and use the `@tool` decorator from `registry.py`
3. Use `_make_api_request()` helper for Alpha Vantage API calls
4. Add category to `TOOL_MODULES` dict in `registry.py`
5. For real-time data categories, add to `ENTITLEMENT_CATEGORIES`

**Example:**
```python
from src.tools.registry import tool
from src.common import _make_api_request

@tool
def MY_NEW_TOOL(symbol: str, interval: str = "daily") -> dict | str:
    """
    Description of what this tool does.

    Args:
        symbol: Stock ticker symbol
        interval: Time interval for data

    Returns:
        Market data in requested format
    """
    return _make_api_request("MY_API_FUNCTION", {
        "symbol": symbol,
        "interval": interval,
        "datatype": "csv"
    })
```

### Tool Categories

Tools are automatically registered based on their module location. Available categories:
- `core_stock_apis` - TIME_SERIES_DAILY, GLOBAL_QUOTE, etc.
- `options_data_apis` - REALTIME_OPTIONS, HISTORICAL_OPTIONS
- `alpha_intelligence` - NEWS_SENTIMENT, INSIDER_TRANSACTIONS
- `fundamental_data` - COMPANY_OVERVIEW, INCOME_STATEMENT, etc.
- `forex` - FX_INTRADAY, FX_DAILY, etc.
- `cryptocurrencies` - DIGITAL_CURRENCY_DAILY, etc.
- `commodities` - WTI, BRENT, COPPER, etc.
- `economic_indicators` - REAL_GDP, CPI, UNEMPLOYMENT, etc.
- `technical_indicators` - SMA, EMA, RSI, MACD, etc. (split across 4 modules)
- `ping` - Health check tools

### Entitlement System

Categories in `ENTITLEMENT_CATEGORIES` automatically get an `entitlement` parameter added:
- `entitlement="delayed"` - 15-minute delayed data
- `entitlement="realtime"` - Real-time data (premium tier)

The `add_entitlement_parameter()` decorator:
1. Adds parameter to function signature
2. Updates docstring with parameter description
3. Passes entitlement value to `_make_api_request()` via global context

## Environment Variables

**Required for deployment:**
- `DOMAIN_NAME` - Custom domain for CloudFront (e.g., mcp.alphavantage.co)
- `CERTIFICATE_ARN` - ACM certificate ARN (must be in us-east-1)
- `SUBNET_IDS` - Comma-delimited VPC subnet IDs for Lambda
- `LAMBDA_SECURITY_GROUP_ID` - Security group for Lambda VPC

**Optional (for R2 large response handling):**
- `R2_BUCKET` - Cloudflare R2 bucket name
- `R2_PUBLIC_DOMAIN` - Public domain for R2 objects
- `R2_ENDPOINT_URL` - R2 endpoint URL
- `R2_ACCESS_KEY_ID` - R2 access key
- `R2_SECRET_ACCESS_KEY` - R2 secret key

**Runtime configuration:**
- `MAX_RESPONSE_TOKENS` - Token limit before R2 upload (default: 50000)
- `ENVIRONMENT` - Deployment environment (production/staging)

## Key Files and Locations

- `template.yaml` - SAM template for Lambda, API Gateway, CloudFront
- `server/lambda_function.py` - Lambda entry point
- `server/local_http_server.py` - Local development server
- `server/src/stdio_server.py` - Stdio MCP server (for `uvx av-mcp`)
- `server/src/tools/registry.py` - Tool registration and category management
- `server/src/common.py` - API request helper and response handling
- `server/src/oauth.py` - OAuth 2.1 authentication flow
- `server/src/openai_actions.py` - OpenAI Actions schema generation
- `scripts/deploy.sh` - Main deployment script
- `web/` - Next.js frontend application

## Important Conventions

**Package Management:**
- Use `uv` for Python dependency management (required)
- `pyproject.toml` is the source of truth for dependencies
- `requirements.txt` is generated from `pyproject.toml` for Lambda deployment

**Response Size Management:**
- Responses >50k tokens automatically uploaded to R2
- Preview data (first 50 lines) returned for large responses
- `data_url` provided for fetching full dataset outside chat context

**Category Filtering:**
- Clients can request specific tool categories via `?categories=core_stock_apis,options_data_apis`
- Categories are validated against `TOOL_MODULES` registry
- Invalid categories log warning and fall back to all tools

**OAuth Flow:**
- OAuth endpoints bypass token validation
- All MCP/API endpoints require Bearer token authentication
- Token passed as `apikey` parameter to Alpha Vantage API

**Analytics:**
- Tool calls logged for analytics (method, params, platform)
- Platform detection from User-Agent header
- Analytics data can be queried via Athena (see `analytics/`)
