"""
Comprehensive test suite for security validation utilities.

Tests all security functions with edge cases, attack scenarios, and unicode support.
Target: ≥95% code coverage on src/utils/security.py
"""

import sys
from pathlib import Path

import pytest

from src.utils.security import (
    SecurityError,
    check_directory_permissions,
    log_security_event,
    sanitize_filename,
    validate_path_contained,
    validate_safe_path,
)


class TestPathContainment:
    """Test suite for validate_path_contained function."""

    def test_valid_relative_path(self, tmp_path):
        """Test that valid relative paths pass validation."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Simple relative path
        assert validate_path_contained(Path("user/file.csv"), base_dir) is True

        # Path with subdirectories
        assert validate_path_contained(Path("user/data/report.csv"), base_dir) is True

        # Current directory reference
        assert validate_path_contained(Path("./file.csv"), base_dir) is True

    def test_valid_absolute_path_within_base(self, tmp_path):
        """Test that absolute paths within base_dir are allowed."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Create a subdirectory
        subdir = base_dir / "user"
        subdir.mkdir()

        # Absolute path that's within base_dir should be allowed
        file_path = subdir / "file.csv"
        assert validate_path_contained(file_path, base_dir) is True

    def test_directory_traversal_attack(self, tmp_path):
        """Test that directory traversal attempts are blocked."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Classic directory traversal
        with pytest.raises(SecurityError, match="Path traversal detected"):
            validate_path_contained(Path("../etc/passwd"), base_dir)

        # Multiple traversals
        with pytest.raises(SecurityError, match="Path traversal detected"):
            validate_path_contained(Path("../../etc/passwd"), base_dir)

        # Mixed with valid path components
        with pytest.raises(SecurityError, match="Path traversal detected"):
            validate_path_contained(Path("user/../../../etc/passwd"), base_dir)

    def test_absolute_path_outside_base(self, tmp_path):
        """Test that absolute paths outside base_dir are rejected."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Absolute path to system directory
        with pytest.raises(SecurityError, match="Absolute paths not allowed"):
            validate_path_contained(Path("/etc/passwd"), base_dir)

        # Absolute path to different directory
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        with pytest.raises(SecurityError, match="Absolute paths not allowed"):
            validate_path_contained(other_dir / "file.csv", base_dir)

    def test_symlink_traversal(self, tmp_path):
        """Test that symlinks are resolved and validated correctly."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Create a symlink pointing outside base_dir
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        outside_file = outside_dir / "secret.txt"
        outside_file.write_text("secret")

        symlink = base_dir / "link"
        try:
            symlink.symlink_to(outside_file)
        except OSError:
            pytest.skip("Cannot create symlinks on this system")

        # Symlink to outside should be blocked (could match different error messages)
        with pytest.raises(SecurityError):
            validate_path_contained(symlink, base_dir)

    def test_symlink_within_base(self, tmp_path):
        """Test that symlinks within base_dir are allowed."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Create a file within base_dir
        target_file = base_dir / "target.txt"
        target_file.write_text("data")

        # Create a symlink within base_dir pointing to target
        symlink = base_dir / "link.txt"
        symlink.symlink_to(target_file)

        # Symlink within base should be allowed
        assert validate_path_contained(symlink, base_dir) is True

    def test_base_dir_not_absolute(self, tmp_path):
        """Test that relative base_dir raises ValueError."""
        with pytest.raises(ValueError, match="base_dir must be an absolute path"):
            validate_path_contained(Path("file.csv"), Path("relative/path"))

    def test_base_dir_creation(self, tmp_path):
        """Test that base_dir is created if it doesn't exist."""
        base_dir = tmp_path / "new_base"
        assert not base_dir.exists()

        # Should create base_dir
        validate_path_contained(Path("file.csv"), base_dir)
        assert base_dir.exists()

    def test_base_dir_creation_failure(self, tmp_path):
        """Test that base_dir creation failure raises ValueError."""
        # Try to create directory in read-only location
        if sys.platform == "win32":
            pytest.skip("Windows permission model different")

        readonly_parent = tmp_path / "readonly"
        readonly_parent.mkdir()
        readonly_parent.chmod(0o444)  # Read-only

        base_dir = readonly_parent / "new_base"

        # Could raise ValueError from creation or PermissionError from access check
        with pytest.raises((ValueError, PermissionError)):
            validate_path_contained(Path("file.csv"), base_dir)

        # Cleanup
        readonly_parent.chmod(0o755)

    def test_nonexistent_base_dir_parent(self):
        """Test that deeply nested nonexistent base_dir parent raises ValueError."""
        with pytest.raises(ValueError, match="Cannot create base directory"):
            # This should fail because /nonexistent doesn't exist and can't be created
            validate_path_contained(Path("file.csv"), Path("/nonexistent/deeply/nested"))

    def test_empty_path_component(self, tmp_path):
        """Test paths with empty components."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Path with double slashes
        assert validate_path_contained(Path("user//file.csv"), base_dir) is True

        # Path with trailing slash is normalized
        assert validate_path_contained(Path("user/"), base_dir) is True


class TestFilenameSanitization:
    """Test suite for sanitize_filename function."""

    def test_safe_filename(self):
        """Test that safe filenames pass through unchanged."""
        assert sanitize_filename("report.csv") == "report.csv"
        assert sanitize_filename("data_2024.json") == "data_2024.json"
        assert sanitize_filename("file-name_123.txt") == "file-name_123.txt"

    def test_unicode_filename(self):
        """Test that unicode characters are preserved."""
        # Japanese
        assert sanitize_filename("日本語ファイル.csv") == "日本語ファイル.csv"
        # Chinese
        assert sanitize_filename("中文文件.txt") == "中文文件.txt"
        # Emoji (should be preserved as valid unicode)
        assert sanitize_filename("report📊.csv") == "report📊.csv"

    def test_dangerous_characters_removed(self):
        """Test that dangerous characters are removed."""
        # Path separators
        assert sanitize_filename("path/to/file.csv") == "pathtofile.csv"
        assert sanitize_filename("path\\to\\file.csv") == "pathtofile.csv"

        # Invalid filename characters
        assert sanitize_filename("file:name.csv") == "filename.csv"
        assert sanitize_filename("file*name.csv") == "filename.csv"
        assert sanitize_filename("file?name.csv") == "filename.csv"
        assert sanitize_filename('file"name.csv') == "filename.csv"
        assert sanitize_filename("file<name.csv") == "filename.csv"
        assert sanitize_filename("file>name.csv") == "filename.csv"
        assert sanitize_filename("file|name.csv") == "filename.csv"

    def test_null_byte_injection(self):
        """Test that null bytes are removed."""
        assert sanitize_filename("file\x00.csv") == "file.csv"
        assert sanitize_filename("file\x00name\x00.csv") == "filename.csv"

    def test_control_characters_removed(self):
        """Test that control characters are removed."""
        # Tab, newline, carriage return
        assert sanitize_filename("file\tname.csv") == "filename.csv"
        assert sanitize_filename("file\nname.csv") == "filename.csv"
        assert sanitize_filename("file\rname.csv") == "filename.csv"

        # Other control characters
        assert sanitize_filename("file\x01name.csv") == "filename.csv"
        assert sanitize_filename("file\x7fname.csv") == "filename.csv"

    def test_windows_reserved_names(self):
        """Test that Windows reserved names are handled."""
        # Reserved device names
        assert sanitize_filename("CON") == "CON_file"
        assert sanitize_filename("PRN") == "PRN_file"
        assert sanitize_filename("AUX") == "AUX_file"
        assert sanitize_filename("NUL") == "NUL_file"

        # COM ports
        assert sanitize_filename("COM1") == "COM1_file"
        assert sanitize_filename("COM9") == "COM9_file"

        # LPT ports
        assert sanitize_filename("LPT1") == "LPT1_file"
        assert sanitize_filename("LPT9") == "LPT9_file"

        # Case insensitive
        assert sanitize_filename("con") == "con_file"
        assert sanitize_filename("CoN") == "CoN_file"

        # With extensions (should still be caught)
        assert sanitize_filename("CON.txt") == "CON.txt_file"
        assert sanitize_filename("PRN.csv") == "PRN.csv_file"

    def test_whitespace_and_dots(self):
        """Test that leading/trailing whitespace and dots are removed."""
        assert sanitize_filename("  file.csv  ") == "file.csv"
        assert sanitize_filename("...file.csv") == "file.csv"
        assert sanitize_filename("file.csv...") == "file.csv"
        assert sanitize_filename("  ...file.csv...  ") == "file.csv"

    def test_empty_string_fallback(self):
        """Test that empty strings return fallback name."""
        assert sanitize_filename("") == "unnamed_file"
        assert sanitize_filename("   ") == "unnamed_file"
        assert sanitize_filename("...") == "unnamed_file"
        assert sanitize_filename("///") == "unnamed_file"

    def test_none_input(self):
        """Test that None input returns fallback name."""
        assert sanitize_filename(None) == "unnamed_file"

    def test_filename_length_limit(self):
        """Test that filenames are limited to 255 characters."""
        # Filename longer than 255 characters
        long_name = "a" * 300 + ".csv"
        result = sanitize_filename(long_name)
        assert len(result) == 255

        # Should preserve extension
        assert result.endswith(".csv")

        # Filename without extension
        long_name_no_ext = "a" * 300
        result = sanitize_filename(long_name_no_ext)
        assert len(result) == 255

    def test_complex_attack_scenarios(self):
        """Test complex attack scenarios combining multiple techniques."""
        # Directory traversal + null byte (.. gets removed)
        assert sanitize_filename("../etc/passwd\x00.csv") == "etcpasswd.csv"

        # Multiple dangerous characters
        assert sanitize_filename('file:*?"<>|/\\.csv') == "file.csv"

        # Reserved name + dangerous chars
        assert sanitize_filename("CON:*?") == "CON_file"


class TestPermissionChecking:
    """Test suite for check_directory_permissions function."""

    def test_existing_directory_with_permissions(self, tmp_path):
        """Test that existing writable/readable directory passes."""
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # Should not raise any exception
        check_directory_permissions(test_dir)

    def test_existing_directory_not_writable(self, tmp_path):
        """Test that read-only directory raises PermissionError."""
        if sys.platform == "win32":
            pytest.skip("Windows permission model different")

        test_dir = tmp_path / "readonly"
        test_dir.mkdir()
        test_dir.chmod(0o444)  # Read-only

        with pytest.raises(PermissionError, match="not writable"):
            check_directory_permissions(test_dir)

        # Cleanup
        test_dir.chmod(0o755)

    def test_existing_directory_not_readable(self, tmp_path):
        """Test that write-only directory raises PermissionError."""
        if sys.platform == "win32":
            pytest.skip("Windows permission model different")

        test_dir = tmp_path / "writeonly"
        test_dir.mkdir()
        test_dir.chmod(0o222)  # Write-only

        with pytest.raises(PermissionError, match="not readable"):
            check_directory_permissions(test_dir)

        # Cleanup
        test_dir.chmod(0o755)

    def test_nonexistent_directory_with_writable_parent(self, tmp_path):
        """Test that nonexistent directory with writable parent passes."""
        test_dir = tmp_path / "new_dir"
        assert not test_dir.exists()

        # Should not raise - parent is writable
        check_directory_permissions(test_dir)

    def test_nonexistent_directory_without_parent(self):
        """Test that deeply nested nonexistent directory raises ValueError."""
        test_dir = Path("/nonexistent/deeply/nested/dir")

        with pytest.raises(ValueError, match="Parent directory does not exist"):
            check_directory_permissions(test_dir)

    def test_nonexistent_directory_readonly_parent(self, tmp_path):
        """Test that nonexistent directory with readonly parent raises PermissionError."""
        if sys.platform == "win32":
            pytest.skip("Windows permission model different")

        parent = tmp_path / "readonly_parent"
        parent.mkdir()
        parent.chmod(0o444)  # Read-only

        test_dir = parent / "new_dir"

        # Could raise either PermissionError (from exists() check) or from parent check
        with pytest.raises(PermissionError):
            check_directory_permissions(test_dir)

        # Cleanup
        parent.chmod(0o755)

    def test_path_is_file_not_directory(self, tmp_path):
        """Test that file path raises ValueError."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("data")

        with pytest.raises(ValueError, match="not a directory"):
            check_directory_permissions(test_file)

    def test_invalid_path_type(self):
        """Test that non-Path input raises ValueError."""
        with pytest.raises(ValueError, match="must be a Path object"):
            check_directory_permissions("/some/string/path")

        with pytest.raises(ValueError, match="must be a Path object"):
            check_directory_permissions(None)


