#!/usr/bin/env python3
"""
Local testing script for the invoice parser.
"""

import os
import sys
import json
import boto3
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
    print("Using system environment variables only.")

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Get AWS configuration from environment variables
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

from pdf_parser import PDFParser

def create_boto3_client(service_name):
    """Create boto3 client with environment credentials if available."""
    kwargs = {
        'region_name': AWS_REGION
    }
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        kwargs['aws_access_key_id'] = AWS_ACCESS_KEY_ID
        kwargs['aws_secret_access_key'] = AWS_SECRET_ACCESS_KEY
    return boto3.client(service_name, **kwargs)

def test_single_pdf(pdf_path: str):
    """
    Test parsing a single PDF file.
    """
    print(f"Testing PDF: {pdf_path}")
    
    # Initialize AWS clients
    try:
        bedrock_client = create_boto3_client('bedrock-runtime')
    except Exception as e:
        print(f"Error initializing AWS client: {e}")
        print("Make sure you have AWS credentials configured (.env file or aws configure)")
        return None
    
    # Initialize parser
    pdf_parser = PDFParser(bedrock_client)
    
    try:
        # Read PDF file
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        print(f"PDF size: {len(pdf_data)} bytes")
        
        filename = os.path.basename(pdf_path)
        
        # Parse PDF
        result = pdf_parser.parse_invoice([(pdf_data, filename)], "")
        
        print("\n" + "="*50)
        print("PARSING RESULT:")
        print("="*50)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return result
        
    except Exception as e:
        print(f"Error parsing PDF: {str(e)}")
        return None

def test_all_sample_pdfs():
    """
    Test all PDF files in the data directory.
    """
    # Get the data directory path
    current_dir = Path(__file__).parent
    data_dir = current_dir.parent / "data"
    
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        return
    
    # Find all PDF files
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {data_dir}")
        return
    
    print(f"Found {len(pdf_files)} PDF files to test:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")
    
    print("\n" + "="*70)
    
    results = {}
    
    for pdf_file in pdf_files:
        print(f"\nTesting: {pdf_file.name}")
        print("-" * 50)
        
        result = test_single_pdf(str(pdf_file))
        results[pdf_file.name] = result
        
        print("\n" + "="*70)
    
    # Summary
    print("\nSUMMARY:")
    print("="*70)
    
    for filename, result in results.items():
        status = "✓ SUCCESS" if result else "✗ FAILED"
        print(f"{filename}: {status}")
    
    return results

def show_pdf_info(pdf_path: str):
    """
    Show basic PDF information without AI parsing.
    """
    print(f"Analyzing PDF: {pdf_path}")
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        print("\n" + "="*50)
        print("PDF INFORMATION:")
        print("="*50)
        print(f"File size: {len(pdf_data)} bytes")
        print(f"File path: {pdf_path}")
        print("Note: PDF content will be sent directly to AWS Bedrock Nova for parsing")
        
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")

def main():
    """
    Main function for command line usage.
    """
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_local.py <command> [options]")
        print("\nCommands:")
        print("  test <pdf_path>    - Test parsing a specific PDF file")
        print("  test-all           - Test all PDF files in ../data directory")
        print("  info <pdf_path>    - Show PDF information without AI parsing")
        print("\nExamples:")
        print("  python test_local.py test ../data/Rechnung-38110.pdf")
        print("  python test_local.py test-all")
        print("  python test_local.py info ../data/42507956.pdf")
        return
    
    command = sys.argv[1]
    
    if command == "test":
        if len(sys.argv) < 3:
            print("Error: Please provide PDF file path")
            return
        pdf_path = sys.argv[2]
        if not os.path.exists(pdf_path):
            print(f"Error: File not found: {pdf_path}")
            return
        test_single_pdf(pdf_path)
    
    elif command == "test-all":
        test_all_sample_pdfs()
    
    elif command == "info":
        if len(sys.argv) < 3:
            print("Error: Please provide PDF file path")
            return
        pdf_path = sys.argv[2]
        if not os.path.exists(pdf_path):
            print(f"Error: File not found: {pdf_path}")
            return
        show_pdf_info(pdf_path)
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()