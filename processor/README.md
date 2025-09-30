# Invoice Parser Processor

This Lambda function processes emails received by AWS SES, extracts PDF attachments, parses them using AWS Bedrock Nova model, and sends results back via email.

## Features

- Receives emails via AWS SES
- Extracts PDF attachments from emails
- Sends PDF directly to AWS Bedrock Nova (no text pre-processing)
- Parses invoices in English and German using AI multimodal capabilities
- Sends parsed JSON results back to sender
- Local testing capability

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your AWS credentials
vim .env
```

3. Alternative: Configure AWS credentials via AWS CLI:
```bash
aws configure
```

4. Validate configuration:
```bash
python validate_config.py
```

## Local Testing

Test individual PDF files:
```bash
python test_local.py test ../data/Rechnung-38110.pdf
```

Test all PDFs in data directory:
```bash
python test_local.py test-all
```

Show PDF info (without AI parsing):
```bash
python test_local.py info ../data/42507956.pdf
```

## Environment Variables

For local development (`.env` file):
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `AWS_REGION`: AWS region (default: us-east-1) 
- `AWS_ACCESS_KEY_ID`: Your AWS access key ID
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key

For Lambda deployment (automatically set):
- `AWS_REGION`: AWS region (default: us-east-1)
- `SES_S3_BUCKET`: S3 bucket where SES stores emails
- `FROM_EMAIL`: Email address to send results from (default: invoice-bot@katechat.tech)

## Output Format

The parser extracts the following information from invoices:

```json
{
    "invoice_number": "12345",
    "receiver_name": "John Doe",
    "receiver_address": "123 Main St, City, 12345",
    "issuer_name": "ACME Corp",
    "issuer_address": "456 Business Ave, Town, 67890",
    "total": 150.50,
    "items": [
        {
            "title": "Product Name",
            "quantity": "2",
            "price": 75.25
        }
    ]
}
```

## Supported Languages

- English
- German (Rechnung, Rechnungsnummer, etc.)

## Error Handling

The function includes comprehensive error handling and logging for:
- PDF text extraction failures
- AWS Bedrock API errors
- Email processing errors
- JSON parsing validation