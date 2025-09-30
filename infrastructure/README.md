# AI Invoice Parser Infrastructure

This Terraform configuration deploys the infrastructure for the AI-based invoice parser system.

## Architecture

- **AWS Lambda**: Processes incoming emails and parses PDF invoices using AWS Bedrock Nova
- **AWS SES**: Receives emails and triggers Lambda function
- **AWS S3**: Stores incoming emails temporarily
- **AWS Bedrock**: Nova model for AI-powered invoice parsing
- **Route53**: DNS configuration for the domain

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform installed (>= 1.0)
3. Domain `katechat.tech` already registered and managed by Route53
4. ACM certificate for the domain

## Configuration

The infrastructure uses the following predefined values:
- Domain: `katechat.tech`
- Email: `invoice-bot@katechat.tech`
- Certificate ARN: `arn:aws:acm:eu-central-1:508414931829:certificate/70c77f1e-3a3f-4530-b393-48bedf6fed60`
- Route53 Zone ID: `Z08280421TLAENXYORVOR`

## Deployment

1. Initialize Terraform:
```bash
terraform init
```

2. Plan the deployment:
```bash
terraform plan
```

3. Apply the configuration:
```bash
terraform apply
```

## What Gets Created

1. **S3 Bucket**: Stores incoming emails from SES
2. **Lambda Function**: Processes emails and parses PDFs
3. **IAM Roles & Policies**: Permissions for Lambda to access required services
4. **SES Configuration**: 
   - Domain identity verification
   - DKIM, SPF, DMARC records
   - MX record for email receiving
   - Receipt rules to trigger Lambda
5. **CloudWatch Log Group**: For Lambda function logs

## Email Flow

1. Email sent to `invoice-bot@katechat.tech`
2. SES receives email and stores in S3
3. SES triggers Lambda function
4. Lambda extracts PDF attachments
5. Lambda uses Bedrock Nova to parse invoice data
6. Lambda sends results back to sender via SES

## DNS Records Created

The following DNS records are automatically created in Route53:

- **SES Verification**: `_amazonses.katechat.tech` (TXT)
- **DKIM**: Three CNAME records for email authentication  
- **SPF**: `katechat.tech` (TXT) - `v=spf1 include:amazonses.com ~all`
- **DMARC**: `_dmarc.katechat.tech` (TXT) - `v=DMARC1; p=quarantine`
- **MX**: `katechat.tech` (MX) - Points to AWS SES

## Monitoring

- Lambda logs are available in CloudWatch under `/aws/lambda/invoice-parser`
- S3 bucket has lifecycle policy to delete emails after 30 days
- All resources are tagged for easy identification

## Security

- Lambda function has minimal IAM permissions
- S3 bucket is encrypted and has restricted access
- SES is configured with SPF, DKIM, and DMARC
- Only invoice-bot@katechat.tech can send emails via SES

## Cleanup

To destroy all resources:
```bash
terraform destroy
```

## Cost Considerations

- Lambda: Pay per invocation and execution time
- SES: Pay per email sent/received
- S3: Minimal storage costs (30-day lifecycle)
- Bedrock: Pay per token for Nova model usage
- Route53: Minimal costs for DNS queries