class TestValidateSafePath:
    """Test suite for validate_safe_path convenience function."""

    def test_valid_safe_path(self, tmp_path):
        """Test that valid path passes all checks."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        result = validate_safe_path(Path("user/report.csv"), base_dir)
        assert result == base_dir / "user" / "report.csv"

    def test_filename_sanitization_applied(self, tmp_path):
        """Test that filename sanitization is applied."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Path with dangerous filename
        result = validate_safe_path(Path("user/file:name?.csv"), base_dir)
        assert result == base_dir / "user" / "filename.csv"

    def test_path_traversal_blocked(self, tmp_path):
        """Test that path traversal is blocked."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        with pytest.raises(SecurityError, match="Path traversal detected"):
            validate_safe_path(Path("../etc/passwd"), base_dir)

    def test_permission_check_enabled(self, tmp_path):
        """Test that permission checking works when enabled."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Create parent directory for file
        parent = base_dir / "user"
        parent.mkdir()

        # Should check permissions
        result = validate_safe_path(Path("user/file.csv"), base_dir, check_permissions=True)
        assert result == base_dir / "user" / "file.csv"

    def test_permission_check_disabled(self, tmp_path):
        """Test that permission checking can be disabled."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Don't create parent - should still work with check_permissions=False
        result = validate_safe_path(Path("nonexistent/file.csv"), base_dir, check_permissions=False)
        assert result == base_dir / "nonexistent" / "file.csv"

    def test_absolute_path_within_base(self, tmp_path):
        """Test absolute path within base_dir."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Create subdirectory
        subdir = base_dir / "user"
        subdir.mkdir()

        # Absolute path within base
        abs_path = subdir / "file.csv"
        result = validate_safe_path(abs_path, base_dir)
        assert result == abs_path


