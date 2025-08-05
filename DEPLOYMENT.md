# Deployment Guide

This guide covers deploying the Alpha Vantage MCP Server to AWS Lambda using AWS SAM.

## Prerequisites

- Python 3.13+ with [uv](https://github.com/astral-sh/uv) (required for package management)
- [AWS CLI](https://aws.amazon.com/cli/) installed and configured
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) installed

## Quick Deployment

1. **Clone and prepare the project:**
   ```bash
   git clone https://github.com/alphavantage/alpha_vantage_mcp.git
   cd alpha_vantage_mcp
   ```

2. **Set up environment variables (optional):**
   Copy the example environment file and customize as needed:
   ```bash
   cp .env.example .env
   ```
   
   The `.env` file contains:
   ```bash
   # AWS profile (if you have multiple profiles)
   AWS_PROFILE=default
   
   # Custom domain configuration
   DOMAIN_NAME=your-custom-domain.com
   ```

3. **Request SSL certificate:**
   ```bash
   ./request_certificate.sh
   ```
   The script will output the certificate ARN. If the certificate is not yet issued, it will also display DNS validation records that you must add to your DNS provider before the certificate can be issued. Follow the instructions provided by the script to add the required DNS records.
   
   This will automatically update the `CERTIFICATE_ARN` in your `.env` file.

4. **Deploy using the automated script:**
   ```bash
   ./deploy.sh
   ```

The deployment script will:
- Load environment variables from `.env`
- Generate `requirements.txt`
- Build the SAM application
- Deploy to AWS (guided setup on first run)

5. **Configure DNS:**
   After deployment, you'll receive `CustomDomainURL` and `CustomDomainTarget` in the output. Go to your DNS management panel (such as Cloudflare) and create a CNAME record:
   - **Name**: `CustomDomainURL`
   - **Target**: `CustomDomainTarget`
   
   **Note for Cloudflare users**: Set SSL/TLS encryption mode to **Full** in your Cloudflare dashboard, otherwise you'll get ERR_TOO_MANY_REDIRECTS.

6. **Test the deployment:**
   Once DNS propagation is complete, verify your domain is working:
   ```bash
   uv run tests/test_remote.py
   ```