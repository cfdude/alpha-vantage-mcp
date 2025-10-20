"""
R2 storage connection validator for Alpha Vantage MCP Server.

This module provides utilities to test R2 (Cloudflare R2) connectivity
and configuration at startup.
"""

import os
from dataclasses import dataclass

import boto3
from botocore.exceptions import BotoCoreError, ClientError


@dataclass
class R2ConnectionResult:
    """
    Result of R2 connection test.

    Attributes:
        success: Whether the connection test succeeded.
        message: Human-readable message about the result.
        details: Optional additional details.
    """

    success: bool
    message: str
    details: dict[str, str] | None = None


def test_r2_connection(timeout: int = 5) -> R2ConnectionResult:
    """
    Test R2 storage connectivity.

    Attempts to connect to R2 and verify bucket access without uploading data.

    Args:
        timeout: Connection timeout in seconds (default: 5).

    Returns:
        R2ConnectionResult with test outcome.
    """
    # Check if R2 is configured
    account_id = os.getenv("R2_ACCOUNT_ID")
    access_key_id = os.getenv("R2_ACCESS_KEY_ID")
    secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
    bucket_name = os.getenv("R2_BUCKET_NAME")

    if not all([account_id, access_key_id, secret_access_key, bucket_name]):
        return R2ConnectionResult(
            success=False,
            message="R2 not configured (missing environment variables)",
            details={
                "required": "R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME"
            },
        )

    try:
        # Create R2 client
        endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

        s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=boto3.session.Config(
                signature_version="s3v4",
                connect_timeout=timeout,
                read_timeout=timeout,
            ),
        )

        # Test connection by checking if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)

            return R2ConnectionResult(
                success=True,
                message=f"R2 connection successful - bucket '{bucket_name}' is accessible",
                details={"endpoint": endpoint_url, "bucket": bucket_name},
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")

            if error_code == "404":
                return R2ConnectionResult(
                    success=False,
                    message=f"R2 bucket '{bucket_name}' does not exist",
                    details={
                        "error_code": error_code,
                        "hint": f"Create bucket '{bucket_name}' in Cloudflare R2 dashboard",
                    },
                )
            elif error_code == "403":
                return R2ConnectionResult(
                    success=False,
                    message=f"Access denied to R2 bucket '{bucket_name}'",
                    details={
                        "error_code": error_code,
                        "hint": "Check R2 API credentials and permissions",
                    },
                )
            else:
                return R2ConnectionResult(
                    success=False,
                    message=f"R2 connection failed: {str(e)}",
                    details={"error_code": error_code, "error": str(e)},
                )

    except BotoCoreError as e:
        return R2ConnectionResult(
            success=False,
            message=f"R2 client error: {str(e)}",
            details={"error": str(e), "hint": "Check network connectivity and R2 configuration"},
        )

    except Exception as e:
        return R2ConnectionResult(
            success=False,
            message=f"Unexpected error testing R2 connection: {str(e)}",
            details={"error": str(e)},
        )
