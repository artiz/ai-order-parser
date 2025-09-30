# SES domain identity
resource "aws_ses_domain_identity" "main" {
  domain = var.domain_name
}

# SES domain verification
resource "aws_route53_record" "ses_verification" {
  zone_id = var.route53_zone_id
  name    = "_amazonses.${var.domain_name}"
  type    = "TXT"
  ttl     = "600"
  records = [aws_ses_domain_identity.main.verification_token]
}

# Wait for SES domain verification
resource "aws_ses_domain_identity_verification" "main" {
  domain = aws_ses_domain_identity.main.id

  depends_on = [aws_route53_record.ses_verification]
}

# SES email identity (for sending emails)
resource "aws_ses_email_identity" "invoice_bot" {
  email = var.email_address
}

# SES email identity for result emails
resource "aws_ses_email_identity" "result_email" {
  email = var.result_email_address
}

# SES DKIM
resource "aws_ses_domain_dkim" "main" {
  domain = aws_ses_domain_identity.main.domain
}

# DKIM records
resource "aws_route53_record" "dkim" {
  count   = 3
  zone_id = var.route53_zone_id
  name    = "${aws_ses_domain_dkim.main.dkim_tokens[count.index]}._domainkey.${var.domain_name}"
  type    = "CNAME"
  ttl     = "600"
  records = ["${aws_ses_domain_dkim.main.dkim_tokens[count.index]}.dkim.amazonses.com"]
}

# SPF record
resource "aws_route53_record" "spf" {
  zone_id = var.route53_zone_id
  name    = var.domain_name
  type    = "TXT"
  ttl     = "600"
  records = ["v=spf1 include:amazonses.com ~all"]
}

# DMARC record
resource "aws_route53_record" "dmarc" {
  zone_id = var.route53_zone_id
  name    = "_dmarc.${var.domain_name}"
  type    = "TXT"
  ttl     = "600"
  records = ["v=DMARC1; p=quarantine; rua=mailto:dmarc@${var.domain_name}"]
}

# MX record for receiving emails
resource "aws_route53_record" "mx" {
  zone_id = var.route53_zone_id
  name    = var.domain_name
  type    = "MX"
  ttl     = "600"
  records = ["10 inbound-smtp.${var.aws_region}.amazonaws.com"]
}

# SES receipt rule set
resource "aws_ses_receipt_rule_set" "main" {
  rule_set_name = "${local.function_name}-ruleset"
}

# Make the rule set active
resource "aws_ses_active_receipt_rule_set" "main" {
  rule_set_name = aws_ses_receipt_rule_set.main.rule_set_name
}

# SES receipt rule
resource "aws_ses_receipt_rule" "invoice_processing" {
  name          = "${local.function_name}-rule"
  rule_set_name = aws_ses_receipt_rule_set.main.rule_set_name
  recipients    = [var.email_address]
  enabled       = true
  scan_enabled  = true

  s3_action {
    bucket_name = aws_s3_bucket.ses_emails.bucket
    object_key_prefix = "emails/"
    position    = 1
  }

  lambda_action {
    function_arn    = aws_lambda_function.invoice_parser.arn
    invocation_type = "Event"
    position        = 2
  }

  depends_on = [
    aws_lambda_permission.allow_ses,
    aws_ses_domain_identity_verification.main
  ]
}