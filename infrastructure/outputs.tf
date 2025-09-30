# Outputs
output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.invoice_parser.arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.invoice_parser.function_name
}

output "ses_domain_identity" {
  description = "SES domain identity"
  value       = aws_ses_domain_identity.main.domain
}

output "ses_verification_token" {
  description = "SES domain verification token"
  value       = aws_ses_domain_identity.main.verification_token
}

output "s3_bucket_name" {
  description = "S3 bucket name for SES emails"
  value       = aws_s3_bucket.ses_emails.bucket
}

output "invoice_email_address" {
  description = "Email address for invoice processing"
  value       = var.email_address
}

output "dkim_tokens" {
  description = "DKIM tokens for domain verification"
  value       = aws_ses_domain_dkim.main.dkim_tokens
}