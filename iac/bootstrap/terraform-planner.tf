resource "aws_iam_role" "terraform_planner" {
  provider = aws.app
  name     = var.terraform_planner_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "sts:AssumeRoleWithWebIdentity"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions.arn
        }
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
            "token.actions.githubusercontent.com:sub" = [
              for environment in var.terraform_plan_github_environments :
              "repo:${var.github_repository}:environment:${environment}"
            ]
          }
        }
      }
    ]
  })

  tags = {
    Name      = var.terraform_planner_role_name
    ManagedBy = "bootstrap-terraform"
  }
}

resource "aws_iam_role_policy_attachment" "terraform_planner_read_only" {
  provider   = aws.app
  role       = aws_iam_role.terraform_planner.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

resource "aws_iam_role_policy" "terraform_planner" {
  provider = aws.app
  name     = "${var.terraform_planner_role_name}-policy"
  role     = aws_iam_role.terraform_planner.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "UseStateKey"
        Effect   = "Allow"
        Action   = ["kms:Decrypt", "kms:GenerateDataKey"]
        Resource = aws_kms_key.terraform_state.arn
      },
      {
        Sid      = "WriteStateLock"
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:DeleteObject"]
        Resource = "${aws_s3_bucket.terraform_state.arn}/app/terraform.tfstate.tflock"
      },
      {
        Sid      = "WriteSavedPlans"
        Effect   = "Allow"
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.terraform_state.arn}/plans/*"
      },
      {
        Sid      = "ReadApplicationSecrets"
        Effect   = "Allow"
        Action   = "secretsmanager:GetSecretValue"
        Resource = local.application_secret_arns
      },
      {
        Sid      = "AssumeDnsRole"
        Effect   = "Allow"
        Action   = "sts:AssumeRole"
        Resource = var.dns_role_arn
      },
      {
        Sid      = "DenyDatabaseDumps"
        Effect   = "Deny"
        Action   = "s3:GetObject*"
        Resource = "${local.application_dump_bucket_arns}/*"
      }
    ]
  })
}
