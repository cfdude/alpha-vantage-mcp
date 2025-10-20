# Sprint 4 Plan: Integration & Testing Part 1

**Sprint**: Sprint 4 - Output Helper Integration & Testing
**Goal**: Integrate Sprint 1 output helper across all consolidated tools from Sprint 2 & 3
**Story Points**: 40
**Issues**: AVB-801 through AVB-914
**Phase**: Phase 3 Milestones 3.1 & 3.2 (partial)
**Duration**: 2 weeks (estimated)

---

## Executive Summary

Sprint 4 integrates the output helper system (built in Sprint 1) into all consolidated tools from Sprint 2 & 3. This enables intelligent file/inline decisions, proper handling of the `force_inline` and `force_file` parameters, and comprehensive testing of the integrated system.

### Current State Analysis

**What Exists (Sprint 1)**:
- ✅ `OutputConfig` - Pydantic configuration management with env vars
- ✅ `Security` - Path traversal prevention, filename sanitization
- ✅ `OutputHandler` - Async file I/O with streaming
- ✅ `TokenEstimator` - Intelligent token estimation with tiktoken
- ✅ Integration helpers - `should_use_output_helper()`, response creators
- ✅ Structured logging with loguru
- ✅ 184+ tests with ≥90% coverage

**What Exists (Sprint 2 & 3)**:
- ✅ 15 consolidated tools (5 from Sprint 2, 10 from Sprint 3)
- ✅ Pydantic schemas with `force_inline` and `force_file` parameters
- ✅ 1,318 tests (650 Sprint 2 + 668 Sprint 3) at 100% pass rate
- ⚠️ Tools use simple `_make_api_request()` - NOT integrated with output helper
- ⚠️ `force_inline`/`force_file` parameters exist but aren't used

**The Gap**:
Sprint 2 & 3 tools have the parameters (`force_inline`, `force_file`) defined in their schemas but don't actually USE the output helper. They pass these to `_make_api_request()` which currently ignores them.

---

## Sprint 4 Objectives

### Primary Goals
1. **Integrate output helper** into all 15 consolidated tools (Sprint 2 + 3)
2. **Replace `_make_api_request()`** with output helper-aware version
3. **Server startup integration** with config validation
4. **Comprehensive testing** - unit, integration, performance

### Success Criteria
- ✅ Output helper integrated across all 15 tools
- ✅ `force_inline`/`force_file` parameters fully functional
- ✅ Server validates MCP_OUTPUT_DIR on startup
- ✅ Unit test coverage ≥85%
- ✅ Integration tests passing
- ✅ Performance validated (<2s for 10MB datasets)

---

## Epic Breakdown

### Epic 3.1.1: Tool Handler Integration (13 points, AVB-801 to AVB-807)

**Objective**: Integrate output helper across all consolidated tools

#### AVB-801: Audit All Tools for Integration Points (2 pts)
**Tasks**:
- [ ] Audit all 5 Sprint 2 tools (time_series, forex_crypto, moving_average, oscillator)
- [ ] Audit all 10 Sprint 3 tools (trend, volatility, volume, cycle, financial_statements, company_data, market_data, economic_indicators, energy_commodity, materials_commodity)
- [ ] Document current `_make_api_request()` usage patterns
- [ ] Identify where `force_inline`/`force_file` parameters are defined but not used
- [ ] Create integration checklist for each tool

**Deliverables**:
- Integration audit report
- Checklist of 15 tools requiring updates

---

#### AVB-802: Add Output Helper to Time Series Tools (2 pts)
**Tasks**:
- [ ] Update `time_series_unified.py` to import output helper
- [ ] Replace `_make_api_request()` with `OutputHandler` integration
- [ ] Pass `force_inline`/`force_file` from request to output helper
- [ ] Update error handling to use output helper responses
- [ ] Test all 8 time series variants (intraday, daily, weekly, monthly, quote, bulk, search, status)

**Technical Changes**:
```python
# Before (Sprint 2)
from src.common import _make_api_request

api_function, params = route_request(request)
return await _make_api_request(api_function, params)

# After (Sprint 4)
from src.integration.helpers import should_use_output_helper, create_response

api_function, params = route_request(request)
response_data = await _make_api_request(api_function, params)

# Use output helper if appropriate
if should_use_output_helper(response_data, request.force_inline, request.force_file):
    return await create_file_response(response_data, request)
else:
    return create_inline_response(response_data)
```

**Files Modified**:
- `server/src/tools/time_series_unified.py`

**Tests Required**:
- Integration tests for inline vs file output
- Tests for `force_inline` parameter
- Tests for `force_file` parameter
- Tests for automatic file threshold

---

