"""Common utility functions shared across modules."""
import json

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