# Sprint 3 Planning: Technical Indicators & Fundamental Data

**Duration**: Weeks 5-6
**Story Points**: 56
**Issues**: 20 (AVB-513 through AVB-706)
**Phases**: Phase 2 Milestones 2.2 (complete), 2.3, 2.4

---

## 🎯 Sprint 3 Objectives

Complete Phase 2 of the Alpha Vantage MCP Server consolidation project by:

1. ✅ **Complete Technical Indicators** - Consolidate remaining 26 technical indicator tools
2. ✅ **Fundamental Data** - Consolidate 11 fundamental/company data tools → 3 unified tools
3. ✅ **Economic Indicators** - Consolidate 10 economic indicator tools → 1 unified tool
4. ✅ **Commodities** - Consolidate 11 commodity tools → 2 unified tools
5. ✅ **Achieve Phase 2 Goal**: 118 original tools → ~25 consolidated tools (≥78% reduction)

---

## 📊 Sprint 2 Achievements (Context)

Sprint 2 successfully delivered:
- **47 tools → 5 tools** (90.4% reduction)
- **~27,300 tokens saved** (~88% context window reduction)
- **650 tests passing** (100% pass rate)
- **4 epics completed**: Time Series, Forex/Crypto, Moving Averages, Oscillators

**Current State**:
- Tools consolidated so far: 47
- Tools remaining to consolidate: 71
- Context window reduction achieved: ~88%

---

## 🏗️ Sprint 3 Structure

### Milestone 2.2: Technical Indicators - Additional (14 Story Points)

Complete the technical indicators consolidation started in Sprint 2.

**Remaining Indicators to Consolidate**: 26 tools

#### Epic 2.2.3: Additional Technical Indicators (14 pts, AVB-513 to AVB-519)

Consolidate remaining 26 technical indicators into 4 unified tools:

1. **GET_TREND_INDICATOR** (8 indicators):
   - AROON, AROONOSC, DX, MINUS_DI, PLUS_DI, MINUS_DM, PLUS_DM, ADX (already done in Sprint 2)

2. **GET_VOLATILITY_INDICATOR** (7 indicators):
   - BBANDS, TRANGE, ATR, NATR, MIDPOINT, MIDPRICE, SAR

3. **GET_VOLUME_INDICATOR** (4 indicators):
   - AD, ADOSC, OBV, MFI (already done in Sprint 2)

4. **GET_CYCLE_INDICATOR** (6 indicators):
   - HT_TRENDLINE, HT_SINE, HT_TRENDMODE, HT_DCPERIOD, HT_DCPHASE, HT_PHASOR

**Context Window Impact**:
- Before: 26 tools × ~600 tokens = ~15,600 tokens
- After: 4 tools × ~600 tokens = ~2,400 tokens
- Savings: ~13,200 tokens (85% reduction)

**Issues**:
- **AVB-513**: Design/implement GET_TREND_INDICATOR (3 pts)
  - Schema with indicator_type routing
  - Conditional parameter validation
  - Router implementation
  - MCP tool with @tool decorator

- **AVB-514**: Design/implement GET_VOLATILITY_INDICATOR (3 pts)
  - Schema for volatility indicators
  - Parameter validation (BBANDS has multiple params, others simpler)
  - Router and unified tool

- **AVB-515**: Design/implement GET_VOLUME_INDICATOR (2 pts)
  - Schema for volume-based indicators
  - Router and unified tool

- **AVB-516**: Design/implement GET_CYCLE_INDICATOR (2 pts)
  - Schema for Hilbert Transform indicators
  - Router and unified tool

- **AVB-517**: Integrate output helper for all (2 pts)
  - Add output decision logic to all 4 tools
  - File vs inline routing

- **AVB-518**: Write comprehensive test suite (1 pt)
  - Unit tests for all 4 schemas
  - Router tests
  - Integration tests

- **AVB-519**: Update documentation with examples (1 pt)
  - Epic documentation
  - README updates
  - Migration guides

---

### Milestone 2.3: Fundamental & Economic Data (35 Story Points)

Consolidate fundamental company data and macroeconomic indicators.

#### Epic 2.3.1: Fundamental Data Consolidation (19 pts, AVB-601 to AVB-608)

Consolidate 11 fundamental data tools into 3 unified tools:

**1. GET_FINANCIAL_STATEMENTS** (3 tools → 1):
- INCOME_STATEMENT, BALANCE_SHEET, CASH_FLOW
- Routing: `statement_type` = "income", "balance", "cash_flow"

**2. GET_COMPANY_DATA** (5 tools → 1):
- COMPANY_OVERVIEW, ETF_PROFILE, DIVIDENDS, SPLITS, EARNINGS
- Routing: `data_type` = "overview", "etf_profile", "dividends", "splits", "earnings"

