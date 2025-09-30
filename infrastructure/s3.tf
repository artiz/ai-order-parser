# S3 bucket for storing SES emails
resource "aws_s3_bucket" "ses_emails" {
  bucket = "${local.function_name}-ses-emails-${random_id.bucket_suffix.hex}"
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket_versioning" "ses_emails" {
  bucket = aws_s3_bucket.ses_emails.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ses_emails" {
  bucket = aws_s3_bucket.ses_emails.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "ses_emails" {
  bucket = aws_s3_bucket.ses_emails.id

  rule {
    id     = "delete_old_emails"
    status = "Enabled"

    filter {
      prefix = "emails/"
    }

    expiration {
      days = 30
    }
  }
}

# S3 bucket policy to allow SES to write emails
resource "aws_s3_bucket_policy" "ses_emails" {
  bucket = aws_s3_bucket.ses_emails.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowSESPuts"
        Effect = "Allow"
        Principal = {
          Service = "ses.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.ses_emails.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:Referer" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}