# Alpha Vantage MCP Server - Architectural Redesign

**Version:** 1.0
**Date:** 2025-10-16
**Status:** Planning Phase

## Executive Summary

This document outlines the architectural redesign of the Alpha Vantage MCP server to address context window limitations and improve usability. The redesign will consolidate 118 individual tools into logical groupings and introduce an intelligent output management system.

**Key Objectives:**
- Reduce context window consumption by 60-80% through tool consolidation
- Implement intelligent file-based output for large datasets
- Improve developer experience through better tool organization
- Provide clean, focused API surface optimized for AI agents

---

## Current State Analysis

### Existing Architecture

**Server Structure:**
- **Location:** `/Users/robsherman/Servers/alpha_vantage_mcp_beta/server/src/`
- **Tool Count:** 118 individual MCP tools
- **Tool Registry:** Dynamic registration via `@tool` decorator
- **API Handler:** Centralized `_make_api_request()` in `common.py`
- **Output Format:** CSV/JSON returned inline in MCP responses

**Tool Categories (11 total):**
1. Core Stock APIs (11 tools) - TIME_SERIES_*, GLOBAL_QUOTE, etc.
2. Options Data (2 tools) - REALTIME_OPTIONS, HISTORICAL_OPTIONS
3. Alpha Intelligence (6 tools) - NEWS_SENTIMENT, EARNINGS_CALL_TRANSCRIPT, etc.
4. Commodities (11 tools) - WTI, BRENT, COPPER, agricultural products
5. Cryptocurrencies (5 tools) - CRYPTO_INTRADAY, DIGITAL_CURRENCY_*
6. Economic Indicators (10 tools) - REAL_GDP, UNEMPLOYMENT, CPI, etc.
7. Forex (4 tools) - FX_INTRADAY, FX_DAILY, FX_WEEKLY, FX_MONTHLY
8. Fundamental Data (12 tools) - COMPANY_OVERVIEW, BALANCE_SHEET, EARNINGS, etc.
9. Technical Indicators (53 tools) - SMA, EMA, RSI, MACD, Bollinger Bands, etc.
10. Health/Utility (2 tools) - PING, ADD_TWO_NUMBERS
11. Placeholder (2 tools) - OpenAI integration, SEARCH

**File Organization:**
```
server/src/tools/
├── registry.py           # Tool registration system
├── core_stock_data.py   # 11 stock tools
├── options.py            # 2 options tools
├── alpha_intelligence.py # 6 intelligence tools
├── commodities.py        # 11 commodity tools
├── cryptocurrencies.py   # 5 crypto tools
├── economic_indicators.py # 10 economic tools
├── forex.py              # 4 forex tools
├── fundamental_data.py   # 12 fundamental tools
├── technical_indicators.py # 53 technical indicator tools
├── ping.py               # 2 utility tools
└── openai.py             # 2 placeholder tools
```

### Problem Statement

**Context Window Consumption:**
- Each tool includes: name, description, parameter schema, examples
- 118 tools × ~200-400 tokens per tool = 23,600-47,200 tokens consumed
- This leaves limited context for actual data and AI reasoning
- Large responses (>25,000 tokens) already trigger MCP limits

**Usability Issues:**
- Tool discovery is overwhelming (118 choices)
- Similar tools have repetitive patterns (e.g., 10 TIME_SERIES variants)
- AI agents struggle to select the correct tool from many similar options
- Parameter patterns are not standardized across similar tool groups

**Output Management:**
- Large datasets returned inline flood the context window
- No mechanism to save outputs for later reference
- No project-based organization of outputs
- AI must process full datasets even when only summary needed

---

## Proposed Solution Architecture

### Phase 1: Output Helper System

**Objective:** Implement intelligent output management based on Snowflake MCP server pattern.

**Components:**

1. **Output Configuration (`output_config.py`)**
   - Pydantic-based configuration model
   - Environment variable loading
   - Default value management
   - Validation and security checks

2. **Output Handler (`output_handler.py`)**
   - Async file writing with streaming
   - CSV/JSON format support
   - Project folder management
   - Metadata generation
   - Security validation (path containment)

3. **Token Estimator (`token_estimator.py`)**
   - tiktoken-based token counting for accurate estimation
   - Decision logic (file vs inline) based on token thresholds
   - Fallback row-count estimation for non-text data
   - Configurable thresholds with override capabilities