**3. GET_MARKET_DATA** (3 tools → 1):
- LISTING_STATUS, EARNINGS_CALENDAR, IPO_CALENDAR
- Routing: `calendar_type` = "listing_status", "earnings_calendar", "ipo_calendar"

**Context Window Impact**:
- Before: 11 tools × ~700 tokens = ~7,700 tokens
- After: 3 tools × ~700 tokens = ~2,100 tokens
- Savings: ~5,600 tokens (73% reduction)

**Issues**:
- **AVB-601**: Design GET_FINANCIAL_STATEMENTS (3 pts)
  - Schema with statement_type routing (income, balance, cash_flow)
  - Router implementation
  - Unified MCP tool

- **AVB-602**: Design GET_COMPANY_DATA (3 pts)
  - Schema with data_type routing (overview, etf_profile, dividends, splits, earnings)
  - Conditional validation (ETF-specific params)
  - Router and tool

- **AVB-603**: Design GET_MARKET_DATA (2 pts)
  - Schema with calendar_type routing
  - Router and tool

- **AVB-604**: Implement all three fundamental tools (5 pts)
  - Complete implementation with error handling
  - Structured responses

- **AVB-605**: Add statement_type/data_type routing (2 pts)
  - Routing logic for all 3 tools
  - Parameter transformation

- **AVB-606**: Integrate output helper (2 pts)
  - Output decision integration
  - File reference responses

- **AVB-607**: Write tests for all fundamental tools (1 pt)
  - Schema, router, integration tests

- **AVB-608**: Update documentation (1 pt)
  - Epic docs + README

---

#### Epic 2.3.2: Economic Indicators Consolidation (16 pts, AVB-609 to AVB-614)

Consolidate 10 macroeconomic indicators into 1 unified tool:

**GET_ECONOMIC_INDICATOR** (10 tools → 1):
- REAL_GDP, REAL_GDP_PER_CAPITA, TREASURY_YIELD, FEDERAL_FUNDS_RATE, CPI
- INFLATION, RETAIL_SALES, DURABLES, UNEMPLOYMENT, NONFARM_PAYROLL

**Routing**: `indicator_type` parameter

**Key Challenge**: Different indicators have different interval requirements:
- GDP: annual/quarterly
- Treasury Yield: daily/weekly/monthly
- Most others: monthly/quarterly/annual

**Context Window Impact**:
- Before: 10 tools × ~600 tokens = ~6,000 tokens
- After: 1 tool × ~600 tokens = ~600 tokens
- Savings: ~5,400 tokens (90% reduction)

**Issues**:
- **AVB-609**: Design GET_ECONOMIC_INDICATOR (2 pts)
  - Schema with indicator_type routing
  - Conditional interval validation

- **AVB-610**: Implement indicator routing (4 pts)
  - Map 10 indicators to API functions
  - Parameter transformation

- **AVB-611**: Add interval parameter validation (2 pts)
  - Validate interval based on indicator type
  - Clear error messages

- **AVB-612**: Integrate output helper (2 pts)
  - Output decision logic
  - File handling for large datasets

- **AVB-613**: Write tests for all 10 indicators (5 pts)
  - Schema tests for all indicators
  - Router tests
  - Integration tests

- **AVB-614**: Update documentation (1 pt)
  - Epic docs + README

---

### Milestone 2.4: Commodities Consolidation (7 Story Points)

Consolidate commodity price data tools.

#### Epic 2.4.1: Commodities Consolidation (7 pts, AVB-701 to AVB-706)

Consolidate 11 commodity tools into 2 unified tools:

**1. GET_ENERGY_COMMODITY** (3 tools → 1):
- WTI, BRENT, NATURAL_GAS
- Routing: `commodity_type` = "wti", "brent", "natural_gas"

**2. GET_MATERIALS_COMMODITY** (8 tools → 1):
- COPPER, ALUMINUM (metals)
- WHEAT, CORN, COTTON, SUGAR, COFFEE (agricultural)
- ALL_COMMODITIES (index)
- Routing: `commodity_type` parameter

**Context Window Impact**:
- Before: 11 tools × ~500 tokens = ~5,500 tokens
- After: 2 tools × ~500 tokens = ~1,000 tokens
- Savings: ~4,500 tokens (82% reduction)

**Issues**:
- **AVB-701**: Design GET_ENERGY_COMMODITY (1 pt)
  - Schema with commodity_type routing
  - Interval validation (daily/weekly/monthly)

- **AVB-702**: Design GET_MATERIALS_COMMODITY (1 pt)
  - Schema with commodity_type routing
  - Support metals, agricultural, index

