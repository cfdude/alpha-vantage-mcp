#!/bin/bash

# Deploy static files to S3 bucket
# Usage: ./deploy-static.sh <bucket-name>
AWS_PROFILE=${AWS_PROFILE:-default}

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$1" ]; then
    BUCKET_NAME="alphavantage-mcp-static-files"
    echo "Using default bucket: $BUCKET_NAME"
else
    BUCKET_NAME=$1
fi
STATIC_DIR="web/out"

if [ ! -d "$STATIC_DIR" ]; then
    echo "Error: Static files directory '$STATIC_DIR' not found"
    echo "Please run 'npm run build' in the web directory first"
    exit 1
fi

echo "Deploying static files to S3 bucket: $BUCKET_NAME"

# Sync files to S3 with appropriate cache headers
aws s3 sync "$STATIC_DIR" "s3://$BUCKET_NAME" \
    --profile $AWS_PROFILE \
    --delete \
    --cache-control "public, max-age=31536000" \
    --exclude "*.html" \
    --exclude "*.txt" \
    --exclude "*.xml"

# Upload HTML files with shorter cache duration
aws s3 sync "$STATIC_DIR" "s3://$BUCKET_NAME" \
    --profile $AWS_PROFILE \
    --delete \
    --cache-control "public, max-age=3600" \
    --include "*.html" \
    --include "*.txt" \
    --include "*.xml"

echo "Static files deployed successfully!"

# Invalidate CloudFront cache if distribution ID is provided
if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    echo "🔄 Invalidating CloudFront cache..."
    aws cloudfront create-invalidation \
        --profile $AWS_PROFILE \
        --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
        --paths "/*" \
        --no-cli-pager
    echo "✅ CloudFront cache invalidation started"
else
    echo "⚠️  CLOUDFRONT_DISTRIBUTION_ID not set - skipping cache invalidation"
fi

echo ""
echo "Don't forget to:"
echo "1. Point your DNS to the CloudFront distribution domain"
echo "2. Set CLOUDFRONT_DISTRIBUTION_ID in .env for automatic cache invalidation"