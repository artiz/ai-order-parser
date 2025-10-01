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

RESULT_EMAIL = os.environ.get('RESULT_EMAIL')

# Get AWS configuration from environment variables
# aws_region = os.environ.get('AWS_REGION', 'eu-central-1')
# aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
# aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

# Initialize AWS clients with explicit credentials if provided
def create_boto3_client(service_name, region_name=None):
    """Create boto3 client with environment credentials if available."""
    kwargs = {}
    # if region_name:
    #     kwargs['region_name'] = region_name
    # if aws_access_key_id and aws_secret_access_key:
    #     kwargs['aws_access_key_id'] = aws_access_key_id
    #     kwargs['aws_secret_access_key'] = aws_secret_access_key
    return boto3.client(service_name, **kwargs)

bedrock_client = create_boto3_client('bedrock-runtime')
ses_client = create_boto3_client('ses')
s3_client = create_boto3_client('s3')

def extract_sender_email(mail_obj: Dict[str, Any]) -> Optional[str]:
    """
    Extract sender email from SES mail object.
    """
    try:
        if 'commonHeaders' in mail_obj and 'from' in mail_obj['commonHeaders']:
            return mail_obj['commonHeaders']['from'][0]
        elif 'source' in mail_obj:
            return mail_obj['source']
        return None
    except Exception as e:
        logger.error(f"Error extracting sender email: {str(e)}")
        return None

def format_error_email_body(error_message: str):
    """
    Format error notification email body.
    """
    error_body = f"""
Hello,

We encountered an error while processing your invoice email. Please find the error details below:

ERROR DETAILS:
{error_message}

POSSIBLE SOLUTIONS:
1. Ensure your email contains PDF attachments
2. Check that the PDF files are not corrupted or password-protected
3. Try sending the email again in a few minutes
4. Contact support if the problem persists

We apologize for the inconvenience.

Best regards,
Invoice Processing Bot
katechat.tech
"""
    return error_body
        
