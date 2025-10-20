import asyncio
import csv
import io
import json
import os
from datetime import UTC, datetime

import httpx

from src.context import get_api_key
from src.integration.helpers import (
    create_file_reference_response,
    create_inline_response,
    should_use_output_helper,
)
from src.output.handler import OutputHandler
from src.utils import estimate_tokens, upload_to_r2
from src.utils.output_config import OutputConfig

API_BASE_URL = "https://www.alphavantage.co/query"

# Maximum token size for responses (configurable via environment variable)
# Used as fallback when MCP_OUTPUT_DIR is not configured
MAX_RESPONSE_TOKENS = int(os.environ.get("MAX_RESPONSE_TOKENS", "50000"))


def _parse_csv_to_dicts(csv_string: str) -> list[dict]:
    """
    Parse CSV string into list of dictionaries.

    Args:
        csv_string: CSV data as string.

    Returns:
        List of dictionaries with CSV data.

    Raises:
        ValueError: If CSV parsing fails.
    """
    try:
        reader = csv.DictReader(io.StringIO(csv_string))
        return list(reader)
    except Exception as e:
        raise ValueError(f"Failed to parse CSV response: {e}") from e


def _parse_json_response(json_string: str) -> dict | list:
    """
    Parse JSON string into dict or list.

    Args:
        json_string: JSON data as string.

    Returns:
        Parsed JSON data (dict or list).

    Raises:
        ValueError: If JSON parsing fails.
    """
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}") from e


def _create_preview(
    response_text: str, datatype: str, estimated_tokens: int, error: str = None
) -> dict:
    """Create preview data for large responses (R2 fallback)."""
    lines = response_text.split("\n")
    preview = {
        "preview": True,
        "data_type": datatype,
        "total_lines": len(lines),
        "sample_data": "\n".join(lines[:50]),  # First 50 lines
        "headers": lines[0] if lines else None,
        "full_data_tokens": estimated_tokens,
        "max_tokens_exceeded": True,
        "content_type": "text/csv" if datatype == "csv" else "application/json",
        "message": f"Response size ({estimated_tokens} tokens) exceeds limit ({MAX_RESPONSE_TOKENS} tokens). {'Unable to provide full data URL.' if error else 'Full data available at URL.'}",
        "usage_instructions": {
            "important_notes": [
                (
                    "Do not fetch the data_url directly into chat context - this will overwhelm the conversation"
                    if not error
                    else "Response was too large for direct display in chat context"
                ),
                "For claude artifacts, prefer TSX artifact using tailwindcss, and in generated page, put this to the top: data from current page is generated sample data, for real data, copy this page code to https://mcp.alphavantage.co/artifacts",
                "When creating artifacts (charts/visualizations), use the provided preview data as fallback due to Content Security Policy (CSP) restrictions",
                (
                    "For full dataset access, consider reducing the query scope or using outputsize='compact' parameter"
                    if error
                    else None
                ),
            ],
            "recommended_workflow": [
                "1. Use preview data to create initial visualization in artifact",
                (
                    "2. Include data_url fetch logic with preview data fallback"
                    if not error
                    else "2. Consider making multiple smaller API requests if full dataset is needed"
                ),
                (
                    "3. Copy artifact code and test with full data at https://mcp.alphavantage.co/artifacts"
                    if not error
                    else "3. Use compact output size when available to reduce response size"
                ),
            ],
        },
    }

    # Filter out None values from important_notes
    preview["usage_instructions"]["important_notes"] = [
        note for note in preview["usage_instructions"]["important_notes"] if note is not None
    ]

    if error:
        preview["error"] = f"Failed to upload large response: {error}"

    return preview


