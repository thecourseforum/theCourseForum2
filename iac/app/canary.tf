data "archive_file" "canary_heartbeat" {
  type        = "zip"
  output_path = "${path.module}/.terraform/build/canary-heartbeat.zip"

  source {
    content  = file("${path.module}/canary/heartbeat.js")
    filename = "nodejs/node_modules/heartbeat.js"
  }
}

resource "aws_s3_bucket" "synthetics_artifacts" {
  bucket_prefix = "${local.name_prefix}-synthetics-artifacts-"
  force_destroy = true

  tags = {
    Name = "${local.name_prefix}-synthetics-artifacts"
  }
}

resource "aws_s3_bucket_public_access_block" "synthetics_artifacts" {
  bucket = aws_s3_bucket.synthetics_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_iam_role" "synthetics_canary" {
  name                 = "${local.name_prefix}-synthetics-canary-role"
  permissions_boundary = local.role_permissions_boundary_arn

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${local.name_prefix}-synthetics-canary-role"
  }
}

resource "aws_iam_role_policy" "synthetics_canary" {
  name = "${local.name_prefix}-synthetics-canary"
  role = aws_iam_role.synthetics_canary.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
        ]
        Resource = "${aws_s3_bucket.synthetics_artifacts.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetBucketLocation"]
        Resource = aws_s3_bucket.synthetics_artifacts.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:ListAllMyBuckets"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/cwsyn-*"
      },
      {
        Effect   = "Allow"
        Action   = "cloudwatch:PutMetricData"
        Resource = "*"
        Condition = {
          StringEquals = {
            "cloudwatch:namespace" = "CloudWatchSynthetics"
          }
        }
      },
      {
        Effect   = "Allow"
        Action   = ["xray:PutTraceSegments"]
        Resource = "*"
      },
    ]
  })
}

resource "aws_synthetics_canary" "heartbeat" {
  name                 = "tcf-site-heartbeat"
  artifact_s3_location = "s3://${aws_s3_bucket.synthetics_artifacts.id}/canary"
  execution_role_arn   = aws_iam_role.synthetics_canary.arn
  runtime_version      = "syn-nodejs-puppeteer-18.0"
  handler              = "heartbeat.handler"
  zip_file             = data.archive_file.canary_heartbeat.output_path
  start_canary         = true

  success_retention_period = 7
  failure_retention_period = 30

  schedule {
    expression          = "rate(5 minutes)"
    duration_in_seconds = 0

    retry_config {
      max_retries = 0
    }
  }

  run_config {
    timeout_in_seconds = 60
    memory_in_mb       = 1536
    active_tracing     = false
    ephemeral_storage  = 1024

    environment_variables = {
      TCF_CANARY_SECRET = random_password.waf_canary_header.result
      TCF_SITE_URL      = "https://${var.domain_name}"
    }
  }

  depends_on = [
    aws_iam_role_policy.synthetics_canary,
    aws_s3_bucket_public_access_block.synthetics_artifacts,
  ]

  tags = {
    Name = "${local.name_prefix}-site-heartbeat"
  }
}

locals {
  canary_log_group_name = "/aws/lambda/${split(":", aws_synthetics_canary.heartbeat.engine_arn)[6]}"
}

import {
  to = aws_cloudwatch_log_group.canary
  id = local.canary_log_group_name
}

resource "aws_cloudwatch_log_group" "canary" {
  name              = local.canary_log_group_name
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${local.name_prefix}-canary-logs"
  }
}
