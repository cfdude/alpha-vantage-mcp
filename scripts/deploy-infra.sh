#!/bin/bash

# AWS SAM deployment script for Streamable HTTP MCP Lambda function
AWS_PROFILE=${AWS_PROFILE:-default}

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

set -e

echo "🚀 Starting deployment of MCP Lambda function..."

# Check if uv is available for dependency resolution (required)
if command -v uv &> /dev/null; then
    echo "📦 Using uv for package management..."
    # Export without the editable package for Lambda deployment
    uv export --format=requirements-txt --no-hashes | grep -v "^-e \." > requirements.txt
else
    echo "❌ Error: uv is required for deployment but not found in PATH"
    echo "Please install uv: https://github.com/astral-sh/uv"
    exit 1
fi

echo "🏗️  Building SAM application..."
sam build --template infra/infra.yaml

# Function to add parameter overrides
add_param() {
    local param_name="$1"
    local env_var="$2"
    if [ -n "${!env_var}" ]; then
        if [ -n "$PARAM_OVERRIDES" ]; then
            PARAM_OVERRIDES="$PARAM_OVERRIDES $param_name=${!env_var}"
        else
            PARAM_OVERRIDES="$param_name=${!env_var}"
        fi
    fi
}

echo "🚀 Deploying SAM application..."
if [ -f "infra/samconfig-infra.toml" ]; then
    echo "📋 Using infrastructure-specific configuration..."
    PARAM_OVERRIDES=""
    
    # Add parameters if environment variables are set
    add_param "StackName" "STACK_NAME"
    
    # If STACK_NAME not set, use the default from samconfig
    if [ -z "$STACK_NAME" ]; then
        STACK_NAME="alphavantage-mcp-server-infra"
        add_param "StackName" "STACK_NAME"
    fi
    
    if [ -n "$PARAM_OVERRIDES" ]; then
        sam deploy --template infra/infra.yaml --config-file $(pwd)/infra/samconfig-infra.toml --profile $AWS_PROFILE --parameter-overrides $PARAM_OVERRIDES
    else
        sam deploy --template infra/infra.yaml --config-file $(pwd)/infra/samconfig-infra.toml --profile $AWS_PROFILE
    fi
else
    echo "📋 Running guided deployment (first time)..."
    sam deploy --template infra/infra.yaml --guided --profile $AWS_PROFILE
fi

echo "✅ Deployment complete!"
echo "🔗 Your MCP server endpoint will be shown above."
echo "📝 Test with: curl -X POST <endpoint-url> -H 'Content-Type: application/json' -d '{\"method\":\"initialize\"}'"