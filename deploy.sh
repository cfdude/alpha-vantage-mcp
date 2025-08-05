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
    PARAM_OVERRIDES=""
    if [ -n "$CERTIFICATE_ARN" ]; then
        PARAM_OVERRIDES="CertificateArn=$CERTIFICATE_ARN"
    fi
    if [ -n "$DOMAIN_NAME" ]; then
        if [ -n "$PARAM_OVERRIDES" ]; then
            PARAM_OVERRIDES="$PARAM_OVERRIDES DomainName=$DOMAIN_NAME"
        else
            PARAM_OVERRIDES="DomainName=$DOMAIN_NAME"
        fi
    fi
    if [ -n "$PARAM_OVERRIDES" ]; then
        sam deploy --profile $AWS_PROFILE --parameter-overrides $PARAM_OVERRIDES
    else
        sam deploy --profile $AWS_PROFILE
    fi
else
    echo "📋 Running guided deployment (first time)..."
    sam deploy --guided --profile $AWS_PROFILE
fi

echo "✅ Deployment complete!"
echo "🔗 Your MCP server endpoint will be shown above."
echo "📝 Test with: curl -X POST <endpoint-url> -H 'Content-Type: application/json' -d '{\"method\":\"initialize\"}'"