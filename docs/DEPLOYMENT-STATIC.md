# Static Files + API Deployment Guide

This guide explains how to deploy both the static web frontend and the API backend using the same domain with AWS CloudFront + S3 + Lambda.

## Architecture

```
Domain (mcp.alphavantage.co)
       ↓
   CloudFront Distribution
       ↓
┌─────────────────┬─────────────────┐
│   Static Files  │   API Routes    │
│   (S3 Bucket)   │   (Lambda)      │
├─────────────────┼─────────────────┤
│ /               │ /mcp*           │
│ /_next/*        │ /openai*        │
│ /index.html     │ /.well-known*   │
│ /404.html       │ /authorize*     │
│ etc.            │ /token*         │
│                 │ /register*      │
└─────────────────┴─────────────────┘
```

## Deployment Steps

### 1. Build the Static Files

First, build the Next.js static export:

```bash
cd web
npm install
npm run build
```

This creates the `web/out` directory with all static files.

### 2. Deploy the CloudFormation Stack

Deploy the updated template with the new parameters:

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name mcp-alphavantage \
  --parameter-overrides \
    Environment=production \
    DomainName=mcp.alphavantage.co \
    CertificateArn=arn:aws:acm:us-east-1:123456789012:certificate/your-cert-id \
    StaticFilesBucket=alphavantage-mcp-static-files \
    R2Bucket=alphavantage-mcp-responses \
    R2PublicDomain=https://data.alphavantage-mcp.com \
    R2EndpointUrl=https://your-account-id.r2.cloudflarestorage.com \
    R2AccessKeyId=your-r2-access-key \
    R2SecretAccessKey=your-r2-secret-key \
  --capabilities CAPABILITY_IAM
```

### 3. Upload Static Files to S3

Use the deployment script to upload static files:

```bash
./deploy-web.sh alphavantage-mcp-static-files
```

Or manually with AWS CLI:

```bash
aws s3 sync web/out s3://alphavantage-mcp-static-files --delete
```

### 4. Configure DNS

Point your domain to the CloudFront distribution:

```bash
# Get the CloudFront domain name from stack outputs
aws cloudformation describe-stacks \
  --stack-name mcp-alphavantage \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDomainName`].OutputValue' \
  --output text
```

Create a CNAME record:
- Name: `mcp.alphavantage.co`
- Value: `d1234567890123.cloudfront.net` (from above command)

### 5. Test the Deployment

- **Static Files**: `https://mcp.alphavantage.co/` → Serves the Next.js app
- **API Endpoints**: `https://mcp.alphavantage.co/mcp` → Routes to Lambda
- **OAuth**: `https://mcp.alphavantage.co/.well-known/oauth-authorization-server` → Routes to Lambda

## Benefits of This Architecture

1. **Performance**: Static files served from S3/CloudFront edge locations
2. **Cost-Effective**: No Lambda cold starts for static content
3. **Scalable**: CloudFront handles traffic spikes automatically
4. **Same Domain**: No CORS issues between frontend and API
5. **Caching**: Aggressive caching for static assets, no caching for API

## Cache Behavior

- **Static Assets** (`/_next/*`): 1 year cache
- **HTML Files**: 1 hour cache
- **API Routes**: No caching (always fresh)

## Updating Static Files

To update the frontend:

1. Make changes in the `web/` directory
2. Run `npm run build`
3. Run `./deploy-web.sh <bucket-name>`
4. (Optional) Invalidate CloudFront cache for immediate updates:

```bash
aws cloudfront create-invalidation \
  --distribution-id E1234567890123 \
  --paths "/*"
```

## Troubleshooting

### Static Files Not Loading
- Check S3 bucket policy allows public read
- Verify CloudFront cache behaviors are configured correctly
- Check if files exist in S3 bucket

### API Routes Not Working
- Verify Lambda function is deployed
- Check CloudFront cache behaviors for API paths
- Look at CloudWatch logs for Lambda errors

### CORS Issues
- Should not occur since everything is on the same domain
- If still seeing CORS, check that API requests are going to the right paths