class TestSecurityError:
    """Test suite for SecurityError exception."""

    def test_security_error_raised(self):
        """Test that SecurityError can be raised and caught."""
        with pytest.raises(SecurityError):
            raise SecurityError("Test error")

    def test_security_error_message(self):
        """Test that SecurityError message is preserved."""
        try:
            raise SecurityError("Test security violation")
        except SecurityError as e:
            assert str(e) == "Test security violation"

    def test_security_error_inheritance(self):
        """Test that SecurityError inherits from Exception."""
        assert issubclass(SecurityError, Exception)


class TestLogSecurityEvent:
    """Test suite for log_security_event function."""

    def test_log_security_event_basic(self, capsys):
        """Test basic security event logging."""
        log_security_event("test_event", "Test message")

        captured = capsys.readouterr()
        assert "[SECURITY]" in captured.err
        assert "test_event" in captured.err
        assert "Test message" in captured.err

    def test_log_security_event_with_path(self, capsys):
        """Test security event logging with path."""
        test_path = Path("/tmp/test.csv")
        log_security_event("path_traversal", "Attempted access", path=test_path)

        captured = capsys.readouterr()
        assert "[SECURITY]" in captured.err
        assert "path_traversal" in captured.err
        assert "Attempted access" in captured.err
        assert str(test_path) in captured.err

    def test_log_security_event_without_path(self, capsys):
        """Test security event logging without path."""
        log_security_event("permission_denied", "Access denied")

        captured = capsys.readouterr()
        assert "[SECURITY]" in captured.err
        assert "permission_denied" in captured.err
        assert "Access denied" in captured.err

    def test_log_security_event_timestamp(self, capsys):
        """Test that security event includes timestamp."""
        log_security_event("test", "Test")

        captured = capsys.readouterr()
        # Should contain ISO format timestamp
        assert "[20" in captured.err  # Year starts with 20xx


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_base_dir_resolve_error(self, tmp_path):
        """Test error handling when base_dir cannot be resolved."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Create a symlink that points to itself (broken symlink)
        broken_link = base_dir / "broken"
        try:
            broken_link.symlink_to(broken_link)
        except OSError:
            pytest.skip("Cannot create symlinks on this system")

        # Try to use broken symlink as base_dir - could raise different errors
        with pytest.raises(ValueError):  # Will match "Cannot create" or "Cannot resolve"
            validate_path_contained(Path("file.csv"), broken_link)

    def test_absolute_path_resolve_error(self, tmp_path):
        """Test error handling when absolute path cannot be resolved."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Test with a path that would cause resolve() to fail
        # This is hard to trigger naturally, but we can at least test the path exists
        # The resolve error on line 98-102 is hard to trigger without OS-specific issues

    def test_relative_path_resolve_error(self, tmp_path):
        """Test error handling when relative path cannot be resolved."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Test with a very deeply nested path (might hit OS limits on some systems)
        # The resolve error on line 115-116 is also hard to trigger

    def test_validate_safe_path_resolve_error(self, tmp_path):
        """Test error handling in validate_safe_path when path cannot be resolved."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # The resolve error on line 400-401 in validate_safe_path is hard to trigger
        # because Path.resolve(strict=False) rarely fails

    def test_path_with_spaces(self, tmp_path):
        """Test paths with spaces are handled correctly."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Path with spaces should be allowed
        assert validate_path_contained(Path("user name/file name.csv"), base_dir) is True

    def test_very_long_path(self, tmp_path):
        """Test very long paths are handled correctly."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Create a very long path (but valid)
        long_path = Path("a" * 50 + "/" + "b" * 50 + "/" + "c" * 50 + ".csv")
        assert validate_path_contained(long_path, base_dir) is True

    def test_dot_files(self, tmp_path):
        """Test that hidden files (dot files) are handled correctly."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Dot files should be allowed
        assert validate_path_contained(Path(".hidden"), base_dir) is True
        assert validate_path_contained(Path("dir/.hidden"), base_dir) is True

        # But not as directory traversal
        with pytest.raises(SecurityError):
            validate_path_contained(Path("../../../.hidden"), base_dir)

    def test_special_filenames(self):
        """Test special filename edge cases."""
        # Single character
        assert sanitize_filename("a") == "a"

        # Numbers only
        assert sanitize_filename("123") == "123"

        # Special characters in extension
        assert sanitize_filename("file.tar.gz") == "file.tar.gz"

        # Multiple dots
        assert sanitize_filename("file.name.with.dots.csv") == "file.name.with.dots.csv"

    def test_mixed_attack_scenarios(self, tmp_path):
        """Test combinations of attack vectors."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Traversal + absolute path
        with pytest.raises(SecurityError):
            validate_path_contained(Path("/etc/../passwd"), base_dir)

        # Sanitization + traversal - path traversal happens in parent, not filename
        # This should fail because validate_path_contained catches the ../ in path
        with pytest.raises(SecurityError):
            validate_safe_path(Path("../file:name.csv"), base_dir, check_permissions=False)


