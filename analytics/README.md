# Log Analytics Pipeline

Set up autonomous log analytics for your Alpha Vantage MCP server deployment.

## Setup Steps

Run these scripts in order to set up the complete pipeline:

1. **Create IAM role for Kinesis Data Firehose:**
   ```bash
   ./create-firehose-role.sh
   ```

2. **Create basic Lambda execution role (if needed):**
   ```bash
   ./create-basic-lambda-role.sh
   ```

3. **Create CloudWatch Logs role (if using subscription filters):**
   ```bash
   ./create-cloudwatch-logs-role.sh
   ```

4. **Deploy the analytics infrastructure:**
   ```bash
   ./deploy-analytics.sh
   ```

5. **Set up Glue tables for querying:**
   ```bash
   ./setup-glue-tables.sh
   ```

6. **Query analytics data:**
   ```bash
   ./query-athena.sh
   ```

## Environment Configuration

The scripts use the following environment variables (can be set in `.env` file):

- `STACK_NAME` - CloudFormation stack name (default: `alphavantage-mcp-server`)
- `ANALYTICS_LOGS_BUCKET` - S3 bucket for analytics logs (default: `alphavantage-mcp-analytics-logs`)
- `FIREHOSE_ROLE_ARN` - ARN of the Firehose IAM role (set by create-firehose-role.sh)
- `LAMBDA_EXECUTION_ROLE_ARN` - ARN of the Lambda execution role
- `LAMBDA_LOG_GROUP_NAME` - CloudWatch Log Group name for Lambda functions
- `AWS_PROFILE` - AWS profile to use (optional)

## Pipeline Components

- **CloudWatch Logs**: `/aws/lambda/[function-name]`
- **IAM Roles**:
  - `KinesisFirehoseDeliveryRole-mcp` - For Firehose delivery streams
  - `BasicLambdaExecutionRole` - For Lambda function execution
  - `CloudWatchLogsRole-mcp` - For CloudWatch Logs subscription filters
- **S3 Destination**: `s3://[bucket]/logs/`
- **Glue Database**: `mcp_analytics`
- **Glue Table**: `mcp_logs`

## Features

- **IAM Role Management**: Automated creation and configuration of required IAM roles
- **Policy Attachment**: Automatic attachment of necessary AWS managed policies
- **Environment Support**: Uses `.env` file for configuration
- **AWS Profile Support**: Works with named AWS profiles
- **Idempotent Scripts**: Safe to run multiple times - checks for existing resources

## Available Scripts

- **`create-firehose-role.sh`**: Creates IAM role for Kinesis Data Firehose with full access policies
- **`create-basic-lambda-role.sh`**: Creates basic Lambda execution role for CloudWatch Logs access
- **`create-cloudwatch-logs-role.sh`**: Creates CloudWatch Logs role for subscription filters
- **`deploy-analytics.sh`**: Deploys the AWS SAM analytics infrastructure (Kinesis Firehose, etc.)
- **`setup-glue-tables.sh`**: Sets up AWS Glue database and tables for analytics querying
- **`query-athena.sh`**: Queries the analytics data using Amazon Athena

## Monitoring & Querying

- **Query data**: Run `./query-athena.sh` to analyze your MCP server logs