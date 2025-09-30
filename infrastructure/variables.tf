# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "domain_name" {
  description = "Domain name for SES"
  type        = string
  default     = "katechat.tech"
}

variable "certificate_arn" {
  description = "ACM certificate ARN"
  type        = string
  default     = "arn:aws:acm:eu-central-1:508414931829:certificate/70c77f1e-3a3f-4530-b393-48bedf6fed60"
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID"
  type        = string
  default     = "Z08280421TLAENXYORVOR"
}

variable "email_address" {
  description = "Email address for invoice processing"
  type        = string
  default     = "invoice-bot@katechat.tech"
}

variable "result_email_address" {
  description = "Email address to send results to"
  type        = string
  default     = "artem.kustikov@gmail.com"
}


# Local variables
locals {
  function_name = "invoice-parser"
  lambda_zip_path = "lambda_deployment.zip"
}