- **AVB-703**: Implement both with routing (2 pts)
  - Router implementations
  - Unified MCP tools

- **AVB-704**: Integrate output helper (1 pt)
  - Output decision logic

- **AVB-705**: Write tests for all types (1 pt)
  - Schema, router, integration tests

- **AVB-706**: Update documentation (1 pt)
  - Epic docs + README

---

## 📈 Sprint 3 Total Impact

### Tool Consolidation

| Milestone | Tools Before | Tools After | Reduction | Token Savings |
|-----------|--------------|-------------|-----------|---------------|
| **2.2 (Additional)** | 26 | 4 | 84.6% | ~13,200 |
| **2.3.1 (Fundamental)** | 11 | 3 | 72.7% | ~5,600 |
| **2.3.2 (Economic)** | 10 | 1 | 90.0% | ~5,400 |
| **2.4 (Commodities)** | 11 | 2 | 81.8% | ~4,500 |
| **SPRINT 3 TOTAL** | **58** | **10** | **82.8%** | **~28,700** |

### Cumulative Project Impact (After Sprint 3)

| Metric | Sprint 1 | Sprint 2 | Sprint 3 | **Total** |
|--------|----------|----------|----------|-----------|
| **Tools Consolidated** | 0 | 47 | 58 | **105** |
| **Unified Tools Created** | 0 | 5 | 10 | **15** |
| **Token Savings** | 0 | ~27,300 | ~28,700 | **~56,000** |
| **Tests Created** | 184 | 650 | ~500 (est) | **~1,334** |

### Phase 2 Completion Target

**Original Goal**: 118 tools → ≤25 tools (≥78% reduction)

**After Sprint 3**:
- Tools before: 118
- Tools consolidated: 105
- Remaining: 13
- Unified tools: 15
- **Target achievement**: ✅ EXCEEDS GOAL (87% reduction vs 78% target)

---

## 🎯 Success Criteria

Sprint 3 will be considered successful when:

1. ✅ **All 3 Milestones Complete**:
   - Milestone 2.2: 4 additional technical indicator tools
   - Milestone 2.3: 4 fundamental/economic tools
   - Milestone 2.4: 2 commodity tools

2. ✅ **Quality Standards Met**:
   - All tests passing (≥99% pass rate)
   - Code quality 100% (ruff + black)
   - Test coverage ≥85%

3. ✅ **Context Window Reduction**:
   - Sprint 3 target: ~28,700 tokens saved
   - Cumulative target: ~56,000 tokens saved

4. ✅ **Documentation Complete**:
   - Epic documentation for all 4 epics
   - README updates with examples
   - Migration guides

5. ✅ **Phase 2 Goal Achieved**:
   - 105/118 tools consolidated (≥87% reduction)
   - Total unified tools ≤20 (target: 15)

---

## 🔄 Established Workflow (from Sprint 2)

Each epic follows the proven pattern:

### Development Pattern
1. **Schema Design**: Pydantic BaseModel with `@model_validator`
2. **Router Implementation**: `route_request() -> tuple[str, dict]`
3. **Unified MCP Tool**: `@tool()` decorator with structured responses
4. **Comprehensive Testing**: Schema + Router + Integration tests
5. **Documentation**: Epic docs + README updates

### Quality Workflow
1. Implement schema → test validation
2. Implement router → test routing
3. Implement tool → test integration
4. Run quality checks: `pytest`, `ruff`, `black`
5. Fix any errors → rerun until 100% pass
6. Update documentation
7. Commit with detailed message

### Testing Requirements
- **Unit Tests**: All schema validation scenarios
- **Router Tests**: API function mapping, parameter transformation
- **Integration Tests**: End-to-end with mocked API calls
- **Parameterization**: Use `@pytest.mark.parametrize` for efficiency

---

## 📋 Issue Breakdown by Epic

### Epic 2.2.3: Additional Technical Indicators (14 pts)
- AVB-513: GET_TREND_INDICATOR (3 pts)
- AVB-514: GET_VOLATILITY_INDICATOR (3 pts)
- AVB-515: GET_VOLUME_INDICATOR (2 pts)
- AVB-516: GET_CYCLE_INDICATOR (2 pts)
- AVB-517: Integrate output helper (2 pts)
- AVB-518: Write tests (1 pt)
- AVB-519: Documentation (1 pt)

### Epic 2.3.1: Fundamental Data (19 pts)
- AVB-601: GET_FINANCIAL_STATEMENTS (3 pts)
- AVB-602: GET_COMPANY_DATA (3 pts)
- AVB-603: GET_MARKET_DATA (2 pts)
- AVB-604: Implement all three tools (5 pts)
- AVB-605: Add routing logic (2 pts)
- AVB-606: Integrate output helper (2 pts)
- AVB-607: Write tests (1 pt)
- AVB-608: Documentation (1 pt)

