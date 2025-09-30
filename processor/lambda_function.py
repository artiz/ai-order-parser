import json
import base64
import boto3
import logging
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from botocore.exceptions import ClientError
import os
from typing import Dict, List, Any, Optional
import tempfile

# Load environment variables from .env file (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available (e.g., in Lambda), use environment variables directly
    pass

from pdf_parser import PDFParser
from email_processor import EmailProcessor

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logger.setLevel(getattr(logging, log_level, logging.INFO))

# Get AWS configuration from environment variables
aws_region = os.environ.get('AWS_REGION', 'us-east-1')
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

# Initialize AWS clients with explicit credentials if provided
def create_boto3_client(service_name, region_name=None):
    """Create boto3 client with environment credentials if available."""
    kwargs = {}
    if region_name:
        kwargs['region_name'] = region_name
    if aws_access_key_id and aws_secret_access_key:
        kwargs['aws_access_key_id'] = aws_access_key_id
        kwargs['aws_secret_access_key'] = aws_secret_access_key
    return boto3.client(service_name, **kwargs)

bedrock_client = create_boto3_client('bedrock-runtime', aws_region)
ses_client = create_boto3_client('ses', aws_region)
s3_client = create_boto3_client('s3', aws_region)

def lambda_handler(event, context):
    """
    Main Lambda handler for processing SES emails with PDF attachments.
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Initialize processors
        pdf_parser = PDFParser(bedrock_client)
        email_processor = EmailProcessor(ses_client)
        
        # Process SES event
        if 'Records' in event:
            for record in event['Records']:
                if record.get('eventSource') == 'aws:ses':
                    process_ses_mail(record, pdf_parser, email_processor)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Successfully processed email')
        }
        
    except Exception as e:
        logger.error(f"Error processing email: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing email: {str(e)}')
        }

def process_ses_mail(record: Dict[str, Any], pdf_parser: PDFParser, email_processor: EmailProcessor):
    """
    Process an SES mail record.
    """
    try:
        # Extract message from SES record
        mail_obj = record['ses']['mail']
        
        # Get S3 object details from SES
        message_id = mail_obj['messageId']
        
        # Download raw email from S3 (SES stores emails in S3)
        bucket_name = os.environ.get('SES_S3_BUCKET')
        s3_key = f"emails/{message_id}"
        
        logger.info(f"Downloading email from S3: {bucket_name}/{s3_key}")
        
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        raw_email = response['Body'].read()
        
        # Parse email
        msg = email.message_from_bytes(raw_email)
        
        # Extract sender - handle different formats
        sender_email = None
        if 'commonHeaders' in mail_obj and 'from' in mail_obj['commonHeaders']:
            sender_email = mail_obj['commonHeaders']['from'][0]
        elif 'source' in mail_obj:
            sender_email = mail_obj['source']
        else:
            # Fallback to parsing from raw email
            sender_email = msg.get('From', '')
        
        logger.info(f"Processing email from: {sender_email}")
        
        # Process email attachments
        pdf_attachments = email_processor.extract_pdf_attachments(msg)
        
        if not pdf_attachments:
            logger.warning("No PDF attachments found in email")
            return
        
        results = []
        
        for pdf_data, pdf_filename in pdf_attachments:
            logger.info(f"Processing PDF: {pdf_filename} ({len(pdf_data)} bytes)")
            
            # Parse PDF with AI
            parsed_data = pdf_parser.parse_invoice_pdf(pdf_data)
            results.append({
                'filename': pdf_filename,
                'parsed_data': parsed_data
            })
        
        # Send results back via email
        if results and sender_email:
            email_processor.send_results_email(
                to_email=sender_email,
                results=results,
                original_pdfs=[(data, filename) for data, filename in pdf_attachments]
            )
            logger.info(f"Sent results email to {sender_email}")
        else:
            logger.error("No results to send or sender email not found")
            
    except Exception as e:
        logger.error(f"Error processing SES mail: {str(e)}")
        raise

if __name__ == "__main__":
    # For local testing, use test_local.py instead
    print("For local testing, use:")
    print("python test_local.py test <path_to_pdf>")
    print("python test_local.py test-all")
    print("Example: python test_local.py test ../data/Rechnung-38110.pdf")