#### AVB-803: Add Output Helper to Technical Indicators (3 pts)
**Tasks**:
- [ ] Update `moving_average_unified.py` (10 indicators)
- [ ] Update `oscillator_unified.py` (17 indicators)
- [ ] Update `trend_unified.py` (7 indicators)
- [ ] Update `volatility_unified.py` (7 indicators)
- [ ] Update `volume_unified.py` (4 indicators)
- [ ] Update `cycle_unified.py` (6 Hilbert Transform indicators)

**Complexity**: 51 total technical indicators across 6 tools

**Files Modified**:
- `server/src/tools/moving_average_unified.py`
- `server/src/tools/oscillator_unified.py`
- `server/src/tools/trend_unified.py`
- `server/src/tools/volatility_unified.py`
- `server/src/tools/volume_unified.py`
- `server/src/tools/cycle_unified.py`

**Tests Required**:
- Integration tests for each of the 6 tools
- Parameterized tests across indicator types
- File output validation tests

---

#### AVB-804: Add Output Helper to Fundamental/Economic (3 pts)
**Tasks**:
- [ ] Update `financial_statements_unified.py` (3 statement types)
- [ ] Update `company_data_unified.py` (5 data types)
- [ ] Update `market_data_unified.py` (3 request types)
- [ ] Update `economic_indicators_unified.py` (10 indicators)

**Files Modified**:
- `server/src/tools/financial_statements_unified.py`
- `server/src/tools/company_data_unified.py`
- `server/src/tools/market_data_unified.py`
- `server/src/tools/economic_indicators_unified.py`

**Tests Required**:
- Integration tests for all 4 tools
- Tests for large financial statement handling
- Tests for economic data file output

---

#### AVB-805: Add Output Helper to Commodity/Market Data (2 pts)
**Tasks**:
- [ ] Update `energy_commodity_unified.py` (3 commodities)
- [ ] Update `materials_commodity_unified.py` (8 commodities)
- [ ] Update `forex_crypto_unified.py` (forex + crypto)

**Files Modified**:
- `server/src/tools/energy_commodity_unified.py`
- `server/src/tools/materials_commodity_unified.py`
- `server/src/tools/forex_crypto_unified.py`

**Tests Required**:
- Integration tests for commodity tools
- Tests for forex/crypto output handling

---

#### AVB-806: Verify Consistent Integration Pattern (1 pt)
**Tasks**:
- [ ] Verify all 15 tools follow same output helper pattern
- [ ] Check error handling consistency
- [ ] Validate parameter passing (force_inline, force_file)
- [ ] Review code for duplication opportunities
- [ ] Create shared helper if patterns are repeated

**Deliverables**:
- Integration pattern documentation
- Consistency audit report

---

#### AVB-807: Write Integration Smoke Tests (2 pts)
**Tasks**:
- [ ] Write smoke tests for all 15 integrated tools
- [ ] Test inline output mode
- [ ] Test file output mode
- [ ] Test force_inline parameter
- [ ] Test force_file parameter
- [ ] Test automatic threshold behavior

**Test Coverage Goal**: ≥85% for integration code

**Files Created**:
- `server/tests/integration/test_tool_output_integration.py`

---

### Epic 3.1.2: Server Startup Integration (7 points, AVB-808 to AVB-813)

**Objective**: Integrate configuration validation into server startup

#### AVB-808: Add Config Loading to Server Startup (2 pts)
**Tasks**:
- [ ] Import `OutputConfig` in main server file
- [ ] Load configuration on server startup
- [ ] Validate MCP_OUTPUT_DIR environment variable
- [ ] Handle missing configuration gracefully
- [ ] Log configuration status

**Files Modified**:
- `server/src/__main__.py` or server entry point

**Technical Implementation**:
```python
# Server startup
from src.utils.output_config import OutputConfig

try:
    config = OutputConfig()
    logger.info(f"Output configuration loaded: {config.MCP_OUTPUT_DIR}")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    # Continue with defaults or exit based on severity
```

---

#### AVB-809: Validate MCP_OUTPUT_DIR Existence (1 pt)
**Tasks**:
- [ ] Check if MCP_OUTPUT_DIR path exists
- [ ] Check if path is writable
- [ ] Log validation results
- [ ] Handle validation failures appropriately

---

#### AVB-810: Create Default Project Folder (1 pt)
**Tasks**:
- [ ] Create "default" project folder if configured
- [ ] Apply proper permissions
- [ ] Log folder creation
- [ ] Handle creation failures

---

#### AVB-811: Add Startup Validation Logging (1 pt)
**Tasks**:
- [ ] Log all startup validation steps
- [ ] Include configuration values (sanitized)
- [ ] Log validation success/failure
- [ ] Add structured logging for monitoring