def lambda_handler(event, context):
    """
    Main Lambda handler for processing SES emails with PDF attachments.
    """
    
    # Initialize AWS clients
    bedrock_client = create_boto3_client('bedrock-runtime')
    ses_client = create_boto3_client('ses')
    
    # Initialize processors
    pdf_parser = PDFParser(bedrock_client)
    email_processor = EmailProcessor(ses_client)
    
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Process SES event
        results = []
        if 'Records' in event:
            for record in event['Records']:
                if record.get('eventSource') == 'aws:ses':
                    result = process_ses_mail(record, pdf_parser, email_processor)
                    results.append(result)
                    logger.info(f"Processed SES record: {json.dumps(result, default=str)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed email(s)',
                'processed_records': len(results),
                'results': results
            })
        }
        
    except Exception as e:
        error_msg = f"Error in lambda handler: {str(e)}"
        logger.error(error_msg)
        
        # Try to extract sender email and send error notification to result email
        try:
            mail_obj = event.get('Records', [{}])[0].get('ses', {}).get('mail', {})
            sender_email = extract_sender_email(mail_obj)
            
            if RESULT_EMAIL:
                error_with_context = f"Error processing email from {sender_email or 'unknown'}: {error_msg}"
                email_processor.send_error_email(RESULT_EMAIL, format_error_email_body(error_with_context))
            else:
                logger.warning("RESULT_EMAIL not configured; cannot send error notification.")
                
        except Exception as notification_error:
            logger.error(f"Failed to send error notification: {str(notification_error)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }

def get_s3_email_details(record: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    """
    Extract S3 bucket and key from SES record
    """
    try:
        # Check if S3 action exists in receipt
        receipt = record.get('ses', {}).get('receipt', {})
        action = receipt.get('action', {})
        
        if action.get('type') == 's3':
            bucket_name = action.get('bucketName')
            object_key = action.get('objectKey')
            logger.info(f"Found S3 details: bucket={bucket_name}, key={object_key}")
            return bucket_name, object_key
        
        # Fallback: try to construct from message ID (common SES pattern)
        message_id = record.get('ses', {}).get('mail', {}).get('messageId')
        if message_id:
            # This is a common pattern - you might need to adjust based on your SES rule configuration
            inferred_key = f"emails/{message_id}"
            logger.info(f"Using inferred S3 key: {inferred_key}")
            return None, inferred_key  # Bucket will be determined from environment
        
        logger.warning("Could not extract S3 details from SES record")
        return None, None
        
    except Exception as e:
        logger.error(f"Error extracting S3 details: {str(e)}")
        return None, None

def download_email_from_s3(bucket_name: str, object_key: str) -> Optional[email.message.EmailMessage]:
    """
    Download and parse email from S3
    """
    try:
        # Use the global s3_client or create one
        s3 = s3_client
        
        # If no bucket name provided, get from environment variable
        if not bucket_name:
            bucket_name = os.environ.get('S3_BUCKET')
            if not bucket_name:
                raise ValueError("S3_BUCKET environment variable not set and no bucket name in SES record")
            logger.info(f"Using S3 bucket from environment: {bucket_name}")
        
        logger.info(f"Downloading email from S3: s3://{bucket_name}/{object_key}")
        
        # Download the email content
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        email_content = response['Body'].read().decode('utf-8')
        
        # Parse the email
        email_message = email.message_from_string(email_content)
        logger.info("Successfully parsed email from S3")
        
        return email_message
        
    except Exception as e:
        logger.error(f"Error downloading email from S3: {str(e)}")
        return None

def process_ses_mail(record: Dict[str, Any], pdf_parser: PDFParser, email_processor: EmailProcessor) -> Dict[str, Any]:
    """
    Process the SES mail record and parse attachments for invoice data
    """
    mail_obj = record.get('ses', {}).get('mail', {})
    sender_email = extract_sender_email(mail_obj)
    
    try:
        logger.info("Processing SES mail record")
        
        # Extract mail headers and basic info
        message_id = mail_obj.get('messageId', '')
        source = mail_obj.get('source', sender_email or 'unknown')
        destination = mail_obj.get('destination', [])
        
        logger.info(f"Processing email from {source} to {destination}")
        
        # Extract S3 information for the email content
        common_headers = mail_obj.get('commonHeaders', {})
        subject = common_headers.get('subject', 'No Subject')
        
        # Get S3 details and download email
        bucket_name, object_key = get_s3_email_details(record)
        
        if not object_key:
            # If we can't find S3 details, try to use the message ID as key
            object_key = message_id
            logger.info(f"Using message ID as S3 key: {object_key}")
        
        # Download and parse the email from S3
        email_message = download_email_from_s3(bucket_name, object_key)
        
        if not email_message:
            error_msg = f"Could not retrieve email content from S3 for email from {sender_email or 'unknown'}"
            logger.error(error_msg)
            if RESULT_EMAIL:
                email_processor.send_error_email(RESULT_EMAIL, format_error_email_body(error_msg))
            return {
                'statusCode': 400,
                'message': error_msg,
                'messageId': message_id
            }
        
        # Extract PDF attachments
        pdf_attachments = email_processor.extract_pdf_attachments(email_message)
        
        if not pdf_attachments:
            # No PDFs found - send informational email
            no_pdf_msg = f"No PDF attachments found in email from {sender_email or 'unknown'}. Please ensure PDF invoices are attached."
            logger.warning(no_pdf_msg)
            if RESULT_EMAIL:
                email_processor.send_error_email(RESULT_EMAIL, format_error_email_body(no_pdf_msg))
            return {
                'statusCode': 200,
                'message': no_pdf_msg,
                'messageId': message_id,
                'processed_attachments': 0
            }
        
        logger.info(f"Found {len(pdf_attachments)} PDF attachments")
        
        # Process each PDF attachment
        results = []
        for pdf_data, filename in pdf_attachments:
            try:
                logger.info(f"Processing PDF: {filename}")
                parsed_data = pdf_parser.parse_invoice_pdf(pdf_data)
                results.append({
                    'filename': filename,
                    'parsed_data': parsed_data,
                    'status': 'success'
                })
                logger.info(f"Successfully parsed {filename}")
                
            except Exception as pdf_error:
                logger.error(f"Error parsing {filename}: {str(pdf_error)}")
                results.append({
                    'filename': filename,
                    'error': str(pdf_error),
                    'parsed_data': dict(),
                    'status': 'error'
                })
        
        # Send results to configured result email address
        if RESULT_EMAIL and results:
            try:
                email_processor.send_results_email(
                    to_email=RESULT_EMAIL,
                    results=results,
                    original_pdfs=pdf_attachments,
                    sender_email=sender_email  # Include sender info for context
                )
                logger.info(f"Sent results email to {RESULT_EMAIL} (from {sender_email})")
            except Exception as email_error:
                logger.error(f"Failed to send results email: {str(email_error)}")
                # Still continue - we processed the PDFs successfully
        
        return {
            'statusCode': 200,
            'message': 'Email processed successfully',
            'messageId': message_id,
            'subject': subject,
            'processed_attachments': len(results),
            'results': results
        }
        
    except Exception as e:
        error_msg = f"Error processing SES mail: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Send error notification to result email if available
        if RESULT_EMAIL:
            error_with_context = f"Error processing email from {sender_email or 'unknown'}: {error_msg}"
            email_processor.send_error_email(RESULT_EMAIL, format_error_email_body(error_with_context))
        
        return {
            'statusCode': 500,
            'message': error_msg,
            'messageId': mail_obj.get('messageId', ''),
            'processed_attachments': 0
        }

if __name__ == "__main__":
    # For local testing, use test_local.py instead
    print("For local testing, use:")
    print("python test_local.py test <path_to_pdf>")
    print("python test_local.py test-all")
    print("Example: python test_local.py test ../data/Rechnung-38110.pdf")