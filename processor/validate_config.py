#!/usr/bin/env python3
"""
Configuration validation script for the invoice parser.
"""

import os
import sys

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Loaded environment variables from .env file")
except ImportError:
    print("⚠ python-dotenv not installed. Using system environment variables only.")
    print("  Install with: pip install python-dotenv")

def validate_config():
    """Validate configuration and AWS credentials."""
    
    print("\n🔍 Configuration Validation")
    print("=" * 50)
    
    # Check required environment variables
    aws_region = os.environ.get('AWS_REGION')
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    
    print(f"AWS_REGION: {aws_region or 'NOT SET (will default to us-east-1)'}")
    print(f"AWS_ACCESS_KEY_ID: {'SET' if aws_access_key else 'NOT SET'}")
    print(f"AWS_SECRET_ACCESS_KEY: {'SET' if aws_secret_key else 'NOT SET'}")
    print(f"LOG_LEVEL: {log_level}")
    
    # Test AWS connection
    print("\n🔗 Testing AWS Connection")
    print("-" * 30)
    
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        
        # Create clients with environment credentials
        kwargs = {}
        if aws_region:
            kwargs['region_name'] = aws_region
        if aws_access_key and aws_secret_key:
            kwargs['aws_access_key_id'] = aws_access_key
            kwargs['aws_secret_access_key'] = aws_secret_key
        
        # Test STS (to verify credentials)
        sts_client = boto3.client('sts', **kwargs)
        identity = sts_client.get_caller_identity()
        print(f"✓ AWS credentials valid")
        print(f"  Account: {identity.get('Account')}")
        print(f"  User/Role: {identity.get('Arn')}")
        
        # Test Bedrock access
        bedrock_client = boto3.client('bedrock-runtime', **kwargs)
        # Note: We can't easily test Bedrock without making a costly API call
        print(f"✓ Bedrock client initialized")
        
        # Test SES access  
        ses_client = boto3.client('ses', **kwargs)
        print(f"✓ SES client initialized")
        
    except NoCredentialsError:
        print("❌ AWS credentials not found")
        print("   Configure credentials in .env file or run 'aws configure'")
        return False
    except ClientError as e:
        print(f"❌ AWS error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing AWS connection: {e}")
        return False
    
    print("\n✅ Configuration validation completed successfully!")
    return True

if __name__ == "__main__":
    success = validate_config()
    sys.exit(0 if success else 1)