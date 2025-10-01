# Create deployment package
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "../processor"
  output_path = local.lambda_zip_path
  excludes    = ["__pycache__", "*.pyc", ".git", "README.md", "test_local.py", ".env", ".env.example"]
}

# Lambda function
resource "aws_lambda_function" "invoice_parser" {
  filename         = local.lambda_zip_path
  function_name    = local.function_name
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      REGION      = var.aws_region
      S3_BUCKET   = aws_s3_bucket.ses_emails.bucket
      FROM_EMAIL      = var.email_address
      RESULT_EMAIL    = var.result_email_address
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy,
    aws_cloudwatch_log_group.lambda_logs,
  ]
}

# Lambda permission for SES
resource "aws_lambda_permission" "allow_ses" {
  statement_id  = "AllowExecutionFromSES"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.invoice_parser.function_name
  principal     = "ses.amazonaws.com"
  source_account = data.aws_caller_identity.current.account_id
}