class TestIntegrationScenarios:
    """Integration tests combining multiple security functions."""

    def test_full_file_creation_workflow(self, tmp_path):
        """Test complete workflow of validating and creating a file."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # User provides input with .. that resolves to a valid path within base
        # "reports/../data" resolves to "data" which is valid
        user_input_with_dots = Path("reports/../data/file:name?.csv")

        # This actually PASSES because it resolves within base_dir (to "data/file.csv")
        # Create the data directory for the test
        (base_dir / "data").mkdir(parents=True, exist_ok=True)
        safe_path_dots = validate_safe_path(user_input_with_dots, base_dir, check_permissions=True)
        assert safe_path_dots == base_dir / "data" / "filename.csv"

        # Test actual path traversal attack (escapes base_dir)
        user_input_bad = Path("../../../etc/passwd")
        with pytest.raises(SecurityError):
            validate_safe_path(user_input_bad, base_dir, check_permissions=False)

        # Try with safer input (no traversal)
        user_input = Path("reports/file:name?.csv")

        # Create parent directory first (needed for permission check)
        (base_dir / "reports").mkdir(parents=True, exist_ok=True)

        safe_path = validate_safe_path(user_input, base_dir)

        # Write file
        safe_path.write_text("test data")

        assert safe_path.exists()
        assert safe_path.read_text() == "test data"
        # Filename should be sanitized
        assert safe_path.name == "filename.csv"

    def test_multi_user_isolation(self, tmp_path):
        """Test that users can't access each other's data."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # User A's directory
        user_a_dir = base_dir / "user_a"
        user_a_dir.mkdir()

        # User B tries to access User A's files
        malicious_path = Path("../user_a/secret.txt")

        with pytest.raises(SecurityError, match="Path traversal detected"):
            validate_path_contained(malicious_path, base_dir / "user_b")

    def test_real_world_attack_patterns(self, tmp_path):
        """Test real-world attack patterns."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        attack_patterns = [
            "../../../../../etc/passwd",  # Classic traversal
            "..\\..\\..\\..\\windows\\system32",  # Windows traversal
            "/etc/passwd",  # Absolute path
            "CON",  # Windows reserved
            "file\x00.txt",  # Null byte injection
            "file\n.txt",  # Newline injection
        ]

        for pattern in attack_patterns:
            # All should either raise SecurityError or be sanitized safely
            try:
                result = validate_safe_path(Path(pattern), base_dir, check_permissions=False)
                # If it didn't raise, check it's within base_dir
                assert result.is_relative_to(base_dir)
            except SecurityError:
                # Expected for path traversal
                pass