def _make_api_request(
    function_name: str,
    params: dict,
    force_inline: bool = False,
    force_file: bool = False,
) -> dict | str:
    """
    Helper function to make API requests and handle responses with Sprint 1 integration.

    This function integrates Sprint 1's output helper system:
    - Uses OutputConfig for configuration
    - Uses should_use_output_helper() for intelligent file vs inline decisions
    - Uses OutputHandler for file writing (CSV/JSON)
    - Uses create_inline_response() for standardized inline responses
    - Falls back to R2 upload when MCP_OUTPUT_DIR is not configured

    Args:
        function_name: Alpha Vantage API function name.
        params: API parameters (without function, apikey, source).
        force_inline: Force inline output regardless of size (overrides auto-decision).
        force_file: Force file output regardless of size (overrides auto-decision).

    Returns:
        - If using Sprint 1 file output: dict with file_reference
        - If using Sprint 1 inline output: dict with inline_data
        - If falling back to R2: dict with preview or CSV/JSON string
        - On error: dict with error information

    Raises:
        httpx.HTTPStatusError: If API request fails.
        ValueError: If both force_inline and force_file are True.
    """
    # Validate force flags
    if force_inline and force_file:
        raise ValueError("Cannot set both force_inline and force_file to True")

    # Create a copy of params to avoid modifying the original
    api_params = params.copy()
    api_params.update(
        {"function": function_name, "apikey": get_api_key(), "source": "alphavantagemcp"}
    )

    # Handle entitlement parameter if present in params or global variable
    current_entitlement = globals().get("_current_entitlement")
    entitlement = api_params.get("entitlement") or current_entitlement

    if entitlement:
        api_params["entitlement"] = entitlement
    elif "entitlement" in api_params:
        # Remove entitlement if it's None or empty
        api_params.pop("entitlement", None)

    # Make HTTP request to Alpha Vantage API
    with httpx.Client() as client:
        response = client.get(API_BASE_URL, params=api_params)
        response.raise_for_status()
        response_text = response.text

    # Determine datatype from params (default to csv if not specified)
    datatype = api_params.get("datatype", "csv")

    # Parse response into structured data for Sprint 1 infrastructure
    try:
        if datatype == "csv":
            parsed_data = _parse_csv_to_dicts(response_text)
        else:  # json
            # Try parsing as JSON, fall back to raw text if it fails
            try:
                parsed_data = _parse_json_response(response_text)
            except ValueError:
                parsed_data = response_text
    except ValueError:
        # If parsing fails, fall back to legacy behavior
        return response_text

    # Try to load OutputConfig for Sprint 1 integration
    try:
        config = OutputConfig()
        use_sprint1 = True
    except Exception:
        # MCP_OUTPUT_DIR not configured - fall back to R2 upload
        use_sprint1 = False

    # Sprint 1 Integration: Use output helper system
    if use_sprint1:
        try:
            # Make output decision using Sprint 1 infrastructure
            decision = should_use_output_helper(
                data=parsed_data,
                config=config,
                force_inline=force_inline,
                force_file=force_file,
                filename_prefix=function_name.lower(),
            )

            # FILE OUTPUT: Use OutputHandler to write to file
            if decision.use_file:
                # Generate filename with timestamp
                timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
                filename = f"{function_name.lower()}_{timestamp}.{datatype}"
                filepath = config.client_root / filename

                # Write data to file using async OutputHandler
                handler = OutputHandler(config)
                if datatype == "csv":
                    metadata = asyncio.run(handler.write_csv(parsed_data, filepath, config))
                else:  # json
                    metadata = asyncio.run(handler.write_json(parsed_data, filepath, config))

                # Return standardized file reference response
                return create_file_reference_response(filepath, metadata, config)

            # INLINE OUTPUT: Use create_inline_response for standardized format
            else:
                return create_inline_response(parsed_data, format=datatype)

        except Exception:
            # If Sprint 1 integration fails, fall back to R2 upload
            # Log error but continue with fallback
            use_sprint1 = False

    # Legacy R2 Fallback: When MCP_OUTPUT_DIR not configured or Sprint 1 fails
    if not use_sprint1:
        # Estimate tokens for size decision
        estimated_tokens = estimate_tokens(response_text)

        # If response is within limits, return normally (legacy behavior)
        if estimated_tokens <= MAX_RESPONSE_TOKENS:
            if datatype == "json":
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    return response_text
            else:
                return response_text

        # For large responses, upload to R2 and return preview
        try:
            # Upload raw response to R2
            data_url = upload_to_r2(response_text)

            # Create preview with data URL
            preview = _create_preview(response_text, datatype, estimated_tokens)
            preview["data_url"] = data_url

            return preview

        except Exception as e:
            # If R2 upload fails, return error with preview
            return _create_preview(response_text, datatype, estimated_tokens, str(e))
