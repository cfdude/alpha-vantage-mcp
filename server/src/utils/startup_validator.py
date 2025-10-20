"""
Startup configuration validator for Alpha Vantage MCP Server.

This module validates all required configuration at server startup to catch
configuration issues early before tools are invoked.

Validation checks:
- Environment variables (ALPHA_VANTAGE_API_KEY, MCP_OUTPUT_DIR, etc.)
- Output directory existence and writability
- R2 configuration (if R2 is being used)
- Sprint 1 integration readiness
"""

import os
from dataclasses import dataclass
from typing import Any

from ..utils.output_config import OutputConfig


@dataclass
class ValidationResult:
    """
    Result of a configuration validation check.

    Attributes:
        check_name: Name of the validation check.
        passed: Whether the check passed.
        message: Human-readable message about the check result.
        severity: Severity level - "error" (fatal), "warning" (non-fatal), "info".
        details: Optional additional details about the check.
    """

    check_name: str
    passed: bool
    message: str
    severity: str = "error"  # error, warning, info
    details: dict[str, Any] | None = None


class StartupValidator:
    """
    Validates server configuration at startup.

    Performs comprehensive validation of all configuration required for
    the server to operate correctly. Collects all validation results
    and provides detailed reporting.
    """

    def __init__(self):
        """Initialize the startup validator."""
        self.results: list[ValidationResult] = []

    def validate_all(self) -> tuple[bool, list[ValidationResult]]:
        """
        Run all validation checks.

        Returns:
            Tuple of (all_passed, results) where all_passed is True if no errors.
        """
        self.results = []

        # Core checks (errors if they fail)
        self._check_api_key()

        # Sprint 1 integration checks (warnings if they fail)
        self._check_output_config()
        self._check_r2_config()

        # Determine overall success
        errors = [r for r in self.results if r.severity == "error" and not r.passed]
        all_passed = len(errors) == 0

        return all_passed, self.results

    def _check_api_key(self) -> None:
        """Validate Alpha Vantage API key is configured."""
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

        if not api_key:
            self.results.append(
                ValidationResult(
                    check_name="ALPHA_VANTAGE_API_KEY",
                    passed=False,
                    message="ALPHA_VANTAGE_API_KEY environment variable is not set",
                    severity="error",
                    details={"hint": "Set ALPHA_VANTAGE_API_KEY in your environment or .env file"},
                )
            )
        elif len(api_key.strip()) == 0:
            self.results.append(
                ValidationResult(
                    check_name="ALPHA_VANTAGE_API_KEY",
                    passed=False,
                    message="ALPHA_VANTAGE_API_KEY is set but empty",
                    severity="error",
                    details={"hint": "Provide a valid API key from www.alphavantage.co"},
                )
            )
        else:
            self.results.append(
                ValidationResult(
                    check_name="ALPHA_VANTAGE_API_KEY",
                    passed=True,
                    message=f"API key is configured ({api_key[:8]}...)",
                    severity="info",
                )
            )

    def _check_output_config(self) -> None:
        """Validate Sprint 1 output configuration."""
        try:
            config = OutputConfig()

            # Check if MCP_OUTPUT_DIR is set
            if not config.client_root:
                self.results.append(
                    ValidationResult(
                        check_name="MCP_OUTPUT_DIR",
                        passed=False,
                        message="MCP_OUTPUT_DIR not configured - Sprint 1 file output disabled",
                        severity="warning",
                        details={
                            "hint": "Set MCP_OUTPUT_DIR to enable local file output",
                            "fallback": "Server will use R2 upload for large responses",
                        },
                    )
                )
                return

            # Check directory exists
            if not config.client_root.exists():
                self.results.append(
                    ValidationResult(
                        check_name="MCP_OUTPUT_DIR",
                        passed=False,
                        message=f"Output directory does not exist: {config.client_root}",
                        severity="warning",
                        details={
                            "hint": f"Create directory: mkdir -p {config.client_root}",
                            "fallback": "Server will use R2 upload for large responses",
                        },
                    )
                )
                return

            # Check directory is writable
            test_file = config.client_root / ".startup_test"
            try:
                test_file.write_text("test")
                test_file.unlink()

                self.results.append(
                    ValidationResult(
                        check_name="MCP_OUTPUT_DIR",
                        passed=True,
                        message=f"Output directory is writable: {config.client_root}",
                        severity="info",
                        details={
                            "threshold": f"{config.output_token_threshold} tokens",
                            "auto_mode": config.output_auto,
                            "compression": config.output_compression,
                        },
                    )
                )
            except Exception as e:
                self.results.append(
                    ValidationResult(
                        check_name="MCP_OUTPUT_DIR",
                        passed=False,
                        message=f"Output directory is not writable: {config.client_root}",
                        severity="warning",
                        details={
                            "error": str(e),
                            "hint": f"Fix permissions: chmod u+w {config.client_root}",
                            "fallback": "Server will use R2 upload for large responses",
                        },
                    )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    check_name="OutputConfig",
                    passed=False,
                    message=f"Failed to load output configuration: {e}",
                    severity="warning",
                    details={
                        "error": str(e),
                        "fallback": "Server will use R2 upload for large responses",
                    },
                )
            )

    def _check_r2_config(self) -> None:
        """Validate R2 configuration (used as fallback for large responses)."""
        # R2 is optional - if not configured, large responses will fail gracefully
        r2_account_id = os.getenv("R2_ACCOUNT_ID")
        r2_access_key = os.getenv("R2_ACCESS_KEY_ID")
        r2_secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
        r2_bucket = os.getenv("R2_BUCKET_NAME")

        r2_configured = all([r2_account_id, r2_access_key, r2_secret_key, r2_bucket])

        if r2_configured:
            self.results.append(
                ValidationResult(
                    check_name="R2_CONFIG",
                    passed=True,
                    message="R2 storage is configured (used for large responses)",
                    severity="info",
                    details={"bucket": r2_bucket, "account_id": r2_account_id[:8] + "..."},
                )
            )
        else:
            # Missing R2 is only a warning if MCP_OUTPUT_DIR is also not configured
            mcp_output_dir = os.getenv("MCP_OUTPUT_DIR")

            if not mcp_output_dir:
                self.results.append(
                    ValidationResult(
                        check_name="R2_CONFIG",
                        passed=False,
                        message="R2 storage not configured - large responses may fail",
                        severity="warning",
                        details={
                            "hint": "Configure R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME",
                            "alternative": "Or set MCP_OUTPUT_DIR for local file output",
                        },
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        check_name="R2_CONFIG",
                        passed=True,
                        message="R2 not configured (using MCP_OUTPUT_DIR for file output)",
                        severity="info",
                    )
                )

    def print_results(self, results: list[ValidationResult]) -> None:
        """
        Print validation results to console.

        Args:
            results: List of validation results to print.
        """
        print("\n" + "=" * 70)
        print("🔍 Alpha Vantage MCP Server - Startup Validation")
        print("=" * 70)

        errors = []
        warnings = []
        infos = []

        for result in results:
            if result.severity == "error":
                errors.append(result)
            elif result.severity == "warning":
                warnings.append(result)
            else:
                infos.append(result)

        # Print errors first
        if errors:
            print("\n❌ ERRORS:")
            for result in errors:
                print(f"  • {result.check_name}: {result.message}")
                if result.details:
                    for key, value in result.details.items():
                        print(f"    {key}: {value}")

        # Print warnings
        if warnings:
            print("\n⚠️  WARNINGS:")
            for result in warnings:
                print(f"  • {result.check_name}: {result.message}")
                if result.details:
                    for key, value in result.details.items():
                        print(f"    {key}: {value}")

        # Print info
        if infos:
            print("\n✅ INFO:")
            for result in infos:
                print(f"  • {result.check_name}: {result.message}")

        print("\n" + "=" * 70)

        # Print summary
        total_checks = len(results)
        passed_checks = len([r for r in results if r.passed])
        print(f"📊 Summary: {passed_checks}/{total_checks} checks passed")

        if errors:
            print(f"❌ {len(errors)} error(s) - server cannot start")
        elif warnings:
            print(f"⚠️  {len(warnings)} warning(s) - server will start with limited functionality")
        else:
            print("✅ All checks passed - server is ready")

        print("=" * 70 + "\n")


def validate_startup_config(verbose: bool = True) -> bool:
    """
    Validate server configuration at startup.

    Args:
        verbose: If True, print detailed validation results to console.

    Returns:
        True if all critical checks passed, False otherwise.
    """
    validator = StartupValidator()
    all_passed, results = validator.validate_all()

    if verbose:
        validator.print_results(results)

    # Exit if there are any errors
    if not all_passed:
        errors = [r for r in results if r.severity == "error" and not r.passed]
        print(f"\n❌ Server startup aborted due to {len(errors)} configuration error(s)\n")
        return False

    return True
