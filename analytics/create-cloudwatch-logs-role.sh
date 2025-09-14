#!/bin/bash

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

set -e

ROLE_NAME="CloudWatchLogsRole-mcp"
POLICY_ARN="arn:aws:iam::aws:policy/AmazonKinesisFirehoseFullAccess"

# Set AWS profile options if specified
AWS_PROFILE_OPTION=""
if [ ! -z "$AWS_PROFILE" ]; then
    AWS_PROFILE_OPTION="--profile $AWS_PROFILE"
    echo "Using AWS profile: $AWS_PROFILE"
fi

echo "Managing CloudWatch Logs role: $ROLE_NAME"
echo ""

# Check for existing role
echo "Checking for existing role..."
EXISTING_ROLE=$(aws iam get-role $AWS_PROFILE_OPTION --role-name "$ROLE_NAME" --query "Role.Arn" --output text 2>/dev/null || echo "")

if [ ! -z "$EXISTING_ROLE" ] && [ "$EXISTING_ROLE" != "None" ]; then
    echo "Found existing role:"
    echo "Role ARN: $EXISTING_ROLE"
    
    # Check if policy is attached
    echo "Checking policy attachments..."
    POLICY_ATTACHED=$(aws iam list-attached-role-policies $AWS_PROFILE_OPTION --role-name "$ROLE_NAME" --query "AttachedPolicies[?PolicyArn=='$POLICY_ARN'].PolicyArn" --output text 2>/dev/null || echo "")
    
    if [ ! -z "$POLICY_ATTACHED" ]; then
        echo "✅ Role already exists with policy attached!"
        echo "Role ARN: $EXISTING_ROLE"
        exit 0
    else
        echo "Role exists but policy not attached. Attaching policy..."
        aws iam attach-role-policy $AWS_PROFILE_OPTION --role-name "$ROLE_NAME" --policy-arn "$POLICY_ARN"
        echo "✅ AmazonKinesisFirehoseFullAccess policy attached!"
        echo "Role ARN: $EXISTING_ROLE"
        exit 0
    fi
fi

echo "No existing role found. Creating new role..."

# Trust policy document
TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "logs.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

# Create role (ignore if it already exists)
if ROLE_ARN=$(aws iam create-role $AWS_PROFILE_OPTION \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document "$TRUST_POLICY" \
    --query "Role.Arn" \
    --output text 2>/dev/null); then
    echo "Role created successfully!"
    echo "Role ARN: $ROLE_ARN"
else
    echo "Role already exists, continuing with policy attachment..."
    # Construct the expected ARN format
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity $AWS_PROFILE_OPTION --query "Account" --output text)
    ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ROLE_NAME}"
    echo "Using role ARN: $ROLE_ARN"
fi
echo ""

# Attach policy
echo "Attaching AmazonKinesisFirehoseFullAccess policy..."
aws iam attach-role-policy $AWS_PROFILE_OPTION \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN"

echo "✅ CloudWatch Logs role setup complete!"
echo "Role ARN: $ROLE_ARN"
echo ""
echo "This role provides:"
echo "- CloudWatch Logs service trust relationship"
echo "- AmazonKinesisFirehoseFullAccess managed policy"
echo ""
echo "Role is ready to use for subscription filters."