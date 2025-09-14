#!/bin/bash

# Create IAM role for Kinesis Data Firehose
# This script creates the necessary IAM role and policy for Firehose delivery stream

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

set -e

# Set AWS profile options if specified
AWS_PROFILE_OPTION=""
if [ ! -z "$AWS_PROFILE" ]; then
    AWS_PROFILE_OPTION="--profile $AWS_PROFILE"
    echo "Using AWS profile: $AWS_PROFILE"
fi

# Get AWS account ID and region
ACCOUNT_ID=$(aws sts get-caller-identity $AWS_PROFILE_OPTION --query Account --output text)
REGION=$(aws configure get region $AWS_PROFILE_OPTION || echo "us-east-1")

echo "🔑 Creating IAM role for Kinesis Data Firehose..."
echo "Account ID: $ACCOUNT_ID"
echo "Region: $REGION"
echo ""

FIREHOSE_ROLE_NAME="KinesisFirehoseDeliveryRole-mcp"
FIREHOSE_POLICY_ARN="arn:aws:iam::aws:policy/AmazonKinesisFirehoseFullAccess"
CLOUDWATCH_POLICY_ARN="arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
LAMBDA_POLICY_ARN="arn:aws:iam::aws:policy/service-role/AWSLambdaRole"
S3_POLICY_ARN="arn:aws:iam::aws:policy/AmazonS3FullAccess"

# Check for existing role
echo "Checking for existing role..."
EXISTING_ROLE=$(aws iam get-role $AWS_PROFILE_OPTION --role-name "$FIREHOSE_ROLE_NAME" --query "Role.Arn" --output text 2>/dev/null || echo "")

if [ ! -z "$EXISTING_ROLE" ] && [ "$EXISTING_ROLE" != "None" ]; then
    echo "Found existing role:"
    echo "Role ARN: $EXISTING_ROLE"
    
    # Check if policies are attached
    echo "Checking policy attachments..."
    FIREHOSE_POLICY_ATTACHED=$(aws iam list-attached-role-policies $AWS_PROFILE_OPTION --role-name "$FIREHOSE_ROLE_NAME" --query "AttachedPolicies[?PolicyArn=='$FIREHOSE_POLICY_ARN'].PolicyArn" --output text 2>/dev/null || echo "")
    CLOUDWATCH_POLICY_ATTACHED=$(aws iam list-attached-role-policies $AWS_PROFILE_OPTION --role-name "$FIREHOSE_ROLE_NAME" --query "AttachedPolicies[?PolicyArn=='$CLOUDWATCH_POLICY_ARN'].PolicyArn" --output text 2>/dev/null || echo "")
    LAMBDA_POLICY_ATTACHED=$(aws iam list-attached-role-policies $AWS_PROFILE_OPTION --role-name "$FIREHOSE_ROLE_NAME" --query "AttachedPolicies[?PolicyArn=='$LAMBDA_POLICY_ARN'].PolicyArn" --output text 2>/dev/null || echo "")
    S3_POLICY_ATTACHED=$(aws iam list-attached-role-policies $AWS_PROFILE_OPTION --role-name "$FIREHOSE_ROLE_NAME" --query "AttachedPolicies[?PolicyArn=='$S3_POLICY_ARN'].PolicyArn" --output text 2>/dev/null || echo "")
    
    if [ ! -z "$FIREHOSE_POLICY_ATTACHED" ] && [ ! -z "$CLOUDWATCH_POLICY_ATTACHED" ] && [ ! -z "$LAMBDA_POLICY_ATTACHED" ] && [ ! -z "$S3_POLICY_ATTACHED" ]; then
        echo "✅ Role already exists with all policies attached!"
        echo "Role ARN: $EXISTING_ROLE"
        echo ""
        echo "This role provides:"
        echo "- Kinesis Data Firehose full access"
        echo "- S3 full access for delivery streams"
        echo "- CloudWatch Logs full access"
        echo "- Lambda execution permissions"
        echo ""
        echo "Role is ready to use in your Firehose delivery streams."
        exit 0
    else
        echo "Role exists but some policies not attached. Attaching missing policies..."
        if [ -z "$FIREHOSE_POLICY_ATTACHED" ]; then
            aws iam attach-role-policy $AWS_PROFILE_OPTION --role-name "$FIREHOSE_ROLE_NAME" --policy-arn "$FIREHOSE_POLICY_ARN"
            echo "✅ AmazonKinesisFirehoseFullAccess attached!"
        fi
        if [ -z "$CLOUDWATCH_POLICY_ATTACHED" ]; then
            aws iam attach-role-policy $AWS_PROFILE_OPTION --role-name "$FIREHOSE_ROLE_NAME" --policy-arn "$CLOUDWATCH_POLICY_ARN"
            echo "✅ CloudWatchLogsFullAccess policy attached!"
        fi
        if [ -z "$LAMBDA_POLICY_ATTACHED" ]; then
            aws iam attach-role-policy $AWS_PROFILE_OPTION --role-name "$FIREHOSE_ROLE_NAME" --policy-arn "$LAMBDA_POLICY_ARN"
            echo "✅ AWSLambdaRole policy attached!"
        fi
        if [ -z "$S3_POLICY_ATTACHED" ]; then
            aws iam attach-role-policy $AWS_PROFILE_OPTION --role-name "$FIREHOSE_ROLE_NAME" --policy-arn "$S3_POLICY_ARN"
            echo "✅ AmazonS3FullAccess policy attached!"
        fi
        echo "Role ARN: $EXISTING_ROLE"
        echo ""
        echo "This role provides:"
        echo "- Kinesis Data Firehose full access"
        echo "- S3 full access for delivery streams"
        echo "- CloudWatch Logs full access"
        echo "- Lambda execution permissions"
        echo ""
        echo "Role is ready to use in your Firehose delivery streams."
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
        "Service": "firehose.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

