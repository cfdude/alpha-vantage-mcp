# Security Architecture - Alpha Vantage MCP Server

## Overview

The Alpha Vantage MCP Server implements a comprehensive security framework to protect against file system attacks and ensure safe handling of user-provided file paths. This document describes the security threat model, validation functions, and best practices for integration.

## Table of Contents

1. [Security Threat Model](#security-threat-model)
2. [Security Functions](#security-functions)
3. [Usage Examples](#usage-examples)
4. [Integration with OutputHandler](#integration-with-outputhandler)
5. [Common Attack Vectors](#common-attack-vectors)
6. [Testing and Validation](#testing-and-validation)
7. [Best Practices](#best-practices)

## Security Threat Model

### What We're Protecting Against

The security framework defends against the following attack vectors:

#### 1. **Directory Traversal Attacks**
- **Threat**: Attackers attempt to access files outside allowed directories using `../` sequences
- **Example**: `../../../etc/passwd` to access system files
- **Protection**: Path containment validation with `Path.resolve()` and `is_relative_to()`

#### 2. **Filename Injection**
- **Threat**: Malicious filenames containing special characters to exploit shell commands or filesystem
- **Example**: `file; rm -rf /` or `file\x00.txt` (null byte injection)
- **Protection**: Comprehensive filename sanitization removing dangerous characters

#### 3. **Symlink Attacks**
- **Threat**: Symbolic links pointing outside allowed directories to access protected files
- **Example**: Creating symlink to `/etc/passwd` within allowed directory
- **Protection**: Path resolution follows symlinks and validates final destination

#### 4. **Permission Escalation**
- **Threat**: Writing files to directories with elevated permissions
- **Example**: Creating files in system directories
- **Protection**: Permission validation before file operations

#### 5. **Reserved Names (Windows)**
- **Threat**: Using Windows reserved device names as filenames
- **Example**: `CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`
- **Protection**: Detection and modification of reserved names

## Security Functions

### 1. `validate_path_contained(path, base_dir)`

**Purpose**: Ensures a path stays within allowed directory boundaries.

**Security Features**:
- Uses `Path.resolve()` to normalize all path components
- Expands symlinks to actual targets
- Validates with `is_relative_to()` for safe containment checking
- Rejects absolute paths outside base directory
- Handles `.` and `..` components correctly

**Function Signature**:
```python
def validate_path_contained(path: Path, base_dir: Path) -> bool:
    """
    Validate that a path is contained within a base directory.

    Args:
        path: The path to validate (relative or absolute)
        base_dir: The base directory that must contain the path

    Returns:
        bool: True if path is safely contained

    Raises:
        SecurityError: If path escapes base_dir boundaries
        ValueError: If base_dir is invalid
    """
```

**Usage Example**:
```python
from pathlib import Path
from src.utils.security import validate_path_contained

base_dir = Path("/var/data")

# Safe path
validate_path_contained(Path("user/file.csv"), base_dir)  # ✓ Returns True

# Attack attempt
validate_path_contained(Path("../etc/passwd"), base_dir)  # ✗ Raises SecurityError
```

### 2. `sanitize_filename(filename)`

**Purpose**: Removes dangerous characters from filenames.

**Security Features**:
- Removes path separators (`/`, `\`)
- Removes shell-dangerous characters (`:`, `*`, `?`, `"`, `<`, `>`, `|`)
- Removes control characters and null bytes
- Removes path traversal sequences (`..`)
- Handles Windows reserved names
- Limits filename length to 255 characters
- Preserves Unicode for international support
- Never returns empty strings (uses "unnamed_file" fallback)

**Function Signature**:
```python
def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing dangerous characters.

    Args:
        filename: The filename to sanitize

    Returns:
        str: Sanitized filename safe for any filesystem
    """
```

**Usage Example**:
```python
from src.utils.security import sanitize_filename

# Safe filename
sanitize_filename("report.csv")  # → "report.csv"

# Attack attempt
sanitize_filename("../etc/passwd")  # → "etcpasswd"
sanitize_filename("file:name?.csv")  # → "filename.csv"
sanitize_filename("CON")  # → "CON_file"

# Unicode preservation
sanitize_filename("日本語ファイル.csv")  # → "日本語ファイル.csv"
```

### 3. `check_directory_permissions(directory)`

**Purpose**: Verifies directory has appropriate read/write permissions.

**Security Features**:
- Uses `os.access()` for permission checking (not try/except)
- Checks both read and write permissions
- Validates parent directory for new directory creation
- Provides actionable error messages with permission codes
- Handles permission errors during existence checks

**Function Signature**:
```python
def check_directory_permissions(directory: Path) -> None:
    """
    Check that a directory has read/write permissions.

    Args:
        directory: The directory path to check

    Raises:
        PermissionError: If directory lacks required permissions
        ValueError: If directory path is invalid
    """
```

**Usage Example**:
```python
from pathlib import Path
from src.utils.security import check_directory_permissions

# Check existing directory
check_directory_permissions(Path("/var/data"))  # ✓ No exception

# Check non-writable directory
check_directory_permissions(Path("/root/protected"))  # ✗ Raises PermissionError
```

### 4. `validate_safe_path(path, base_dir, check_permissions=True)`

**Purpose**: Comprehensive validation combining all security checks.

**Security Features**:
- Sanitizes filename component
- Validates path containment
- Resolves path to handle `..` components
- Checks directory permissions
- Returns validated, resolved path

**Function Signature**:
```python
def validate_safe_path(
    path: Path,
    base_dir: Path,
    check_permissions: bool = True
) -> Path:
    """
    Comprehensive path validation with all security checks.

    Args:
        path: The path to validate
        base_dir: The base directory
        check_permissions: Whether to check permissions

    Returns:
        Path: Validated and sanitized path

    Raises:
        SecurityError: If path fails validation
        PermissionError: If permissions are insufficient
    """
```

**Usage Example**:
```python
from pathlib import Path
from src.utils.security import validate_safe_path

base_dir = Path("/var/data")

# Safe path with sanitization
safe_path = validate_safe_path(Path("user/file:name.csv"), base_dir)
# → PosixPath('/var/data/user/filename.csv')

# Attack blocked
validate_safe_path(Path("../etc/passwd"), base_dir)  # ✗ Raises SecurityError
```

### 5. `log_security_event(event_type, message, path=None)`

**Purpose**: Log security-related events for audit trail.

**Security Features**:
- Centralized logging for security events
- ISO format timestamps
- Logs to stderr (production: integrate with logging system)
- Includes path information when relevant

**Function Signature**:
```python
def log_security_event(
    event_type: str,
    message: str,
    path: Optional[Path] = None
) -> None:
    """
    Log security events for audit trail.

    Args:
        event_type: Type of event (e.g., "path_traversal")
        message: Detailed message
        path: Optional path related to event
    """
```

**Usage Example**:
```python
from pathlib import Path
from src.utils.security import log_security_event

log_security_event(
    "path_traversal",
    "Attempted to access /etc/passwd",
    path=Path("../etc/passwd")
)
# Logs: [2025-10-18T12:00:00+00:00] [SECURITY] path_traversal: Attempted to access /etc/passwd (path: ../etc/passwd)
```

## Usage Examples

### Example 1: Validating User-Provided Filename

```python
from pathlib import Path
from src.utils.security import validate_safe_path

def save_user_file(base_dir: Path, user_filename: str, content: str):
    """Save user-provided file with security validation."""
    try:
        # Validate and sanitize the path
        safe_path = validate_safe_path(
            Path(user_filename),
            base_dir,
            check_permissions=True
        )

        # Create parent directories if needed
        safe_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file safely
        safe_path.write_text(content)

        return safe_path

    except SecurityError as e:
        # Log the security violation
        log_security_event("path_validation_failed", str(e), path=Path(user_filename))
        raise

    except PermissionError as e:
        # Log permission issue
        log_security_event("permission_denied", str(e), path=Path(user_filename))
        raise
```

### Example 2: Multi-Step Validation

```python
from pathlib import Path
from src.utils.security import (
    sanitize_filename,
    validate_path_contained,
    check_directory_permissions
)

def process_user_path(base_dir: Path, user_path: str):
    """Process user path with explicit validation steps."""
    # Step 1: Parse the path
    path = Path(user_path)

    # Step 2: Sanitize the filename
    if path.name:
        sanitized_name = sanitize_filename(path.name)
        path = path.parent / sanitized_name

    # Step 3: Validate containment
    validate_path_contained(path, base_dir)

    # Step 4: Build full path
    full_path = base_dir / path
    resolved_path = full_path.resolve(strict=False)

    # Step 5: Check permissions
    check_directory_permissions(resolved_path.parent)

    return resolved_path
```

### Example 3: Handling Path with .. Components

```python
from pathlib import Path
from src.utils.security import validate_safe_path

base_dir = Path("/var/data")

# Path with .. that stays within base_dir
# "reports/../data/file.csv" resolves to "data/file.csv"
user_path = Path("reports/../data/file.csv")

# Create the target directory
(base_dir / "data").mkdir(parents=True, exist_ok=True)

# Validate - this passes because it resolves within base_dir
safe_path = validate_safe_path(user_path, base_dir)
# → PosixPath('/var/data/data/file.csv')

# Actual traversal attack - this fails
attack_path = Path("../../../etc/passwd")
validate_safe_path(attack_path, base_dir)  # ✗ Raises SecurityError
```

## Integration with OutputHandler

### Recommended Integration Pattern

```python
from pathlib import Path
from src.utils.security import validate_safe_path, SecurityError
from src.utils.output_config import load_output_config

class OutputHandler:
    """Handle output with security validation."""

    def __init__(self):
        self.config = load_output_config()
        self.base_dir = self.config.client_root

    def save_file(self, filename: str, content: str) -> Path:
        """Save file with security validation."""
        try:
            # Validate path (includes sanitization)
            safe_path = validate_safe_path(
                Path(filename),
                self.base_dir,
                check_permissions=True
            )

            # Create parent directories
            safe_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            safe_path.write_text(content)

            return safe_path

        except SecurityError as e:
            # Log and re-raise
            from src.utils.security import log_security_event
            log_security_event("file_save_blocked", str(e), path=Path(filename))
            raise ValueError(f"Security violation: {e}") from e
```

### Key Integration Points

1. **Initialize with base_dir from config**:
   ```python
   self.base_dir = load_output_config().client_root
   ```

2. **Validate ALL user-provided paths**:
   ```python
   safe_path = validate_safe_path(user_path, self.base_dir)
   ```

3. **Handle security exceptions appropriately**:
   ```python
   except SecurityError as e:
       log_security_event("security_violation", str(e), path=user_path)
       raise ValueError(f"Invalid path: {e}") from e
   ```

4. **Create directories AFTER validation**:
   ```python
   safe_path.parent.mkdir(parents=True, exist_ok=True)
   ```

## Common Attack Vectors

### Attack Vector 1: Classic Directory Traversal

**Attack**: `../../../etc/passwd`

**Detection**:
```python
>>> validate_path_contained(Path("../../../etc/passwd"), Path("/var/data"))
SecurityError: Path traversal detected: path escapes base directory
```

**How We Block It**:
- `Path.resolve()` converts to absolute path
- `is_relative_to()` checks if within base_dir
- Raises SecurityError with detailed message

### Attack Vector 2: Null Byte Injection

**Attack**: `file\x00.txt` (attempts to bypass extension checks)

**Detection**:
```python
>>> sanitize_filename("file\x00.txt")
'file.txt'
```

**How We Block It**:
- Null bytes removed in sanitization
- Control characters stripped
- Clean filename returned

### Attack Vector 3: Shell Command Injection

**Attack**: `file; rm -rf /`

**Detection**:
```python
>>> sanitize_filename("file; rm -rf /")
'file rm -rf '
```

**How We Block It**:
- Dangerous characters (`;`, `/`, etc.) removed
- Shell cannot interpret sanitized filename
- Safe for filesystem operations

### Attack Vector 4: Symlink Traversal

**Attack**: Create symlink `/var/data/link` → `/etc/passwd`

**Detection**:
```python
>>> symlink = Path("/var/data/link")  # points to /etc/passwd
>>> validate_path_contained(symlink, Path("/var/data"))
SecurityError: Path traversal detected (symlink resolution)
```

**How We Block It**:
- `Path.resolve()` follows symlinks to actual target
- Target checked against base_dir
- Symlinks outside base_dir rejected

### Attack Vector 5: Windows Reserved Names

**Attack**: `CON` (Windows device name)

**Detection**:
```python
>>> sanitize_filename("CON")
'CON_file'
```

**How We Block It**:
- Reserved names detected (case-insensitive)
- `_file` suffix added
- Safe for Windows filesystems

## Testing and Validation

### Test Coverage

The security module has **91% test coverage** with 51 comprehensive tests covering:

- **Path Containment**: 11 tests
  - Valid relative/absolute paths
  - Directory traversal attacks
  - Symlink handling
  - Edge cases

- **Filename Sanitization**: 11 tests
  - Safe filenames
  - Unicode preservation
  - Dangerous character removal
  - Reserved name handling
  - Length limits

- **Permission Checking**: 8 tests
  - Existing/nonexistent directories
  - Read/write permissions
  - Parent directory validation

- **Integration**: 9 tests
  - End-to-end workflows
  - Multi-user isolation
  - Real-world attack patterns

### Running Tests

```bash
# Run security tests with coverage
python3 -m pytest tests/utils/test_security.py -v --cov=src.utils.security --cov-report=term-missing

# Expected output:
# 51 passed
# Coverage: 91%
```

### Example Test Cases

```python
# Test 1: Directory traversal blocked
def test_directory_traversal_attack():
    with pytest.raises(SecurityError, match="Path traversal detected"):
        validate_path_contained(Path("../etc/passwd"), base_dir)

# Test 2: Filename sanitization
def test_dangerous_characters_removed():
    assert sanitize_filename("file:name?.csv") == "filename.csv"

# Test 3: Permission checking
def test_readonly_directory():
    readonly_dir.chmod(0o444)
    with pytest.raises(PermissionError, match="not writable"):
        check_directory_permissions(readonly_dir)
```

## Best Practices

### 1. Always Validate User Input

```python
# ✓ GOOD: Validate before use
safe_path = validate_safe_path(user_input, base_dir)
safe_path.write_text(content)

# ✗ BAD: Direct use without validation
Path(user_input).write_text(content)  # SECURITY RISK!
```

### 2. Use validate_safe_path() for Convenience

```python
# ✓ GOOD: One function call validates everything
safe_path = validate_safe_path(path, base_dir, check_permissions=True)

# ✗ OKAY but verbose: Manual validation
sanitized = sanitize_filename(path.name)
validate_path_contained(path, base_dir)
check_directory_permissions(path.parent)
```

### 3. Handle Exceptions Appropriately

```python
# ✓ GOOD: Specific exception handling
try:
    safe_path = validate_safe_path(user_path, base_dir)
except SecurityError as e:
    log_security_event("path_rejected", str(e), path=user_path)
    raise ValueError(f"Invalid path: {e}") from e
except PermissionError as e:
    log_security_event("permission_denied", str(e), path=user_path)
    raise

# ✗ BAD: Catching all exceptions
try:
    safe_path = validate_safe_path(user_path, base_dir)
except Exception:
    pass  # Silent failure hides security issues!
```

### 4. Log Security Events

```python
# ✓ GOOD: Log for audit trail
from src.utils.security import log_security_event

try:
    validate_path_contained(user_path, base_dir)
except SecurityError as e:
    log_security_event("path_traversal_attempt", str(e), path=user_path)
    raise

# ✗ BAD: No logging
try:
    validate_path_contained(user_path, base_dir)
except SecurityError:
    raise  # No audit trail
```

### 5. Create Directories After Validation

```python
# ✓ GOOD: Validate first, then create
safe_path = validate_safe_path(path, base_dir)
safe_path.parent.mkdir(parents=True, exist_ok=True)
safe_path.write_text(content)

# ✗ BAD: Create before validation
path.parent.mkdir(parents=True, exist_ok=True)  # Might create outside base_dir!
validate_safe_path(path, base_dir)
```

### 6. Never Skip Validation

```python
# ✓ GOOD: Always validate
if user_provided:
    safe_path = validate_safe_path(path, base_dir)
else:
    safe_path = validate_safe_path(internal_path, base_dir)

# ✗ BAD: Skipping validation for "trusted" input
if user_provided:
    safe_path = validate_safe_path(path, base_dir)
else:
    safe_path = internal_path  # SECURITY RISK even for internal paths!
```

### 7. Use Pathlib, Not os.path

```python
# ✓ GOOD: pathlib provides better security
from pathlib import Path
safe_path = validate_safe_path(Path(user_input), base_dir)

# ✗ BAD: os.path is more error-prone
import os.path
path = os.path.join(base_dir, user_input)  # Can be bypassed with absolute paths!
```

### 8. Test with Real Attack Patterns

```python
# ✓ GOOD: Test with actual attack vectors
test_cases = [
    "../../../etc/passwd",
    "file\x00.txt",
    "file; rm -rf /",
    "CON",
    "/etc/passwd",
]

for attack in test_cases:
    with pytest.raises((SecurityError, ValueError)):
        validate_safe_path(Path(attack), base_dir)
```

## Security Checklist

When integrating the security framework, verify:

- [ ] All user-provided paths validated with `validate_safe_path()`
- [ ] SecurityError exceptions logged with `log_security_event()`
- [ ] Directories created AFTER validation, not before
- [ ] Permission errors handled appropriately
- [ ] Tests include real attack patterns
- [ ] No validation skipped for "internal" or "trusted" paths
- [ ] Using `pathlib.Path`, not `os.path`
- [ ] Error messages don't leak sensitive path information
- [ ] Audit trail maintained for security events
- [ ] Code coverage ≥90% for security-critical code

## Conclusion

The security framework provides comprehensive, defense-in-depth protection against file system attacks. By following the best practices in this document and using the provided validation functions, the OutputHandler system ensures that all file operations are safe and contained within approved directories.

**Key Takeaways**:

1. **Always validate** user-provided paths with `validate_safe_path()`
2. **Log security events** for audit trail
3. **Handle exceptions** appropriately with specific error types
4. **Test thoroughly** with real attack patterns
5. **Never skip validation**, even for "trusted" input

For questions or security concerns, review the test suite in `tests/utils/test_security.py` for comprehensive examples and edge cases.