---

#### AVB-812: Write Server Startup Tests (1 pt)
**Tasks**:
- [ ] Test server starts with valid config
- [ ] Test server handles invalid MCP_OUTPUT_DIR
- [ ] Test server handles missing config
- [ ] Test default project folder creation

**Files Created**:
- `server/tests/test_server_startup.py`

---

#### AVB-813: Document Configuration Requirements (1 pt)
**Tasks**:
- [ ] Update README with configuration instructions
- [ ] Document all environment variables
- [ ] Provide configuration examples
- [ ] Add troubleshooting section

**Files Modified**:
- `README.md`
- `server/.env.example`

---

### Epic 3.2.1: Unit Testing (10 points, AVB-901 to AVB-907)

**Objective**: Comprehensive unit testing for all Sprint 1 components

#### AVB-901: Unit Tests for OutputConfig (1 pt)
**Note**: Sprint 1 already has 184+ tests with ≥90% coverage. This epic is about verifying coverage is complete.

**Tasks**:
- [ ] Review existing OutputConfig tests
- [ ] Add any missing edge case tests
- [ ] Verify all environment variable combinations tested

---

#### AVB-902: Unit Tests for Security Validation (2 pts)
**Tasks**:
- [ ] Review existing security tests
- [ ] Add path traversal attack tests
- [ ] Add filename sanitization tests
- [ ] Test permission validation

---

#### AVB-903: Unit Tests for OutputHandler (2 pts)
**Tasks**:
- [ ] Review existing OutputHandler tests
- [ ] Add async I/O tests
- [ ] Add streaming tests
- [ ] Test error handling

---

#### AVB-904: Unit Tests for TokenEstimator (2 pts)
**Tasks**:
- [ ] Review existing TokenEstimator tests
- [ ] Test tiktoken integration
- [ ] Test various content types (CSV, JSON)
- [ ] Test large content handling

---

#### AVB-905: Unit Tests for Project Management (1 pt)
**Tasks**:
- [ ] Test project folder creation
- [ ] Test project folder validation
- [ ] Test permission handling

---

#### AVB-906: Measure and Report Code Coverage (1 pt)
**Tasks**:
- [ ] Run pytest with coverage
- [ ] Generate HTML coverage report
- [ ] Identify coverage gaps
- [ ] Document coverage metrics

**Command**:
```bash
pytest --cov=src --cov-report=html --cov-report=term
```

---

#### AVB-907: Fix Coverage Gaps to ≥85% (1 pt)
**Tasks**:
- [ ] Add tests for uncovered lines
- [ ] Test error paths
- [ ] Test edge cases
- [ ] Achieve ≥85% coverage

---

### Epic 3.2.2: Integration Testing (10 points, AVB-908 to AVB-914)

**Objective**: End-to-end integration testing

#### AVB-908: Integration Tests for Time Series (2 pts)
**Tasks**:
- [ ] Test GET_TIME_SERIES with real API
- [ ] Test all 8 series types
- [ ] Test inline vs file output
- [ ] Test with large datasets

---

#### AVB-909: Integration Tests for Technical Indicators (2 pts)
**Tasks**:
- [ ] Test all 6 technical indicator tools
- [ ] Test multiple indicators per tool
- [ ] Test output helper integration
- [ ] Verify file creation

---

#### AVB-910: Integration Tests for Fundamental Data (2 pts)
**Tasks**:
- [ ] Test GET_FINANCIAL_STATEMENTS
- [ ] Test GET_COMPANY_DATA
- [ ] Test GET_MARKET_DATA
- [ ] Test GET_ECONOMIC_INDICATOR
- [ ] Test commodity tools

---

#### AVB-911: Integration Tests for Project Folders (1 pt)
**Tasks**:
- [ ] Test project folder creation
- [ ] Test folder structure
- [ ] Test permission handling
- [ ] Test cleanup

---

#### AVB-913: Performance Tests for Large Datasets (2 pts)
**Tasks**:
- [ ] Test 1MB dataset handling
- [ ] Test 5MB dataset handling
- [ ] Test 10MB dataset handling
- [ ] Measure response times
- [ ] Verify <2s target for 10MB

**Performance Goals**:
- 1MB: <500ms
- 5MB: <1s
- 10MB: <2s

---

#### AVB-914: Memory Usage Tests with Streaming (1 pt)
**Tasks**:
- [ ] Test memory usage with large files
- [ ] Verify streaming reduces memory
- [ ] Test concurrent requests
- [ ] Measure memory footprint

**Memory Goals**:
- Single 10MB file: <50MB RAM
- 10 concurrent requests: <200MB RAM

---

## Implementation Strategy

