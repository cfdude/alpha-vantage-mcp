# Development Workflow

## Quality-First Development Process

This document defines the mandatory development workflow for all Sprint work on the Alpha Vantage MCP Server redesign project.

---

## 🎯 Core Principle

**NOTHING is "done" until ALL tests pass.** Use accurate status descriptions:
- "Draft implementation" or "Done but not tested" for untested code
- "Ready for testing" when code is complete but tests haven't run
- "Tests passing" only when verified
- Never use "complete," "ready," or "production-ready" until fully tested

---

## 📋 Development Workflow (Per Issue)

### 1. Development Phase
- **Delegate to sub-agent** for implementation work
- Sub-agent implements the feature/fix according to issue specifications
- Sub-agent creates/updates tests as needed

### 2. Initial Quality Check (Mandatory After Development)
Run all quality checks in this order:

```bash
# Syntax check
python -m py_compile <modified_files>

# Formatting check
black --check <modified_files>

# Linting check
ruff check <modified_files>

# Run all tests
pytest
```

### 3. Error Fixing Protocol
**CRITICAL:** Fix ALL errors, even if not introduced by current work

- **Errors:** MUST be fixed immediately
  - Syntax errors
  - Import errors
  - Test failures
  - Linting errors (not warnings)

- **Warnings:** Can be ignored (document if relevant)

- **Regression Detection:**
  - If errors exist that weren't caused by current development, FIX THEM
  - This catches regressions early
  - Never skip errors with "not my problem" mentality

### 4. Retest After Fixes
After fixing any errors:
```bash
# Rerun all quality checks
black --check <modified_files>
ruff check <modified_files>
pytest
```

Repeat steps 3-4 until ALL errors are resolved.

### 5. Mark Issue Complete
Only after all tests pass:
- Update progress.md with issue completion
- Update todo.md to mark issue done
- Commit changes with conventional commit message

---

## 🚀 End-of-Sprint Process

### 1. Full Regression Test Suite
Run complete test suite across entire sprint's work:

```bash
# Full formatting check
black --check server/

# Full linting check
ruff check server/

# Full test suite
pytest --verbose

# Coverage report (optional but recommended)
pytest --cov=server --cov-report=term-missing
```

### 2. Fix Any Regressions Found
If regression tests reveal issues:
- Stop and fix ALL errors
- Rerun full test suite
- Repeat until clean

### 3. Sprint Summary Report
Create sprint summary including:

**Work Completed:**
- List all issues completed (AVB-XXX)
- Story points completed vs planned
- Key features delivered
- Test coverage metrics

**Issues Encountered:**
- Technical blockers
- Unexpected complexity
- Dependencies discovered
- Time estimate accuracy

**Recommendations for Next Sprint:**
- Process improvements
- Technical debt to address
- Dependency changes needed
- Story point estimation adjustments

### 4. Sprint Retrospective
Discuss:
- What went well?
- What could be improved?
- What should we change for next sprint?
- Any scope adjustments needed?

### 5. Next Sprint Planning
- Review next sprint from sprint-planning.md
- Adjust story points based on velocity from completed sprint
- Confirm priorities and dependencies
- Create sprint backlog

---

## 🛠️ Tools & Commands Reference

### Quality Check Commands
```bash
# Python syntax check
python -m py_compile <file>.py

# Format code (auto-fix)
black <file>.py

# Check formatting only (no changes)
black --check <file>.py

# Lint with auto-fix
ruff check --fix <file>.py

# Lint without fixes
ruff check <file>.py

# Run specific test file
pytest tests/test_<module>.py

# Run all tests
pytest

# Run tests with coverage
pytest --cov=server --cov-report=html
```

### Git Commit Convention
```bash
# Format: <type>(<scope>): <subject>
# Types: feat|fix|docs|style|refactor|test|chore|perf

git commit -m "feat(output): implement OutputConfig Pydantic model"
git commit -m "fix(tools): resolve parameter validation error"
git commit -m "test(output): add OutputHelper integration tests"
```

---

## ✅ Quality Checklist (Per Issue)

Before marking any issue complete:

- [ ] Code implements issue requirements fully
- [ ] All syntax is valid (python -m py_compile passes)
- [ ] Code is formatted (black --check passes)
- [ ] Code passes linting (ruff check passes, no errors)
- [ ] All tests pass (pytest passes)
- [ ] Any existing errors fixed (including regressions)
- [ ] Tests retested after fixes
- [ ] progress.md updated
- [ ] todo.md updated
- [ ] Git commit created with conventional format

---

## ✅ Sprint Completion Checklist

Before closing any sprint:

- [ ] Full regression test suite run
- [ ] All errors fixed (no regressions)
- [ ] Sprint summary report created
- [ ] Issues encountered documented
- [ ] Recommendations for next sprint documented
- [ ] Sprint retrospective completed
- [ ] Next sprint planned
- [ ] All commits pushed to repository
- [ ] Documentation updated (if needed)

---

## 🚫 What NOT To Do

- ❌ **Never** claim something is "done" without running tests
- ❌ **Never** ignore errors "because they existed before"
- ❌ **Never** skip quality checks "to save time"
- ❌ **Never** commit without running tests
- ❌ **Never** leave failing tests "to fix later"
- ❌ **Never** use terms like "production-ready" without evidence

---

## 📞 Questions?

If any step is unclear or if you encounter issues with this workflow:
1. Document the issue
2. Propose workflow improvements
3. Discuss with team before proceeding

**This workflow is mandatory but not immutable** - suggest improvements as you discover better approaches.

---

**Last Updated:** 2025-10-17
**Owner:** Rob Sherman (rob.sherman@highway.ai)
**Status:** Active - Sprint 1 onwards
