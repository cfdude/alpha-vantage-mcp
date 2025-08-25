#!/bin/bash

# Script to configure CloudFront to S3 access with Origin Access Control (OAC)
AWS_PROFILE=${AWS_PROFILE:-default}

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

set -e

echo "🔧 Configuring CloudFront to S3 access..."

# Check required environment variables
if [ -z "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    echo "❌ Error: CLOUDFRONT_DISTRIBUTION_ID not found in .env"
    exit 1
fi

STATIC_FILES_BUCKET=${STATIC_FILES_BUCKET:-alphavantage-mcp-web}
echo "🪣 Using S3 bucket: $STATIC_FILES_BUCKET"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text)
echo "📋 AWS Account ID: $AWS_ACCOUNT_ID"

# Step 1: Create Origin Access Control (OAC)
echo "🔐 Creating Origin Access Control..."
OAC_ID=$(aws cloudfront create-origin-access-control \
    --profile $AWS_PROFILE \
    --origin-access-control-config \
    "Name=alphavantage-mcp-oac,Description=OAC for MCP static files,OriginAccessControlOriginType=s3,SigningBehavior=always,SigningProtocol=sigv4" \
    --query 'OriginAccessControl.Id' \
    --output text 2>/dev/null || echo "")

if [ -z "$OAC_ID" ]; then
    echo "⚠️  OAC might already exist, listing existing OACs..."
    aws cloudfront list-origin-access-controls --profile $AWS_PROFILE --query 'OriginAccessControlList.Items[?Name==`alphavantage-mcp-oac`].Id' --output text
else
    echo "✅ Created OAC with ID: $OAC_ID"
fi

# Step 2: Create S3 bucket policy
echo "📄 Creating S3 bucket policy..."
cat > /tmp/bucket-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipal",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::${STATIC_FILES_BUCKET}/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::${AWS_ACCOUNT_ID}:distribution/${CLOUDFRONT_DISTRIBUTION_ID}"
        }
      }
    }
  ]
}
EOF

echo "🔒 Applying S3 bucket policy..."
aws s3api put-bucket-policy \
    --profile $AWS_PROFILE \
    --bucket $STATIC_FILES_BUCKET \
    --policy file:///tmp/bucket-policy.json

# Step 3: Block public access (security best practice)
echo "🔐 Blocking public access to S3 bucket..."
aws s3api put-public-access-block \
    --profile $AWS_PROFILE \
    --bucket $STATIC_FILES_BUCKET \
    --public-access-block-configuration \
    'BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true'

# Clean up temporary file
rm /tmp/bucket-policy.json

echo "✅ CloudFront to S3 configuration complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Update your CloudFront distribution to use the OAC (if not already configured)"
echo "   2. Test static file access through CloudFront"
echo "   3. Verify S3 direct access is blocked"
echo ""
echo "🔗 CloudFront Distribution ID: $CLOUDFRONT_DISTRIBUTION_ID"
echo "🪣 S3 Bucket: $STATIC_FILES_BUCKET"