### Week 1: Output Helper Integration (23 points)
**Day 1-2**: Epic 3.1.1 Tasks 1-3
- AVB-801: Audit (2 pts)
- AVB-802: Time series integration (2 pts)
- AVB-803: Technical indicators integration (3 pts)

**Day 3-4**: Epic 3.1.1 Tasks 4-7
- AVB-804: Fundamental/economic integration (3 pts)
- AVB-805: Commodity/market integration (2 pts)
- AVB-806: Verify consistency (1 pt)
- AVB-807: Smoke tests (2 pts)

**Day 5**: Epic 3.1.2 - Server Integration
- AVB-808 to AVB-813: Server startup integration (7 pts)

---

### Week 2: Testing & Quality (17 points)
**Day 1-3**: Epic 3.2.1 - Unit Testing
- AVB-901 to AVB-907: Unit testing (10 pts)

**Day 4-5**: Epic 3.2.2 - Integration Testing
- AVB-908 to AVB-914: Integration testing (10 pts)

---

## Technical Architecture

### Output Helper Integration Pattern

**Current Pattern (Sprint 2/3)**:
```python
@tool()
async def GET_TOOL(..., force_inline: bool = False, force_file: bool = False):
    request = ToolRequest(...)
    api_function, params = route_request(request)
    return await _make_api_request(api_function, params)
    # ⚠️ force_inline/force_file are ignored!
```

**Target Pattern (Sprint 4)**:
```python
from src.integration.helpers import should_use_output_helper, create_file_response, create_inline_response

@tool()
async def GET_TOOL(..., force_inline: bool = False, force_file: bool = False):
    request = ToolRequest(...)
    api_function, params = route_request(request)

    # Make API request
    response_data = await _make_api_request(api_function, params)

    # Intelligent output decision
    if should_use_output_helper(response_data, request.force_inline, request.force_file):
        # Save to file and return file reference
        return await create_file_response(
            data=response_data,
            project_name=request.project_name or "default",
            filename=f"{api_function}_{request.symbol}_{timestamp}.{ext}"
        )
    else:
        # Return inline data
        return create_inline_response(response_data)
```

---

## Success Metrics

### Code Quality
- [ ] ≥85% test coverage across all modules
- [ ] 100% ruff compliance
- [ ] 100% black formatting
- [ ] All integration tests passing
- [ ] Zero TODO/FIXME in production code

### Performance
- [ ] <2s response time for 10MB datasets
- [ ] <50MB memory usage per request
- [ ] Streaming reduces memory by ≥50%

### Functionality
- [ ] All 15 tools use output helper
- [ ] `force_inline` parameter works
- [ ] `force_file` parameter works
- [ ] Automatic threshold detection works
- [ ] Project folders created correctly

---

## Risk Assessment

### High Risk
**Risk**: Integration breaks existing tool behavior
**Mitigation**:
- Comprehensive smoke tests before integration
- Backward compatibility tests
- Incremental rollout (1 tool at a time)

### Medium Risk
**Risk**: Performance degradation from output helper overhead
**Mitigation**:
- Performance benchmarks before/after
- Optimize hot paths
- Use async I/O throughout

### Low Risk
**Risk**: Configuration errors on startup
**Mitigation**:
- Clear error messages
- Graceful degradation
- Comprehensive startup logging

---

## Dependencies

### Internal
- ✅ Sprint 1 output helper infrastructure (complete)
- ✅ Sprint 2 tool consolidation (complete)
- ✅ Sprint 3 tool consolidation (complete)

### External
- Alpha Vantage API availability
- R2 storage (for large files)
- Environment configuration (MCP_OUTPUT_DIR)

---

## Deliverables

### Code
- [ ] 15 unified tools integrated with output helper
- [ ] Updated `_make_api_request()` function
- [ ] Server startup validation
- [ ] Comprehensive test suite (≥85% coverage)

### Documentation
- [ ] Configuration guide
- [ ] Integration pattern documentation
- [ ] Troubleshooting guide
- [ ] API reference updates

### Reports
- [ ] Integration audit report
- [ ] Test coverage report
- [ ] Performance benchmark report
- [ ] Sprint 4 completion report

---

## Sprint 4 Completion Criteria

Sprint 4 is complete when:
1. ✅ All 15 tools integrated with output helper
2. ✅ `force_inline`/`force_file` parameters functional
3. ✅ Server validates configuration on startup
4. ✅ ≥85% test coverage achieved
5. ✅ All integration tests passing
6. ✅ Performance goals met (<2s for 10MB)
7. ✅ Documentation complete
8. ✅ Sprint 4 completion report delivered

---

**Status**: Ready to begin
**Approved by**: (Pending approval)
**Start Date**: (TBD)
**Target Completion**: 2 weeks from start
