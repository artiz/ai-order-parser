#!/bin/bash

# AI Invoice Parser Deployment Script
set -e

echo "🚀 Starting AI Invoice Parser Deployment"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check if AWS CLI is installed and configured
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Run 'aws configure' first.${NC}"
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform is not installed. Please install it first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Get current AWS account and region
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")

echo "AWS Account: $AWS_ACCOUNT"
echo "AWS Region: $AWS_REGION"

# Change to infrastructure directory
cd infrastructure

echo -e "${YELLOW}Initializing Terraform...${NC}"
terraform init

echo -e "${YELLOW}Planning Terraform deployment...${NC}"
terraform plan

echo -e "${YELLOW}Do you want to proceed with the deployment? (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo -e "${YELLOW}Applying Terraform configuration...${NC}"
terraform apply -auto-approve

echo -e "${GREEN}✅ Infrastructure deployment completed!${NC}"

# Display outputs
echo ""
echo "📋 Deployment Summary:"
echo "======================"
terraform output

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo "📧 Your invoice processing email is ready at: invoice-bot@katechat.tech"
echo ""
echo "📝 Next steps:"
echo "1. Wait for DNS propagation (may take up to 24 hours)"
echo "2. Test by sending an email with PDF attachment to invoice-bot@katechat.tech"
echo "3. Check CloudWatch logs for debugging if needed"
echo ""
echo "🧪 For local testing:"
echo "cd processor"
echo "python test_local.py test-all"