**Configuration Variables:**
```bash
# Required
MCP_OUTPUT_DIR=/Users/robsherman/Documents/alpha_vantage_outputs

# Optional (with defaults)
MCP_PROJECT_NAME=default
MCP_OUTPUT_AUTO=true
MCP_OUTPUT_TOKEN_THRESHOLD=1000
MCP_OUTPUT_CSV_THRESHOLD=100
MCP_OUTPUT_FORMAT=csv
MCP_OUTPUT_COMPRESSION=false
MCP_OUTPUT_METADATA=true
MCP_STREAMING_CHUNK_SIZE=10000
MCP_MAX_INLINE_ROWS=50
MCP_ENABLE_PROJECT_FOLDERS=true
MCP_DEFAULT_FOLDER_PERMISSIONS=0o755
```

**Security Architecture:**
- **Path Validation:** All paths validated with `Path.is_relative_to(MCP_OUTPUT_DIR)`
- **Filename Sanitization:** Block invalid characters, Windows reserved names
- **Permission Checks:** Test write permissions before operations
- **No Server Pollution:** Never write to server installation directory
- **Directory Traversal Prevention:** Reject paths with `..` or absolute paths

**Decision Logic:**
```python
# tiktoken-based token counting with fallback
token_count = estimate_tokens(data)  # Uses tiktoken library
if token_count > MCP_OUTPUT_TOKEN_THRESHOLD:
    write_to_file()
else:
    return_inline()
```

### Phase 2: Tool Consolidation

**Objective:** Reduce 118 tools to ~20-25 flexible, parameterized tools.

**Consolidation Strategy:**

**Group 1: Time Series Data (11→1 tool)**
- **New Tool:** `GET_TIME_SERIES`
- **Series Type Parameter:** `intraday | daily | daily_adjusted | weekly | weekly_adjusted | monthly | monthly_adjusted`
- **Interval Parameter:** `1min | 5min | 15min | 30min | 60min` (for intraday only)
- **Consolidates:** TIME_SERIES_INTRADAY, TIME_SERIES_DAILY, TIME_SERIES_DAILY_ADJUSTED, etc.

**Group 2: Technical Indicators (53→5-6 tools)**
- **Moving Averages:** SMA, EMA, WMA, DEMA, TEMA, TRIMA, KAMA, MAMA, VWAP, T3 → `GET_MOVING_AVERAGE`
- **Oscillators:** RSI, STOCH, STOCHF, STOCHRSI, WILLR, MOM, APO, PPO, ROC, ROCR → `GET_OSCILLATOR`
- **Trend Indicators:** MACD, MACDEXT, ADX, ADXR, AROON, AROONOSC, BOP, CCI → `GET_TREND_INDICATOR`
- **Volatility:** BBANDS, ATR, NATR, TRANGE → `GET_VOLATILITY_INDICATOR`
- **Volume:** AD, ADOSC, OBV → `GET_VOLUME_INDICATOR`
- **Cycle:** HT_TRENDLINE, HT_SINE, HT_TRENDMODE, HT_DCPERIOD, HT_DCPHASE, HT_PHASOR → `GET_CYCLE_INDICATOR`

**Group 3: Forex Data (4→1 tool)**
- **New Tool:** `GET_FOREX_DATA`
- **Interval Parameter:** `intraday | daily | weekly | monthly`
- **Consolidates:** FX_INTRADAY, FX_DAILY, FX_WEEKLY, FX_MONTHLY

**Group 4: Cryptocurrency Data (5→1 tool)**
- **New Tool:** `GET_CRYPTO_DATA`
- **Data Type Parameter:** `intraday | daily | weekly | monthly | rating`
- **Consolidates:** CRYPTO_INTRADAY, DIGITAL_CURRENCY_DAILY, DIGITAL_CURRENCY_WEEKLY, DIGITAL_CURRENCY_MONTHLY, CRYPTO_RATING

**Group 5: Fundamental Data (12→3 tools)**
- **Financial Statements:** `GET_FINANCIAL_STATEMENTS` (income, balance, cash_flow)
- **Company Data:** `GET_COMPANY_DATA` (overview, earnings, earnings_calendar, dividends, splits)
- **Market Data:** `GET_MARKET_DATA` (IPO calendar, listing status, ETF profile)

**Group 6: Commodities (11→2 tools)**
- **Energy:** `GET_ENERGY_COMMODITY` (WTI, BRENT, NATURAL_GAS)
- **Materials:** `GET_MATERIALS_COMMODITY` (COPPER, ALUMINUM, WHEAT, CORN, COTTON, SUGAR, COFFEE, ALL_COMMODITIES)

