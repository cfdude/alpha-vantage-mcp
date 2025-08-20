#!/usr/bin/env python3
"""Test script for OpenAI schema generation."""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.openai_actions import generate_openapi_schema, execute_tool
from lambda_function import lambda_handler

def test_schema_generation():
    """Test generating the OpenAPI schema."""
    print("Testing OpenAPI schema generation...")
    schema = generate_openapi_schema()
    
    # Pretty print the schema
    print(json.dumps(schema, indent=2))
    
    # Verify schema structure
    assert "openapi" in schema
    assert "paths" in schema
    assert "info" in schema
    
    # Check that we have some paths
    assert len(schema["paths"]) > 0
    
    # Check a specific tool exists (function names are uppercased)
    assert "/openai/PING" in schema["paths"]
    assert "/openai/ADD_TWO_NUMBERS" in schema["paths"]
    
    # Check that all descriptions are within 300 character limit
    print("\nChecking description lengths...")
    exceeded_limit = []
    for path, methods in schema["paths"].items():
        for method, details in methods.items():
            if "description" in details:
                desc_len = len(details["description"])
                if desc_len > 300:
                    exceeded_limit.append(f"Path {path}, method {method}: {desc_len} chars")
    
    if exceeded_limit:
        print("❌ Descriptions exceeding 300 character limit:")
        for item in exceeded_limit:
            print(f"  {item}")
        assert False, f"{len(exceeded_limit)} descriptions exceed 300 character limit"
    else:
        print("✓ All descriptions are within 300 character limit")
    
    print(f"\n✓ Schema generated successfully with {len(schema['paths'])} endpoints")
    return schema

def test_tool_execution():
    """Test executing tools directly."""
    print("\nTesting tool execution...")
    
    # Test ping
    result = execute_tool("ping", {})
    assert result == "pong"
    print("✓ ping() returned:", result)
    
    # Test add_two_numbers
    result = execute_tool("add_two_numbers", {"a": 5, "b": 3})
    assert result == 8
    print("✓ add_two_numbers(5, 3) returned:", result)
    
    print("✓ Tool execution working correctly")

def test_category_filtering():
    """Test category-based tool filtering."""
    print("\nTesting category filtering...")
    
    # Test schema with specific category
    schema_all = generate_openapi_schema()
    all_tools_count = len(schema_all["paths"])
    print(f"  Total tools available: {all_tools_count}")
    
    # Test filtering by category (using "core_stock_apis" as example)
    schema_stocks = generate_openapi_schema(categories=["core_stock_apis"])
    stocks_tools_count = len(schema_stocks["paths"])
    print(f"  Tools in 'core_stock_apis' category: {stocks_tools_count}")
    
    # Verify filtering worked
    assert stocks_tools_count <= all_tools_count
    assert stocks_tools_count > 0  # Should have at least some tools
    print("✓ Category filtering reduces available tools")
    
    # Test multiple categories
    schema_multi = generate_openapi_schema(categories=["core_stock_apis", "forex"])
    multi_tools_count = len(schema_multi["paths"])
    print(f"  Tools in 'core_stock_apis' + 'forex' categories: {multi_tools_count}")
    
    # Verify combined categories have more tools than single category
    assert multi_tools_count >= stocks_tools_count
    
    # Test with just ping category to verify small result set
    schema_ping = generate_openapi_schema(categories=["ping"])
    ping_tools_count = len(schema_ping["paths"])
    print(f"  Tools in 'ping' category: {ping_tools_count}")
    assert ping_tools_count == 2  # Should only have ping and add_two_numbers
    
    print("✓ Category filtering working correctly")

def test_lambda_handler():
    """Test the Lambda handler."""
    print("\nTesting Lambda handler...")
    
    # Test GET /openai - should return schema
    event = {
        "path": "/openai",
        "httpMethod": "GET",
        "headers": {},
        "requestContext": {
            "domainName": "api.example.com",
            "stage": "prod"
        }
    }
    
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    schema = json.loads(response["body"])
    assert "openapi" in schema
    print("✓ GET /openai returns schema")
    
    # Test GET /openai with categories query parameter
    event = {
        "path": "/openai",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {
            "categories": "core_stock_apis"
        },
        "requestContext": {
            "domainName": "api.example.com",
            "stage": "prod"
        }
    }
    
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    schema_filtered = json.loads(response["body"])
    assert "openapi" in schema_filtered
    assert len(schema_filtered["paths"]) <= len(schema["paths"])
    print("✓ GET /openai with categories filter returns filtered schema")
    
    # Test POST /openai/PING (uppercase function names)
    event = {
        "path": "/openai/PING",
        "httpMethod": "POST",
        "headers": {},
        "body": "{}"
    }
    
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["result"] == "pong"
    print("✓ POST /openai/PING returns correct result")
    
    # Test POST /openai/ADD_TWO_NUMBERS
    event = {
        "path": "/openai/ADD_TWO_NUMBERS",
        "httpMethod": "POST",
        "headers": {},
        "body": json.dumps({"a": 10, "b": 20})
    }
    
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["result"] == "30"
    print("✓ POST /openai/ADD_TWO_NUMBERS returns correct result")
    
    # Test invalid function
    event = {
        "path": "/openai/nonexistent_function",
        "httpMethod": "POST",
        "headers": {},
        "body": "{}"
    }
    
    response = lambda_handler(event, None)
    assert response["statusCode"] == 404
    print("✓ Invalid function returns 404")
    
    # Test OPTIONS for CORS
    event = {
        "path": "/openai",
        "httpMethod": "OPTIONS",
        "headers": {}
    }
    
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    assert "Access-Control-Allow-Origin" in response["headers"]
    print("✓ OPTIONS request handled for CORS")
    
    print("✓ Lambda handler working correctly")

def main():
    """Run all tests."""
    print("=" * 60)
    print("OpenAI Schema Generator Tests")
    print("=" * 60)
    
    try:
        # Run tests
        schema = test_schema_generation()
        test_tool_execution()
        test_category_filtering()
        test_lambda_handler()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✅")
        print("=" * 60)
        
        # Print sample endpoint info
        print("\nSample endpoints generated:")
        for path in list(schema["paths"].keys())[:5]:
            print(f"  • {path}")
        if len(schema["paths"]) > 5:
            print(f"  ... and {len(schema['paths']) - 5} more")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    main()