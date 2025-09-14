# Log Analytics Pipeline

Set up autonomous log analytics for your Alpha Vantage MCP server deployment.

## Setup Steps

Run these scripts in order to set up the complete pipeline:

1. **Create IAM role for Lambda logs processor:**
   ```bash
   ./create-logs-processor-role.sh
   ```

2. **Deploy the analytics infrastructure:**
   ```bash
   ./deploy-analytics.sh
   ```

3. **Set up Glue tables for querying:**
   ```bash
   ./setup-glue-tables.sh
   ```

4. **Query analytics data:**
   ```bash
   ./query-athena.sh
   ```

## Environment Configuration

The scripts use the following environment variables (can be set in `.env` file):

- `ANALYTICS_LOGS_BUCKET` - S3 bucket for analytics logs (default: `alphavantage-mcp-analytics-logs`)
- `LAMBDA_LOG_GROUP_NAME` - CloudWatch Log Group name for Lambda functions
- `AWS_PROFILE` - AWS profile to use (optional)

## Pipeline Components

- **CloudWatch Logs**: `/aws/lambda/[function-name]`
- **IAM Roles**:
  - `LogsProcessorRole-mcp` - For Lambda logs processor function
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

- **`create-logs-processor-role.sh`**: Creates IAM role for Lambda logs processor with S3 and CloudWatch access
- **`deploy-analytics.sh`**: Deploys the AWS SAM analytics infrastructure (CloudWatch Logs + Lambda)
- **`setup-glue-tables.sh`**: Sets up AWS Glue database and tables for analytics querying
- **`query-athena.sh`**: Queries the analytics data using Amazon Athena

## Monitoring & Querying

- **Query data**: Run `./query-athena.sh` to analyze your MCP server logs