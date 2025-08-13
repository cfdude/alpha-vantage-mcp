"""Common utility functions shared across modules."""
import json
import hashlib
import time
from typing import Any

def parse_token_from_request(event: dict) -> str:
    """Parse API key from request body, query params, or Authorization header. Priority: body > query > header."""
    # Check request body first (highest priority)
    if event.get("body"):
        try:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
            if isinstance(body, dict) and "apikey" in body and body["apikey"]:
                return body["apikey"]
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Check query parameters second
    query_params = event.get("queryStringParameters") or {}
    if "apikey" in query_params and query_params["apikey"]:
        return query_params["apikey"]
    
    # Fallback to Authorization header
    headers = event.get("headers", {})
    auth_header = headers.get("Authorization") or headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    return ""

def parse_tool_categories_from_request(event: dict) -> list[str] | None:
    """Parse tool categories from request path or query parameters."""
    path = event.get("path", "/")
    query_params = event.get("queryStringParameters") or {}
    
    # Check for categories in query parameters first (new method)
    if "categories" in query_params and query_params["categories"]:
        categories = [cat.strip() for cat in query_params["categories"].split(",") if cat.strip()]
        return categories if categories else None
    
    # Don't parse categories from OpenAI paths
    if path.startswith("/openai"):
        return None
    
    # Fallback to path-based parsing (backwards compatibility)
    if not path or path == "/" or path == "/mcp":
        return None
    
    # Remove leading slash and extract path segments
    path_parts = path.lstrip("/").split("/")
    
    # Handle /mcp root path - category is second segment
    if len(path_parts) >= 2 and path_parts[0] == "mcp" and path_parts[1]:
        return [path_parts[1]]
    
    # Handle direct category path (backwards compatibility)
    if len(path_parts) > 0 and path_parts[0] and path_parts[0] != "mcp":
        return [path_parts[0]]
    
    return None

def estimate_tokens(data: Any) -> int:
    """Estimate the number of tokens in a data structure.
    
    Uses a simple heuristic: ~4 characters per token.
    This is a rough estimate suitable for JSON/text data.
    """
    if isinstance(data, str):
        return len(data) // 4
    elif isinstance(data, (dict, list)):
        json_str = json.dumps(data, separators=(',', ':'))
        return len(json_str) // 4
    else:
        return len(str(data)) // 4

def generate_r2_key(data: str) -> str:
    """Generate a unique R2 key for temporary data storage."""
    data_hash = hashlib.sha256(data.encode()).hexdigest()[:8]
    timestamp = int(time.time())
    return f"alphavantage-responses/{timestamp}-{data_hash}.json"

def upload_to_r2(data: str, bucket_name: str = None) -> str | None:
    """Upload data to Cloudflare R2 and return a public URL.
    
    Args:
        data: The data to upload (as string)
        bucket_name: R2 bucket name (uses environment variable if not provided)
        
    Returns:
        Public URL to access the data, or None if upload fails
    """
    import os
    try:
        import boto3
    except ImportError:
        return None
    
    try:
        # Get bucket name from environment or use default
        bucket = bucket_name or os.environ.get('R2_BUCKET', 'alphavantage-mcp-responses')
        
        # Get R2 public domain from environment
        r2_domain = os.environ.get('R2_PUBLIC_DOMAIN', 'https://data.alphavantage-mcp.com')
        
        # Initialize R2 client using S3-compatible API
        # R2 requires specific endpoint and credentials
        r2_client = boto3.client(
            's3',
            endpoint_url=os.environ.get('R2_ENDPOINT_URL'),
            aws_access_key_id=os.environ.get('R2_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('R2_SECRET_ACCESS_KEY'),
            region_name='auto'
        )
        
        # Generate unique key
        key = generate_r2_key(data)
        
        # Upload to R2 with public access
        r2_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            ContentType='application/json',
            CacheControl='public, max-age=3600',  # 1 hour cache
            Metadata={
                'created': str(int(time.time()))
            }
        )
        
        # Return R2 public URL
        url = f"{r2_domain}/{key}"
        
        return url
    except Exception:
        # If any error occurs during upload, return None to trigger fallback
        return None

def create_oauth_error_response(error_dict: dict, status_code: int = 401) -> dict:
    """Create Lambda-compatible OAuth 2.1 error response.
    
    Args:
        error_dict: OAuth error dictionary from detect_alphavantage_auth_error
        status_code: HTTP status code (401 for auth errors, 429 for rate limits)
        
    Returns:
        Lambda response dict with proper headers and status
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "WWW-Authenticate": f'Bearer error="{error_dict["error"]}", error_description="{error_dict["error_description"]}"',
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(error_dict)
    }

def create_response_preview(data: dict | list, max_items: int = 5) -> dict:
    """Create a preview of the response data.
    
    Args:
        data: The full response data
        max_items: Maximum number of items to include in preview
        
    Returns:
        A preview dictionary with sample data and metadata
    """
    preview = {
        "preview": True,
        "total_size_estimate": estimate_tokens(data),
        "data_type": type(data).__name__
    }
    
    if isinstance(data, dict):
        # For dict, show structure and first few values
        preview["keys"] = list(data.keys())
        preview["sample_data"] = {}
        
        for i, (key, value) in enumerate(data.items()):
            if i >= max_items:
                break
            
            # Handle nested structures
            if isinstance(value, dict):
                preview["sample_data"][key] = {
                    "type": "dict",
                    "keys": list(value.keys())[:5],
                    "size": len(value)
                }
            elif isinstance(value, list):
                preview["sample_data"][key] = {
                    "type": "list",
                    "length": len(value),
                    "first_item": value[0] if value else None
                }
            else:
                preview["sample_data"][key] = value
                
    elif isinstance(data, list):
        # For list, show length and first few items
        preview["length"] = len(data)
        preview["sample_data"] = data[:max_items]
        
    else:
        # For other types, convert to string and truncate
        str_data = str(data)
        preview["sample_data"] = str_data[:1000] + ("..." if len(str_data) > 1000 else "")
    
    return preview