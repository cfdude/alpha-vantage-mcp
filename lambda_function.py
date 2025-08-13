from awslabs.mcp_lambda_handler import MCPLambdaHandler
from loguru import logger
from src.context import set_api_key
from src.decorators import setup_custom_tool_decorator
from src.tools.registry import register_all_tools, register_tools_by_categories
from src.openai_actions import handle_openai_request
from src.utils import parse_token_from_request, parse_tool_categories_from_request, create_oauth_error_response
from src.oauth import handle_metadata_discovery, handle_authorization_request, handle_token_request, handle_registration_request

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
    path = event.get("path", "/")
    
    # Handle OAuth 2.1 endpoints first
    if path == "/.well-known/oauth-authorization-server":
        return handle_metadata_discovery(event)
    elif path == "/authorize":
        return handle_authorization_request(event)
    elif path == "/token":
        return handle_token_request(event)
    elif path == "/register":
        return handle_registration_request(event)
    
    # Extract Bearer token from Authorization header
    token = parse_token_from_request(event)
    
    # Validate token presence for MCP/API requests
    if not token:
        return create_oauth_error_response({
            "error": "invalid_request",
            "error_description": "Missing access token",
            "error_uri": "https://tools.ietf.org/html/rfc6750#section-3.1"
        }, 401)
    
    # Set token in context for tools to access
    set_api_key(token)
    
    # Parse tool categories from request path or query parameters
    categories = parse_tool_categories_from_request(event)
    
    # Check if this is an OpenAI Actions request
    if path.startswith("/openai"):
        response = handle_openai_request(event, categories)
        if response:
            return response
    
    # Handle MCP requests
    
    # Create MCP handler with appropriate tools
    mcp = create_mcp_handler_for_categories(categories)
    
    return mcp.handle_request(event, context)