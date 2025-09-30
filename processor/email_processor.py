import email
import json
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Tuple, Dict, Any
import os
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class EmailProcessor:
    """
    Handles email processing for SES integration.
    """
    
    def __init__(self, ses_client):
        self.ses_client = ses_client
        self.from_email = os.environ.get('FROM_EMAIL', 'invoice-bot@katechat.tech')
    
    def extract_pdf_attachments(self, msg: email.message.EmailMessage) -> List[Tuple[bytes, str]]:
        """
        Extract PDF attachments from email message.
        
        Returns:
            List of tuples (pdf_data, filename)
        """
        pdf_attachments = []
        
        try:
            for part in msg.walk():
                # Check if this part is an attachment
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    
                    if filename and filename.lower().endswith('.pdf'):
                        pdf_data = part.get_payload(decode=True)
                        if pdf_data:
                            pdf_attachments.append((pdf_data, filename))
                            logger.info(f"Found PDF attachment: {filename}")
                
                # Also check for inline PDFs
                elif part.get_content_type() == 'application/pdf':
                    filename = part.get_filename() or 'invoice.pdf'
                    pdf_data = part.get_payload(decode=True)
                    if pdf_data:
                        pdf_attachments.append((pdf_data, filename))
                        logger.info(f"Found inline PDF: {filename}")
        
        except Exception as e:
            logger.error(f"Error extracting PDF attachments: {str(e)}")
            raise
        
        return pdf_attachments
    
    def send_results_email(self, to_email: str, results: List[Dict[str, Any]], 
                          original_pdfs: List[Tuple[bytes, str]]):
        """
        Send results back to the sender via email.
        
        Args:
            to_email: Recipient email address
            results: List of parsing results
            original_pdfs: List of original PDF files (data, filename)
        """
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['Subject'] = 'Invoice Processing Results'
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Create email body
            body_text = self._create_email_body(results)
            msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
            
            # Attach original PDFs
            for pdf_data, filename in original_pdfs:
                pdf_attachment = MIMEApplication(pdf_data, 'pdf')
                pdf_attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                msg.attach(pdf_attachment)
            
            # Attach JSON results
            for i, result in enumerate(results):
                json_filename = f"parsed_{result['filename'].replace('.pdf', '')}.json"
                json_data = json.dumps(result['parsed_data'], indent=2, ensure_ascii=False).encode('utf-8')
                
                json_attachment = MIMEApplication(json_data, 'json')
                json_attachment.add_header('Content-Disposition', 'attachment', filename=json_filename)
                msg.attach(json_attachment)
            
            # Send email
            self.ses_client.send_raw_email(
                Source=self.from_email,
                Destinations=[to_email],
                RawMessage={'Data': msg.as_string()}
            )
            
            logger.info(f"Successfully sent results email to {to_email}")
            
        except ClientError as e:
            logger.error(f"Error sending email via SES: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating/sending email: {str(e)}")
            raise
    
    def _create_email_body(self, results: List[Dict[str, Any]]) -> str:
        """
        Create the email body text with processing results.
        """
        body = "Hello,\n\n"
        body += "Your invoice processing is complete. Please find the results below:\n\n"
        
        for i, result in enumerate(results, 1):
            parsed_data = result['parsed_data']
            filename = result['filename']
            
            body += f"=== Invoice {i}: {filename} ===\n"
            body += f"Invoice Number: {parsed_data.get('invoice_number', 'N/A')}\n"
            body += f"Issuer: {parsed_data.get('issuer_name', 'N/A')}\n"
            body += f"Receiver: {parsed_data.get('receiver_name', 'N/A')}\n"
            body += f"Total: {parsed_data.get('total', 0)}\n"
            
            items = parsed_data.get('items', [])
            if items:
                body += f"Items ({len(items)}):\n"
                for item in items:
                    title = item.get('title', 'N/A')
                    quantity = item.get('quantity', 'N/A')
                    price = item.get('price', 0)
                    body += f"  - {title} (Qty: {quantity}, Price: {price})\n"
            else:
                body += "Items: None found\n"
            
            body += "\n"
        
        body += "Attachments included:\n"
        body += "- Original PDF files\n"
        body += "- Parsed JSON data for each invoice\n\n"
        body += "Best regards,\n"
        body += "Invoice Processing Bot\n"
        body += "katechat.tech"
        
        return body