data "archive_file" "require_virginia_email" {
  type        = "zip"
  source_file = "${path.module}/lambda/require_virginia_email/index.mjs"
  output_path = "${path.module}/.terraform/build/require_virginia_email.zip"
}

resource "aws_iam_role" "require_virginia_email" {
  name                 = "${local.name_prefix}-require-virginia-email-role"
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
    Name = "${local.name_prefix}-require-virginia-email-role"
  }
}

resource "aws_iam_role_policy_attachment" "require_virginia_email_logs" {
  role       = aws_iam_role.require_virginia_email.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_cloudwatch_log_group" "require_virginia_email" {
  name              = "/aws/lambda/${local.name_prefix}-require-virginia-email"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${local.name_prefix}-require-virginia-email-logs"
  }
}

resource "aws_lambda_function" "require_virginia_email" {
  function_name    = "${local.name_prefix}-require-virginia-email"
  role             = aws_iam_role.require_virginia_email.arn
  runtime          = "nodejs22.x"
  handler          = "index.handler"
  filename         = data.archive_file.require_virginia_email.output_path
  source_code_hash = data.archive_file.require_virginia_email.output_base64sha256

  depends_on = [
    aws_iam_role_policy_attachment.require_virginia_email_logs,
    aws_cloudwatch_log_group.require_virginia_email,
  ]

  tags = {
    Name = "${local.name_prefix}-require-virginia-email"
  }
}

resource "aws_lambda_permission" "require_virginia_email_cognito" {
  statement_id  = "AllowCognitoInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.require_virginia_email.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = aws_cognito_user_pool.main.arn
}
