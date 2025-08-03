#!/bin/bash

# AWS SAM deployment script for Streamable HTTP MCP Lambda function

set -e

echo "🚀 Starting deployment of MCP Lambda function..."

# Check if uv is available for faster dependency resolution
if command -v uv &> /dev/null; then
    echo "📦 Using uv for package management..."
    # Export without the editable package for Lambda deployment
    uv export --format=requirements-txt --no-hashes | grep -v "^-e \." > requirements.txt
else
    echo "📦 uv not found, using existing requirements.txt..."
    # Remove editable package line if it exists
    sed -i.bak '/^-e \./d' requirements.txt && rm -f requirements.txt.bak
fi

echo "🏗️  Building SAM application..."
sam build

echo "🚀 Deploying SAM application..."
if [ -f "samconfig.toml" ]; then
    echo "📋 Using existing configuration..."
    sam deploy
else
    echo "📋 Running guided deployment (first time)..."
    sam deploy --guided
fi

echo "✅ Deployment complete!"
echo "🔗 Your MCP server endpoint will be shown above."
echo "📝 Test with: curl -X POST <endpoint-url> -H 'Content-Type: application/json' -d '{\"method\":\"initialize\"}'"