**Group 7: Economic Indicators (10→1 tool)**
- **New Tool:** `GET_ECONOMIC_INDICATOR`
- **Indicator Parameter:** `real_gdp | real_gdp_per_capita | treasury_yield | federal_funds_rate | cpi | inflation | retail_sales | durables | unemployment | nonfarm_payroll`
- **Consolidates:** REAL_GDP, REAL_GDP_PER_CAPITA, TREASURY_YIELD, FEDERAL_FUNDS_RATE, CPI, INFLATION, RETAIL_SALES, DURABLES, UNEMPLOYMENT, NONFARM_PAYROLL

**Group 8: Keep As-Is (6 tools)**
- Stock quotes: GLOBAL_QUOTE, SYMBOL_SEARCH, REALTIME_BULK_QUOTES
- Alpha Intelligence: NEWS_SENTIMENT, EARNINGS_CALL_TRANSCRIPT, TOP_GAINERS_LOSERS, INSIDER_TRANSACTIONS
- Options: REALTIME_OPTIONS, HISTORICAL_OPTIONS
- Analytics: ANALYTICS_FIXED_WINDOW, ANALYTICS_SLIDING_WINDOW
- Utility: PING, MARKET_STATUS

**Consolidated Tool Count: ~25 tools (78% reduction)**

**New Parameter Pattern:**
```python
@tool
def get_time_series(
    symbol: str,
    series_type: Literal["intraday", "daily", "daily_adjusted", ...],
    interval: Optional[Literal["1min", "5min", ...]] = None,
    outputsize: Literal["compact", "full"] = "compact",
    datatype: Literal["json", "csv"] = "csv",
    month: Optional[str] = None,
    entitlement: Literal["delayed", "realtime"] = "delayed"
) -> List[types.TextContent]:
    """
    Get time series stock data in various granularities.

    Replaces: TIME_SERIES_INTRADAY, TIME_SERIES_DAILY, TIME_SERIES_DAILY_ADJUSTED,
              TIME_SERIES_WEEKLY, TIME_SERIES_WEEKLY_ADJUSTED, TIME_SERIES_MONTHLY,
              TIME_SERIES_MONTHLY_ADJUSTED
    """
    ...
```

### Phase 3: Integration & Testing

**Objective:** Integrate output helper with consolidated tools and ensure quality.

**Integration Points:**

1. **Tool Handler Integration**
   ```python
   async def get_time_series(...):
       # Make API request
       data = await _make_api_request(...)

       # Check if output helper should be used
       if should_use_output_helper(data):
           file_path = await output_handler.write_output(data, ...)
           return create_file_reference_response(file_path)
       else:
           return create_inline_response(data)
   ```

2. **Project Management Tools**
   - `create_project_folder(name: str)` - Create new project folder
   - `list_project_files(project: str)` - List files in project
   - `delete_project_file(project: str, filename: str)` - Remove file
   - `list_projects()` - List all projects

3. **Configuration Loading**
   - Load output config at server startup
   - Validate MCP_OUTPUT_DIR existence
   - Create default project folder if needed

**Testing Strategy:**

1. **Unit Tests**
   - Output configuration validation
   - Path security validation
   - Token estimation accuracy
   - File writing operations
   - Project folder management

2. **Integration Tests**
   - Tool consolidation correctness
   - Output helper decision logic
   - End-to-end file writing
   - Large dataset handling

3. **Performance Tests**
   - Context window usage comparison
   - File I/O performance
   - Memory usage with streaming

---

## Design Decisions

### 1. **Conservative Consolidation Approach**

**Decision:** Focus on high-value consolidations (time series, technical indicators, forex, crypto) while keeping complex tools separate.

**Rationale:**
- Some tools (NEWS_SENTIMENT, OPTIONS) have unique parameters that don't fit consolidation patterns
- Over-consolidation increases parameter complexity
- Better to have 25 clear tools than 10 confusing ones

### 2. **Snowflake Output Helper Pattern**

**Decision:** Adopt Snowflake MCP server's output helper architecture with enhanced token estimation.

**Rationale:**
- Proven pattern in production use
- Security-first design already validated
- Enhanced with tiktoken library for accurate token counting
- Project folder concept is valuable for organization
- Restrictive security model (output within MCP_OUTPUT_DIR only)

### 3. **Parameter Standardization**

**Decision:** Use consistent parameter names across tool groups (e.g., `symbol`, `interval`, `series_type`).

**Rationale:**
- Easier for AI agents to learn patterns
- Reduces documentation overhead
- Improves developer experience

### 4. **Output Format Defaults**

**Decision:** Default to CSV output with optional JSON.

