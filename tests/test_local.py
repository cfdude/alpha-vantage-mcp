#!/usr/bin/env python3
"""
MCP client test for Lambda function
Tests the Lambda MCP server using a client-like approach
"""

import json
from lambda_function import lambda_handler
import os

import dotenv

dotenv.load_dotenv()

class MockMCPClient:
    """Mock MCP client that tests Lambda function directly"""
    
    def __init__(self):
        self.request_id = 1
    
    def _call_lambda(self, method: str, params: dict = None) -> dict:
        """Call the Lambda function with MCP-formatted request"""
        body = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
        }
        if params:
            body["params"] = params
        
        self.request_id += 1
        
        # Create Lambda event
        event = {
            "httpMethod": "POST",
            "path": "/mcp",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Authorization": f"Bearer {os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')}"
            },
            "body": json.dumps(body),
            "queryStringParameters": None,
            "isBase64Encoded": False
        }
        
        # Call the Lambda handler
        response = lambda_handler(event, None)
        
        # Parse response
        if response["statusCode"] == 200:
            try:
                return json.loads(response["body"])
            except json.JSONDecodeError as e:
                return {"error": f"Invalid JSON response: {e}"}
        else:
            return {"error": f"HTTP {response['statusCode']}: {response['body']}"}
    
    def initialize(self, client_info: dict = None) -> dict:
        """Initialize MCP connection"""
        params = {
            "protocolVersion": "2025-03-26",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            },
            "clientInfo": client_info or {
                "name": "mcp-lambda-test-client",
                "version": "1.0.0"
            }
        }
        return self._call_lambda("initialize", params)
    
    def list_tools(self) -> dict:
        """List available tools"""
        return self._call_lambda("tools/list")
    
    def call_tool(self, name: str, arguments: dict = None) -> dict:
        """Call a specific tool"""
        params = {
            "name": name,
            "arguments": arguments or {}
        }
        return self._call_lambda("tools/call", params)


def print_test_result(test_name: str, success: bool, response: dict = None, details: str = None):
    """Print formatted test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    
    if details:
        print(f"   {details}")
    
    if response and not success:
        print(f"   Response: {json.dumps(response, indent=4)}")
    elif response and success:
        # Show condensed response for successful tests
        if isinstance(response, dict) and "result" in response:
            result = response["result"]
            if isinstance(result, dict):
                if "tools" in result:
                    tools_count = len(result["tools"])
                    print(f"   Found {tools_count} tools")
                elif "content" in result:
                    print(f"   Tool executed successfully")
                elif "protocolVersion" in result:
                    print(f"   Protocol version: {result['protocolVersion']}")


def test_mcp_client_functionality():
    """Test MCP functionality using client-like patterns"""
    print("🚀 Starting MCP Lambda Client Tests")
    print("=" * 50)
    
    client = MockMCPClient()
    results = []
    
    # Test 1: Initialize
    print("\n🔧 Testing MCP Initialize...")
    try:
        response = client.initialize()
        success = (
            "error" not in response and
            "result" in response and
            "protocolVersion" in response.get("result", {})
        )
        print_test_result("Initialize", success, response)
        results.append(success)
    except Exception as e:
        print_test_result("Initialize", False, details=f"Exception: {e}")
        results.append(False)
    
    # Test 2: List Tools
    print("\n🔨 Testing List Tools...")
    try:
        response = client.list_tools()
        success = (
            "error" not in response and
            "result" in response and
            "tools" in response.get("result", {})
        )
        tools = response.get("result", {}).get("tools", [])
        tool_names = [tool.get("name", "unknown") for tool in tools]
        details = f"Available tools: {', '.join(tool_names)}" if tool_names else "No tools found"
        
        print_test_result("List Tools", success, response, details)
        results.append(success)
    except Exception as e:
        print_test_result("List Tools", False, details=f"Exception: {e}")
        results.append(False)
    
    # Test 3: Add Two Numbers
    print("\n🔢 Testing Add Two Numbers...")
    try:
        response = client.call_tool("ADD_TWO_NUMBERS", {"a": 5, "b": 3})
        success = (
            "error" not in response and
            "result" in response and
            "content" in response.get("result", {})
        )
        
        if success:
            content = response.get("result", {}).get("content", [])
            if content and len(content) > 0:
                result_text = content[0].get("text", "")
                details = f"5 + 3 = {result_text}"
            else:
                details = "Addition completed successfully"
        else:
            details = "Failed to add numbers"
        
        print_test_result("Add Two Numbers", success, response, details)
        results.append(success)
    except Exception as e:
        print_test_result("Add Two Numbers", False, details=f"Exception: {e}")
        results.append(False)
    
    # Test 4: Get Stock Quote for AAPL
    print("\n📈 Testing Get Stock Quote (AAPL)...")
    try:
        response = client.call_tool("GLOBAL_QUOTE", {"symbol": "AAPL"})
        success = (
            "error" not in response and
            "result" in response and
            "content" in response.get("result", {})
        )
        
        if success:
            content = response.get("result", {}).get("content", [])
            if content and len(content) > 0:
                text_content = content[0].get("text", "")
                details = f"Retrieved AAPL quote data (length: {len(text_content)} chars)"
                print(f"   {text_content[:100]}...")  # Print first 100 chars
            else:
                details = "Quote retrieved successfully"
        else:
            details = "Failed to get stock quote"
        
        print_test_result("Get Stock Quote (AAPL)", success, response, details)
        results.append(success)
    except Exception as e:
        print_test_result("Get Stock Quote (AAPL)", False, details=f"Exception: {e}")
        results.append(False)
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 TEST SUMMARY")
    print(f"{'='*50}")
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! Your MCP Lambda server is working perfectly with client patterns.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")
        
    return passed == total


def print_time_series_daily_adjusted_schema():
    """Print the tool schema for REALTIME_OPTIONS"""
    client = MockMCPClient()
    
    # Initialize the client first
    init_response = client.initialize()
    if "error" in init_response:
        print(f"❌ Failed to initialize: {init_response}")
        return
    
    # Get list of tools
    tools_response = client.list_tools()
    if "error" in tools_response:
        print(f"❌ Failed to get tools: {tools_response}")
        return
    
    tools = tools_response.get("result", {}).get("tools", [])
    
    # Find REALTIME_OPTIONS tool
    target_tool = None
    for tool in tools:
        if tool.get("name") == "REALTIME_OPTIONS":
            target_tool = tool
            break
    
    if target_tool:
        print("📋 Tool Schema for REALTIME_OPTIONS:")
        print("=" * 60)
        print(json.dumps(target_tool, indent=2))
    else:
        print("❌ REALTIME_OPTIONS tool not found")
        print(f"Available tools: {[tool.get('name') for tool in tools]}")


def main():
    """Run the MCP client tests"""
    print_time_series_daily_adjusted_schema()
    return True


if __name__ == "__main__":
    main()