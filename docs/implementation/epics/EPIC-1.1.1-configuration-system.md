# EPIC-1.1.1: Configuration System

**Epic ID:** EPIC-1.1.1  
**Jira Epic:** AVB-1.1.1  
**Phase:** 1 - Output Helper System  
**Milestone:** 1.1 - Foundation Setup  
**Story Points:** 7  
**Priority:** P0 (Critical)

---

## Epic Summary

Create a Pydantic-based configuration management system that loads, validates, and manages all output helper configuration from environment variables. This is the foundation for all file output functionality.

## Business Value

**Why this matters:**
- Enables users to configure output behavior without code changes
- Prevents misconfiguration through validation
- Provides clear error messages when setup is incorrect
- Essential foundation for all subsequent output helper features

**User Impact:**
- Users can customize output behavior for their workflow
- Clear feedback when configuration is invalid
- Secure by default with path validation

---

## Technical Scope

### Components to Build
1. `OutputConfig` Pydantic model (12 configuration fields)
2. Environment variable loading helpers
3. Configuration validation logic
4. `.env.example` template
5. Unit test suite

### Key Technologies
- Pydantic 2.0+ for configuration validation
- python-dotenv for env file loading
- pathlib for path handling

---

## Issues in this Epic

### AVB-101: Design OutputConfig Pydantic Model
**Type:** Story  
**Priority:** P0  
**Story Points:** 2

**Description:**
Create the core OutputConfig class with all 12 configuration fields defined, typed, and documented.

**Acceptance Criteria:**
- [ ] All 12 fields defined with proper types
- [ ] Field descriptions provided
- [ ] Default values specified
- [ ] Pydantic model validates on instantiation

**Implementation Notes:**
- Use Field() with description parameter for documentation
- Use default_factory for environment variable loading
- Include validators for critical fields

---

### AVB-102: Implement Environment Variable Loading
**Type:** Story  
**Priority:** P0  
**Story Points:** 1

**Description:**
Add helper functions for loading and parsing environment variables with type coercion.

**Acceptance Criteria:**
- [ ] get_env_bool() works for all boolean formats
- [ ] get_env_int() validates integer parsing
- [ ] load_output_config() creates valid OutputConfig
- [ ] Helpful errors on invalid values

**Implementation Notes:**
- Support common boolean formats: "true", "false", "1", "0", "yes", "no"
- Provide context in error messages (which env var failed, why)

---

### AVB-103: Add Configuration Validation
**Type:** Story  
**Priority:** P0  
**Story Points:** 2

**Description:**
Implement Pydantic validators for critical configuration fields.

**Acceptance Criteria:**
- [ ] client_root validated (absolute, exists, writable)
- [ ] Thresholds validated (reasonable ranges)
- [ ] Chunk size validated (reasonable bounds)
- [ ] Clear error messages on validation failure

**Implementation Notes:**
- Use @validator decorator
- Test write permissions with temporary file
- Provide suggestions in error messages

---

### AVB-104: Create .env.example
**Type:** Story  
**Priority:** P1  
**Story Points:** 1

**Description:**
Create comprehensive .env.example file with all configuration variables documented.

**Acceptance Criteria:**
- [ ] All 12 variables listed
- [ ] Each variable has comment explaining purpose
- [ ] Example values provided
- [ ] Required vs optional clearly marked

**Template Structure:**
```bash
# Required: Root directory for output files
MCP_OUTPUT_DIR=/path/to/outputs

# Optional: Project organization (default: default)
MCP_PROJECT_NAME=my_project
...
```

---

### AVB-105: Write Unit Tests
**Type:** Task  
**Priority:** P0  
**Story Points:** 1

**Description:**
Create comprehensive unit test suite for configuration loading and validation.

**Acceptance Criteria:**
- [ ] Test valid configuration loading
- [ ] Test each validator (success and failure cases)
- [ ] Test environment variable parsing
- [ ] Test error messages are helpful
- [ ] ≥90% code coverage for configuration module

**Test Cases:**
- Valid configuration
- Missing MCP_OUTPUT_DIR
- Non-absolute client_root path
- Non-writable client_root directory
- Invalid threshold values
- Invalid chunk size
- Invalid boolean/int parsing

---

## Epic Dependencies

**Blocks:**
- All other Phase 1 work (nothing works without configuration)

**Depends On:**
- None (this is the starting point)

---

## Definition of Done

- [ ] All 5 issues completed and tested
- [ ] Code reviewed and approved
- [ ] Unit tests passing with ≥90% coverage
- [ ] Documentation updated
- [ ] .env.example created and reviewed
- [ ] Configuration can be loaded successfully
- [ ] Validation catches all invalid configurations

---

## Testing Strategy

### Unit Tests
- Configuration model instantiation
- Validator logic for all fields
- Environment variable parsing
- Error message clarity

### Integration Tests
- Load configuration from actual .env file
- Validate with invalid paths
- Test with missing required variables

### Manual Testing
- Create .env file and load configuration
- Verify validation catches misconfigurations
- Test error messages are helpful

---

## Documentation Requirements

- [ ] Inline docstrings for all classes and methods
- [ ] `.env.example` with comprehensive comments
- [ ] README section on configuration
- [ ] Troubleshooting guide for common config errors

---

## Risks & Mitigation

**Risk:** Path validation too strict, blocks legitimate use cases
- **Mitigation:** Test with various path formats, allow absolute paths within client_root

**Risk:** Error messages too technical for users
- **Mitigation:** Include examples and suggestions in error messages

---

## Notes

- This epic is foundational - take time to get it right
- Configuration pattern will be reused in other components
- Security validation is critical - don't skip testing

---

**Epic Owner:** Lead Developer  
**Reviewer:** Security Reviewer  
**Created:** 2025-10-16  
**Target Sprint:** Sprint 1
