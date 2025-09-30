# AI Invoice Parser

An intelligent invoice processing system that receives PDFs via email, extracts structured data using AWS Bedrock Nova AI model, and returns parsed JSON results automatically.

## 🌟 Features

- **Email Integration**: Receive invoices via `invoice-bot@katechat.tech`
- **Multi-language Support**: Parse invoices in English and German
- **AI-Powered Extraction**: Uses AWS Bedrock Nova multimodal model with direct PDF input
- **Automatic Processing**: Fully automated from email receipt to response
- **Structured Output**: Returns clean JSON with invoice details and line items
- **Local Testing**: Test parser locally with sample invoices

## 📁 Project Structure

```
ai-order-parser/
├── data/                    # Sample invoice PDFs for testing
│   ├── 2025-30240870.pdf
│   ├── 42507956.pdf
│   ├── KR318586338013.pdf
│   ├── Rechnung-38110.pdf
│   └── Rechnung_HDK-054031.pdf
├── processor/               # Lambda function code
│   ├── lambda_function.py   # Main Lambda handler
│   ├── pdf_parser.py        # PDF parsing with Bedrock Nova
│   ├── email_processor.py   # SES email handling
│   ├── test_local.py        # Local testing script
│   ├── requirements.txt     # Python dependencies
│   └── README.md           # Processor documentation
├── infrastructure/          # Terraform IaC
│   ├── main.tf             # Main Terraform configuration
│   ├── variables.tf        # Variable definitions
│   ├── lambda.tf           # Lambda function resources
│   ├── ses.tf              # SES configuration
│   ├── s3.tf               # S3 bucket for emails
│   ├── iam.tf              # IAM roles and policies
│   ├── outputs.tf          # Terraform outputs
│   └── README.md           # Infrastructure documentation
├── deploy.sh               # Deployment script
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.0 installed
3. **Python** 3.11+ with pip
4. Domain `katechat.tech` already configured (provided in requirements)

### Deployment

1. **Clone and navigate to project**:
   ```bash
   cd ai-order-parser
   ```

2. **Deploy infrastructure**:
   ```bash
   ./deploy.sh
   ```

3. **Wait for DNS propagation** (up to 24 hours)

4. **Test the system**:
   Send an email with PDF attachment to `invoice-bot@katechat.tech`

### Local Testing

1. **Configure environment variables**:
```bash
cd processor
cp .env.example .env
# Edit .env with your AWS credentials
```

2. **Test the parser** with sample invoices:
```bash
# Test a specific PDF
python test_local.py test ../data/Rechnung-38110.pdf

# Test all sample PDFs
python test_local.py test-all

# Show PDF info (without AI parsing)
python test_local.py info ../data/42507956.pdf
```

## 📧 How It Works

1. **Email Receipt**: Send invoice PDF to `invoice-bot@katechat.tech`
2. **SES Processing**: AWS SES receives email and stores in S3
3. **Lambda Trigger**: SES triggers Lambda function automatically
4. **PDF Extraction**: Function extracts PDF attachments from email
5. **AI Parsing**: AWS Bedrock Nova model receives PDF directly for multimodal analysis
6. **Response**: Parsed JSON and original PDF sent back via email

## 📄 Output Format

The system extracts invoices into this JSON structure:

```json
{
    "invoice_number": "INV-2024-001",
    "receiver_name": "John Doe",
    "receiver_address": "123 Main St, City, 12345 Country",
    "issuer_name": "ACME Corporation",
    "issuer_address": "456 Business Ave, Town, 67890 Country",
    "total": 250.75,
    "items": [
        {
            "title": "Product A",
            "quantity": "2",
            "price": 125.00
        },
        {
            "title": "Service Fee", 
            "quantity": "1",
            "price": 0.75
        }
    ]
}
```

## 🌍 Multi-language Support

The system understands invoices in:
- **English**: Invoice, Total, Items, etc.
- **German**: Rechnung, Rechnungsnummer, Gesamt, Summe, etc.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Email Client  │───▶│  AWS SES     │───▶│  AWS Lambda     │
└─────────────────┘    └──────────────┘    └─────────────────┘
                              │                       │
                              ▼                       ▼
                       ┌──────────────┐    ┌─────────────────┐
                       │   AWS S3     │    │ AWS Bedrock     │
                       │  (Storage)   │    │  (Nova AI)      │
                       └──────────────┘    └─────────────────┘
```

## 🔐 Security Features

- **IAM Policies**: Minimal permissions for each service
- **Email Authentication**: SPF, DKIM, and DMARC configured
- **Encryption**: S3 bucket encrypted at rest
- **Access Control**: Only authorized email addresses can send via SES
- **Temporary Storage**: Emails deleted after 30 days

## 💰 Cost Estimation

Approximate AWS costs for moderate usage (100 invoices/month):

- **Lambda**: ~$0.10/month (100 invocations × 30s avg)
- **SES**: ~$1.00/month (200 emails × $0.10/1000)
- **S3**: ~$0.01/month (minimal storage, 30-day lifecycle)
- **Bedrock Nova**: ~$5.00/month (varies by token usage)
- **Route53**: ~$0.50/month (DNS queries)

**Total: ~$6.61/month**

## 🐛 Troubleshooting

### Common Issues

1. **Emails not received**:
   - Check DNS propagation: `dig MX katechat.tech`
   - Verify SES domain verification in AWS console
   - Check spam folder

2. **Lambda function errors**:
   - Check CloudWatch logs: `/aws/lambda/invoice-parser`
   - Verify Bedrock model permissions
   - Ensure S3 bucket permissions

3. **PDF parsing issues**:
   - Test locally with `test_local.py`
   - Check if PDF is text-based (not scanned image)
   - Verify Bedrock Nova model availability in region

### Monitoring

- **CloudWatch Logs**: Function execution details
- **SES Metrics**: Email delivery statistics  
- **Lambda Metrics**: Invocation count, duration, errors

## 🔧 Configuration

### Environment Variables (Lambda)

- `AWS_REGION`: Deployment region (default: eu-central-1)
- `SES_S3_BUCKET`: S3 bucket for email storage (auto-generated)
- `FROM_EMAIL`: Sender email address (invoice-bot@katechat.tech)

### Terraform Variables

- `aws_region`: AWS region for deployment
- `domain_name`: Domain for SES (katechat.tech)
- `certificate_arn`: ACM certificate ARN (provided)
- `route53_zone_id`: Route53 zone ID (provided)

## 📈 Scaling

The system is designed to scale automatically:

- **Lambda**: Scales to handle concurrent email processing
- **SES**: No limits on email volume (within SES limits)
- **S3**: Unlimited storage capacity
- **Bedrock**: Handles multiple simultaneous requests

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

For issues and questions:

1. Check the troubleshooting section above
2. Review CloudWatch logs for errors
3. Test locally using the provided scripts
4. Open an issue in the GitHub repository

---

**Built with ❤️ using AWS Lambda, Bedrock Nova, SES, and Terraform**