**Rationale:**
- CSV is more token-efficient for tabular data
- Easier for AI to parse structured data
- Matches Alpha Vantage API's recommended format

---

## Technology Stack

**Core:**
- Python 3.13+
- MCP SDK 1.12.3+
- Pydantic 2.0+ (for configuration validation)
- aiofiles (for async file I/O)

**Existing Dependencies:**
- click 8.2.1+ (CLI)
- loguru 0.7.3+ (logging)
- python-dotenv 1.1.1+ (environment variables)

**Development:**
- pytest 7.0.0+ (testing)
- pytest-asyncio 0.21.0+ (async testing)
- black 23.0.0+ (formatting)
- ruff 0.1.0+ (linting)

**No New Runtime Dependencies Required**

---

## Success Criteria

### Quantitative Metrics

1. **Context Window Reduction:** ≥60% reduction in tool metadata tokens
   - Before: ~30,000-40,000 tokens
   - After: ≤15,000 tokens

2. **Tool Count:** Reduce from 118 to ≤25 tools (78% reduction)

3. **Performance:** File I/O operations complete in <2 seconds for datasets up to 10MB

4. **Test Coverage:** ≥85% code coverage for new components

### Qualitative Metrics

1. **Developer Experience:** Improved tool discoverability (measured by developer feedback)

2. **AI Agent Efficiency:** Faster tool selection (fewer retries, measured in logs)

3. **Security:** Zero path traversal or unauthorized file access incidents

4. **Token Estimation:** Estimation accuracy within 10% of actual token count

### Acceptance Criteria

- [ ] All 118 original tools accessible through new consolidated tools
- [ ] Output helper successfully writes files to configured directory
- [ ] Project folder management tools functional
- [ ] All security validations passing
- [ ] Documentation complete and accurate
- [ ] Test suite passing with ≥85% coverage
- [ ] No regression in API functionality

---

## Implementation Timeline

### Phase 1: Output Helper System (Weeks 1-3)
- Implement output configuration and security
- Build output handler with streaming
- Add token estimation with tiktoken
- Create project management utilities
- Comprehensive unit testing

### Phase 2: Tool Consolidation (Weeks 4-7)
- Implement consolidated tools with new parameter patterns
- Integrate output helper decision logic
- Create comprehensive integration tests
- Update all tool documentation

### Phase 3: Integration & QA (Weeks 8-10)
- Full system integration testing
- Performance and security testing
- Documentation completion
- Beta release preparation

---

## Risk Assessment

### High Risk

**Risk:** Security vulnerabilities in file operations
**Mitigation:** Adopt proven Snowflake security patterns, restrictive path validation, comprehensive security testing, code review

### Medium Risk

**Risk:** Performance degradation with file I/O
**Mitigation:** Async streaming, chunked writes, performance testing, monitoring

**Risk:** Configuration complexity for users
**Mitigation:** Sensible defaults, clear documentation, validation with helpful errors

### Low Risk

**Risk:** Parameter naming conflicts
**Mitigation:** Early design review, consistent naming conventions, documentation

**Risk:** Token estimation accuracy
**Mitigation:** Use tiktoken library for accurate counting, fallback row-count estimation, configurable thresholds, performance testing

---

## Future Enhancements

1. **Smart Caching:** Cache API responses to reduce redundant calls
2. **Batch Operations:** Allow multiple symbols in single request
3. **Data Transformations:** Built-in aggregations, filters, calculations
4. **Webhook Support:** Real-time data streaming for subscriptions
5. **Cloud Storage:** Optional S3/R2 integration for large outputs
6. **Query Builder:** Interactive tool selection UI for complex queries

---

## References

**Source Code:**
- Current implementation: `/Users/robsherman/Servers/alpha_vantage_mcp_beta/`
- Snowflake MCP reference: `/Users/robsherman/Servers/snowflake-mcp-server/`

**Documentation:**
- Agent exploration: `docs/SNOWFLAKE_OUTPUT_PATTERNS.md`
- Tool analysis: `/tmp/alpha_vantage_tools_analysis.md`
- Consolidation strategy: `/tmp/alpha_vantage_consolidation_strategy.md`

**External:**
- Alpha Vantage API: https://www.alphavantage.co/documentation/
- MCP Specification: https://modelcontextprotocol.io/
- Snowflake MCP: https://github.com/ModelContextProtocol/servers/tree/main/src/snowflake

---

**Document Status:** Draft - Ready for Review
**Next Review Date:** Before Phase 1 implementation start
**Owner:** Rob Sherman (rob.sherman@highway.ai)
