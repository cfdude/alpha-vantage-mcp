import json
import base64
import gzip
import boto3
import os
from datetime import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda function to consume CloudWatch Logs via Subscription Filter
    and write them to S3 in the exact format expected by the Glue table.
    """
    s3_bucket = os.environ['S3_BUCKET']
    processed_records = 0
    failed_records = 0
    
    # Collect log lines to batch write to S3
    log_lines = []
    
    try:
        # Decode CloudWatch Logs data from Subscription Filter
        compressed_data = base64.b64decode(event['awslogs']['data'])
        log_data = gzip.decompress(compressed_data).decode('utf-8')
        log_json = json.loads(log_data)
        
        # Process CloudWatch log events
        if 'logEvents' in log_json:
            for log_event in log_json['logEvents']:
                try:
                    log_line = process_log_event(log_event)
                    if log_line:
                        log_lines.append(log_line)
                        processed_records += 1
                except Exception as e:
                    logger.error(f"Error processing log event: {str(e)}")
                    failed_records += 1
        
        # Write batched log lines to S3
        if log_lines:
            write_logs_to_s3(log_lines, s3_bucket)
                
        logger.info(f"Processed {processed_records} records successfully, {failed_records} failed")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'processed': processed_records,
                'failed': failed_records
            })
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def process_log_event(log_event):
    """Process a single log event and return it in the exact format from log.txt"""
    try:
        message = log_event.get('message', '')
        
        # Only process MCP_ANALYTICS messages
        if 'MCP_ANALYTICS' not in message:
            return None
        
        # Return the message stripped of whitespace
        return message.strip()
        
    except Exception as e:
        logger.error(f"Error processing log event: {str(e)}")
        return None

def write_logs_to_s3(log_lines, s3_bucket):
    """Write log lines to S3 with the expected key format: logs/YYYY/MM/DD/HH/xxx.txt"""
    try:
        # Create content from log lines with proper line separation, filtering empty lines
        content = '\n'.join(line for line in log_lines if line.strip())
        
        # Generate S3 key with the expected format: logs/YYYY/MM/DD/HH/xxx.txt
        now = datetime.utcnow()
        s3_key = f"logs/{now.year}/{now.month:02d}/{now.day:02d}/{now.hour:02d}/{now.strftime('%Y%m%d_%H%M%S_%f')}.txt"
        
        # Write to S3 (uncompressed .txt file)
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=content.encode('utf-8'),
            ContentType='text/plain'
        )
        
        logger.info(f"Wrote {len(log_lines)} log lines to s3://{s3_bucket}/{s3_key}")
        
    except Exception as e:
        logger.error(f"Error writing logs to S3: {str(e)}")
        raise