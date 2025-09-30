import json
import logging
import base64
import os
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class PDFParser:
    """
    PDF parser using AWS Bedrock Nova model for invoice extraction.
    """
    
    def __init__(self, bedrock_client):
        self.bedrock_client = bedrock_client
        self.model_id = "eu.amazon.nova-lite-v1:0"  # Nova Lite model
    
    def parse_invoice_pdf(self, pdf_data: bytes) -> Dict[str, Any]:
        """
        Parse invoice PDF using AWS Bedrock Nova model with direct PDF input.
        """
        try:
            logger.info(f"Processing PDF of {len(pdf_data)} bytes")
            
            # Call Bedrock Nova model with PDF
            response = self._call_bedrock_nova_with_pdf(pdf_data)
            
            # Parse and validate response
            parsed_data = self._parse_nova_response(response)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise
    
    def _create_invoice_parsing_prompt(self) -> str:
        """
        Create a detailed prompt for the Nova model to parse invoice data from PDF.
        """
        return """
You are an expert invoice parser. Please analyze the PDF document and extract the required information in a strict JSON format.

The PDF may contain an invoice in English or German. Please extract the following information and return ONLY a valid JSON object with this exact structure:

{
    "invoice_number": "<invoice/receipt number>",
    "receiver_name": "<invoice receiver name>",
    "receiver_address": "<invoice receiver full address>",
    "issuer_name": "<invoice issuer name/company name>",
    "issuer_address": "<invoice issuer full address>",
    "total": <total amount as number>,
    "items": [
        {
            "title": "<item title/description>",
            "quantity": "<item quantity>",
            "price": "<item unit price as number>"
        }
    ]
}

IMPORTANT INSTRUCTIONS:
1. Return ONLY the JSON object, no additional text or explanations
2. For German invoices: "Rechnung" means invoice, "Rechnungsnummer" means invoice number, "Gesamt" or "Summe" means total
3. Extract ALL line items with their quantities and individual prices
4. Use numbers (not strings) for price and total fields
5. If information is not available, use empty string "" for strings and 0 for numbers
6. Ensure the JSON is valid and properly formatted
7. For addresses, include the complete address with street, city, postal code if available
8. For quantities, extract the actual number (e.g., "2x" becomes "2")
9. Look carefully at the document structure to identify invoice details, line items, and totals

Remember: Return ONLY the JSON object, nothing else.
"""
    
    def _call_bedrock_nova_with_pdf(self, pdf_data: str) -> str:
        """
        Call AWS Bedrock Nova model with PDF document directly.
        """
        try:
            # Create prompt for PDF analysis
            prompt = self._create_invoice_parsing_prompt()
            
            # Prepare the request body for Nova model with PDF document
            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            },
                            {
                                "document": {
                                    "format": "pdf",
                                    "name": "invoice",
                                    "source": {
                                        "bytes": pdf_data
                                    }
                                }
                            }
                        ]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": 2000,
                    "temperature": 0.1,
                    "topP": 0.9
                }
            }
            
            # Call the model
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=request_body["messages"],
                inferenceConfig=request_body["inferenceConfig"]
            )
            
            # Extract the response text
            response_text = response['output']['message']['content'][0]['text']
            
            logger.info(f"Received response from Nova model: {len(response_text)} characters")
            
            return response_text
            
        except ClientError as e:
            logger.error(f"Error calling Bedrock Nova: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Nova: {str(e)}")
            raise
    
    def _parse_nova_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse and validate the Nova model response.
        """
        try:
            # Clean the response - sometimes models add extra text
            response_text = response_text.strip()
            
            # Find JSON in the response (in case there's extra text)
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_text = response_text[start_idx:end_idx]
            
            # Parse JSON
            parsed_data = json.loads(json_text)
            
            # Validate required fields
            required_fields = ['invoice_number', 'receiver_name', 'receiver_address', 
                             'issuer_name', 'issuer_address', 'total', 'items']
            
            for field in required_fields:
                if field not in parsed_data:
                    parsed_data[field] = "" if field != 'total' and field != 'items' else (0 if field == 'total' else [])
            
            # Validate items structure
            if not isinstance(parsed_data['items'], list):
                parsed_data['items'] = []
            
            for item in parsed_data['items']:
                if not isinstance(item, dict):
                    continue
                if 'title' not in item:
                    item['title'] = ""
                if 'quantity' not in item:
                    item['quantity'] = ""
                if 'price' not in item:
                    item['price'] = 0
            
            # Ensure total is a number
            try:
                parsed_data['total'] = float(parsed_data['total'])
            except (ValueError, TypeError):
                parsed_data['total'] = 0.0
            
            logger.info("Successfully parsed and validated invoice data")
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in Nova response: {str(e)}")
            logger.error(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from AI model: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing Nova response: {str(e)}")
            raise