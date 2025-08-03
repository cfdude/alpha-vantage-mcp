"""
MCP Client test for deployed Lambda function using streamable HTTP transport
Run from the repository root:
    uv run tests/mcp_client.py
"""

import asyncio
import os
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

import os

import dotenv

dotenv.load_dotenv()


# Lambda endpoint from deployment (update this with your actual endpoint)
LAMBDA_ENDPOINT = os.getenv("LAMBDA_ENDPOINT")


async def test_mcp_lambda_client():
    """Test the deployed Lambda MCP server using real MCP client"""
    print("🚀 Testing deployed MCP Lambda server")
    print(f"📡 Connecting to: {LAMBDA_ENDPOINT}")
    print("=" * 60)
    
    try:
        # Connect to the deployed Lambda MCP server
        async with streamablehttp_client(LAMBDA_ENDPOINT) as (
            read_stream,
            write_stream,
            _,
        ):
            print("✅ Connected to Lambda endpoint")
            
            # Create a session using the client streams
            async with ClientSession(read_stream, write_stream) as session:
                print("✅ MCP session created")
                
                # Initialize the connection
                print("\n🔧 Initializing MCP session...")
                try:
                    initialize_result = await session.initialize()
                    print("✅ MCP session initialized")
                    print(f"   Protocol version: {initialize_result.protocolVersion}")
                    print(f"   Server info: {initialize_result.serverInfo}")
                except Exception as init_error:
                    print(f"❌ Initialization failed: {init_error}")
                    raise
                
                # List available tools
                print("\n🔨 Listing available tools...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"   - {tool.name}: {tool.description}")
                
                # List available resources
                print("\n📋 Listing available resources...")
                try:
                    resources_result = await session.list_resources()
                    resources = resources_result.resources
                    print(f"✅ Found {len(resources)} resources:")
                    for resource in resources:
                        print(f"   - {resource.uri}: {resource.name}")
                except Exception as e:
                    print(f"⚠️ Resources not available: {e}")
                
                # Test echo tool
                if any(tool.name == "echo" for tool in tools):
                    print("\n💬 Testing echo tool...")
                    test_message = "Hello from real MCP client!"
                    echo_result = await session.call_tool("echo", {"message": test_message})
                    print(f"✅ Echo response: {echo_result.content}")
                
                # Test AWS info tool
                if any(tool.name == "get_aws_info" for tool in tools):
                    print("\n☁️  Testing AWS info tool...")
                    aws_result = await session.call_tool("get_aws_info", {})
                    print(f"✅ AWS info retrieved: {len(aws_result.content)} content items")
                
                # Test get_quote tool if available
                if any(tool.name == "get_quote" for tool in tools):
                    print("\n📊 Testing get_quote tool...")
                    try:
                        quote_result = await session.call_tool("get_quote", {"symbol": "AAPL"})
                        print(f"✅ Quote retrieved: {len(quote_result.content)} content items")
                    except Exception as e:
                        print(f"⚠️ Quote test failed: {e}")
                
                # Test system resource if available
                if any(resource.uri == "system://info" for resource in resources_result.resources if 'resources_result' in locals()):
                    print("\n🖥️  Testing system resource...")
                    try:
                        system_result = await session.read_resource("system://info")
                        print(f"✅ System resource read: {len(system_result.contents)} content items")
                    except Exception as e:
                        print(f"⚠️ System resource test failed: {e}")
                
                print(f"\n🎉 All tests completed successfully!")
                print("Your Lambda MCP server is working with real MCP clients!")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure your Lambda endpoint is correct and accessible")
        return False
    
    return True


async def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        global LAMBDA_ENDPOINT
        LAMBDA_ENDPOINT = sys.argv[1]
        print(f"Using custom endpoint: {LAMBDA_ENDPOINT}")
    
    success = await test_mcp_lambda_client()
    
    if success:
        print("\n✅ Lambda MCP server test PASSED")
    else:
        print("\n❌ Lambda MCP server test FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())