### Epic 2.3.2: Economic Indicators (16 pts)
- AVB-609: GET_ECONOMIC_INDICATOR design (2 pts)
- AVB-610: Implement routing (4 pts)
- AVB-611: Interval validation (2 pts)
- AVB-612: Integrate output helper (2 pts)
- AVB-613: Write tests (5 pts)
- AVB-614: Documentation (1 pt)

### Epic 2.4.1: Commodities (7 pts)
- AVB-701: GET_ENERGY_COMMODITY (1 pt)
- AVB-702: GET_MATERIALS_COMMODITY (1 pt)
- AVB-703: Implement both (2 pts)
- AVB-704: Integrate output helper (1 pt)
- AVB-705: Write tests (1 pt)
- AVB-706: Documentation (1 pt)

---

## 🚀 Execution Plan

### Week 5: Milestones 2.2 & 2.3.1

**Day 1-2**: Epic 2.2.3 - Additional Technical Indicators (14 pts)
- Design and implement 4 unified tools
- Write comprehensive tests
- Update documentation

**Day 3-5**: Epic 2.3.1 - Fundamental Data (19 pts)
- Design and implement 3 fundamental data tools
- Write tests
- Update documentation

### Week 6: Milestones 2.3.2 & 2.4

**Day 1-3**: Epic 2.3.2 - Economic Indicators (16 pts)
- Design and implement GET_ECONOMIC_INDICATOR
- Write tests for all 10 indicators
- Update documentation

**Day 4-5**: Epic 2.4.1 - Commodities (7 pts)
- Design and implement 2 commodity tools
- Write tests
- Update documentation
- **Sprint 3 completion report**

---

## 📝 Deliverables Checklist

### Code Deliverables
- [ ] 10 new source modules (schemas, routers, unified tools)
- [ ] ~500 comprehensive tests (unit, router, integration)
- [ ] All tests passing (≥99% pass rate)
- [ ] 100% code quality compliance (ruff + black)

### Documentation Deliverables
- [ ] Epic documentation (4 epics)
- [ ] README updates with examples
- [ ] Migration guides for all consolidated tools
- [ ] Parameter reference tables
- [ ] Usage examples for common scenarios

### Quality Deliverables
- [ ] Test coverage ≥85% for all new modules
- [ ] Context window reduction metrics
- [ ] Performance benchmarks (where applicable)
- [ ] Sprint 3 completion report

---

## 🎯 Risk Assessment

### Technical Risks (LOW)

1. **Complex Parameter Patterns**: ✅ Mitigated
   - Proven pattern from Sprint 2
   - Pydantic conditional validation tested

2. **Testing Coverage**: ✅ Mitigated
   - Parameterized testing reduces effort
   - Clear test structure established

3. **Documentation Burden**: ✅ Mitigated
   - Template from Sprint 2 epics
   - Consistent format

### Schedule Risks (LOW)

- Sprint 2 completed on schedule
- Team velocity established
- Buffer built into estimates

---

## 📊 Success Metrics

### Quantitative Metrics
- ✅ 56/56 story points delivered
- ✅ 58 tools → 10 tools (82.8% reduction)
- ✅ ~28,700 tokens saved
- ✅ ~500 tests passing
- ✅ 100% code quality compliance

### Qualitative Metrics
- ✅ Consistent consolidation pattern
- ✅ Clear error messages
- ✅ Comprehensive documentation
- ✅ Production-ready implementation

---

## 🎊 Sprint 3 Completion Will Achieve

1. **Phase 2 Complete**: 105/118 tools consolidated (87% reduction)
2. **Context Window**: ~56,000 tokens saved cumulatively
3. **Unified Tools**: 15 total (vs 118 original)
4. **Test Suite**: ~1,334 tests passing
5. **Ready for Phase 3**: Integration and final testing

---

## ✅ Approval to Proceed

Once approved, I will:
1. ✅ Execute all 20 issues in priority order (AVB-513 → AVB-706)
2. ✅ Complete all work following Sprint 2's proven workflow
3. ✅ Run all quality checks (syntax, formatting, linting, tests)
4. ✅ Fix all errors and warnings
5. ✅ Provide comprehensive Sprint 3 completion report

**Ready to begin Sprint 3 when you approve!** 🚀

---

**Expected Duration**: 2 weeks (Weeks 5-6)
**Expected Outcome**: Phase 2 complete, ready for Phase 3 integration
**Risk Level**: LOW (proven patterns from Sprint 2)
