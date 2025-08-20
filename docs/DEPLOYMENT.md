# Deployment Guide

This guide covers deploying the Alpha Vantage MCP Server to AWS Lambda using AWS SAM.

## Prerequisites

- Python 3.13+ with [uv](https://github.com/astral-sh/uv) (required for package management)
- [AWS CLI](https://aws.amazon.com/cli/) installed and configured
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) installed
- [Cloudflare Account](https://www.cloudflare.com) for R2 storage (optional, for large response handling)

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

## Cloudflare R2 Setup (Optional)

For handling large API responses, the server can upload data to Cloudflare R2 storage and provide URLs for access. This is optional but recommended for production use.

### 1. Create R2 Bucket

1. Log into your [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Navigate to **R2 Object Storage** in the left sidebar
3. Click **Create bucket**
4. Choose a bucket name (e.g., `alphavantage-mcp-responses`)
5. Select a location close to your users
6. Click **Create bucket**

### 2. Configure Domain Access

Choose one of the following options for accessing uploaded files:

**Option A: Custom Domain (Recommended)**

1. In your bucket settings, click **Custom Domains** tab
2. Click **Connect Domain**
3. Enter your custom domain (e.g., `data.yourdomain.com`)
4. Add the required DNS record to your domain:
   - **Type**: CNAME
   - **Name**: `data` (or your chosen subdomain)
   - **Target**: Your bucket's R2.dev URL
5. Wait for DNS propagation and domain verification
6. Use your custom domain as `R2_PUBLIC_DOMAIN` (e.g., `https://data.yourdomain.com`)

**Option B: Public Access (Alternative)**

If you don't want to use a custom domain:

1. Go to your bucket settings
2. Click **Settings** tab
3. Under **Public access**, click **Allow Access**
4. Use the public bucket URL as `R2_PUBLIC_DOMAIN` (e.g., `https://pub-xxxxx.r2.dev`)

### 3. Create R2 API Token

1. In your R2 overview page, click **Manage API tokens** button
2. Choose **Account API Tokens** (recommended for production systems as they remain active even if you leave the organization)
3. Click **Create Account API Token**
4. Configure the token:
   - **Token name**: Enter a name (e.g., `R2 Account Token`)
   - **Permissions**: Select **Object Read & Write** (allows reading, writing, and listing objects)
   - **Specify bucket(s)**: Choose **Apply to specific buckets only** and select your bucket
5. Click **Create Token**
6. Copy and save the token securely

### 4. Get R2 Configuration Values

After creating your bucket and API token, collect these values:

- **R2_BUCKET**: Your bucket name (e.g., `alphavantage-mcp-responses`)
- **R2_PUBLIC_DOMAIN**: Your public domain or bucket URL
  - Custom domain: `https://data.yourdomain.com`
  - Public bucket URL: `https://pub-xxxxx.r2.dev`
- **R2_ENDPOINT_URL**: `https://<account-id>.r2.cloudflarestorage.com` (find your account ID in Cloudflare Dashboard)
- **R2_ACCESS_KEY_ID**: From your R2 API token (created in step 3)
- **R2_SECRET_ACCESS_KEY**: Generated alongside the access key

### 5. Add to Environment Variables

Add these to your `.env` file or Lambda environment variables:

```bash
# Cloudflare R2 Configuration
R2_BUCKET=alphavantage-mcp-responses
R2_PUBLIC_DOMAIN=https://data.yourdomain.com
R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your-r2-access-key-id
R2_SECRET_ACCESS_KEY=your-r2-secret-access-key
```