# Create role (ignore if it already exists)
if FIREHOSE_ROLE_ARN=$(aws iam create-role $AWS_PROFILE_OPTION \
    --role-name "$FIREHOSE_ROLE_NAME" \
    --assume-role-policy-document "$TRUST_POLICY" \
    --query "Role.Arn" \
    --output text 2>/dev/null); then
    echo "Role created successfully!"
    echo "Role ARN: $FIREHOSE_ROLE_ARN"
else
    echo "Role already exists, continuing with policy attachment..."
    # Construct the expected ARN format
    FIREHOSE_ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$FIREHOSE_ROLE_NAME"
    echo "Using role ARN: $FIREHOSE_ROLE_ARN"
fi
echo ""

# Attach managed policies to role
echo "📎 Attaching managed policies..."

# Attach Kinesis Data Firehose delivery role policy
echo "Attaching AmazonKinesisFirehoseFullAccess..."
aws iam attach-role-policy $AWS_PROFILE_OPTION \
    --role-name "$FIREHOSE_ROLE_NAME" \
    --policy-arn "$FIREHOSE_POLICY_ARN"

# Attach CloudWatch Logs full access for logging
echo "Attaching CloudWatchLogsFullAccess policy..."
aws iam attach-role-policy $AWS_PROFILE_OPTION \
    --role-name "$FIREHOSE_ROLE_NAME" \
    --policy-arn "$CLOUDWATCH_POLICY_ARN"

# Attach Lambda role for Lambda function invocation
echo "Attaching AWSLambdaRole policy..."
aws iam attach-role-policy $AWS_PROFILE_OPTION \
    --role-name "$FIREHOSE_ROLE_NAME" \
    --policy-arn "$LAMBDA_POLICY_ARN"

# Attach S3 full access for S3 delivery
echo "Attaching AmazonS3FullAccess policy..."
aws iam attach-role-policy $AWS_PROFILE_OPTION \
    --role-name "$FIREHOSE_ROLE_NAME" \
    --policy-arn "$S3_POLICY_ARN"

echo "✅ Firehose IAM role setup complete!"
echo "Role ARN: $FIREHOSE_ROLE_ARN"
echo ""
echo "This role provides:"
echo "- Kinesis Data Firehose full access"
echo "- S3 full access for delivery streams"
echo "- CloudWatch Logs full access"
echo ""
echo "Role is ready to use in your Firehose delivery streams and CloudFormation templates."