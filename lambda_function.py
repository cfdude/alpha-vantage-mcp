from awslabs.mcp_lambda_handler import MCPLambdaHandler
from loguru import logger
from src.context import set_api_key
from src.decorators import setup_custom_tool_decorator
from src.tools.registry import register_all_tools, register_tools_by_categories

def parse_token_from_request(event: dict) -> str:
    """Parse API key from query params or Authorization header. Query param takes priority."""
    # Check query parameters first (higher priority)
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

def create_mcp_handler_for_categories(categories: list[str] | None) -> MCPLambdaHandler:
    """Create and configure MCP handler for specific tool categories."""
    mcp = MCPLambdaHandler(name="mcp-lambda-server", version="1.0.0")
    
    # Set up custom tool decorator
    setup_custom_tool_decorator(mcp)
    
    # Register tools based on categories
    if categories:
        logger.info(f"Registering tools for categories: {', '.join(categories)}")
        try:
            register_tools_by_categories(mcp, categories)
        except ValueError as e:
            logger.warning(f"Error with categories {categories}: {e}, registering all tools")
            register_all_tools(mcp)
    else:
        logger.info("Registering all tools")
        register_all_tools(mcp)
    
    return mcp

def lambda_handler(event, context):
    """AWS Lambda handler function."""
    # Extract Bearer token from Authorization header
    token = parse_token_from_request(event)
    
    # Set token in context for tools to access
    if token:
        set_api_key(token)
    
    # Parse tool categories from request path or query parameters
    categories = parse_tool_categories_from_request(event)
    
    # Create MCP handler with appropriate tools
    mcp = create_mcp_handler_for_categories(categories)
    
    return mcp.handle_request(event, context)