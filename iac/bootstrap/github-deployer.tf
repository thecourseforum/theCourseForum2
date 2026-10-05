locals {
  app_account_id          = data.aws_caller_identity.app.account_id
  application_name_prefix = trimsuffix(var.application_role_prefix, "-")
  application_role_arns   = "arn:aws:iam::${local.app_account_id}:role/${var.application_role_prefix}*"
  application_secret_arns = "arn:aws:secretsmanager:${var.aws_region}:${local.app_account_id}:secret:${local.application_name_prefix}/*"
  application_bucket_arns = "arn:aws:s3:::${local.application_name_prefix}-static-*"
  application_cluster_arn = "arn:aws:ecs:${var.aws_region}:${local.app_account_id}:cluster/${local.application_name_prefix}-cluster"
}

resource "aws_iam_policy" "application_role_boundary" {
  provider    = aws.app
  name        = "${local.application_name_prefix}-role-boundary"
  description = "Permissions boundary for IAM roles created by the application Terraform stack"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "PullImages"
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Sid    = "WriteLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Sid      = "ReadApplicationSecrets"
        Effect   = "Allow"
        Action   = "secretsmanager:GetSecretValue"
        Resource = local.application_secret_arns
      },
      {
        Sid      = "ListStaticBucket"
        Effect   = "Allow"
        Action   = "s3:ListBucket"
        Resource = local.application_bucket_arns
      },
      {
        Sid    = "UseStaticObjects"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectAcl",
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:DeleteObject"
        ]
        Resource = "${local.application_bucket_arns}/*"
      }
    ]
  })

  tags = {
    Name      = "${local.application_name_prefix}-role-boundary"
    ManagedBy = "bootstrap-terraform"
  }
}

resource "aws_iam_role" "github_deployer" {
  provider = aws.app
  name     = var.github_deployer_role_name

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
              for environment in var.code_deploy_github_environments :
              "repo:${var.github_repository}:environment:${environment}"
            ]
          }
        }
      }
    ]
  })

  tags = {
    Name      = var.github_deployer_role_name
    ManagedBy = "bootstrap-terraform"
  }
}

resource "aws_iam_role_policy" "github_deployer" {
  provider = aws.app
  name     = "${var.github_deployer_role_name}-policy"
  role     = aws_iam_role.github_deployer.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "LogInToEcr"
        Effect   = "Allow"
        Action   = "ecr:GetAuthorizationToken"
        Resource = "*"
      },
      {
        Sid    = "PushApplicationImages"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:BatchGetImage",
          "ecr:DescribeImages",
          "ecr:GetDownloadUrlForLayer",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage"
        ]
        Resource = "arn:aws:ecr:${var.aws_region}:${local.app_account_id}:repository/${var.application_role_prefix}*"
      },
      {
        Sid    = "RegisterTaskDefinitions"
        Effect = "Allow"
        Action = [
          "ecs:DescribeTaskDefinition",
          "ecs:RegisterTaskDefinition"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = var.aws_region
          }
        }
      },
      {
        Sid      = "RunReleaseTasks"
        Effect   = "Allow"
        Action   = "ecs:RunTask"
        Resource = "arn:aws:ecs:${var.aws_region}:${local.app_account_id}:task-definition/${var.application_role_prefix}*:*"
        Condition = {
          ArnEquals = {
            "ecs:cluster" = local.application_cluster_arn
          }
        }
      },
      {
        Sid      = "ReadReleaseTasks"
        Effect   = "Allow"
        Action   = "ecs:DescribeTasks"
        Resource = "arn:aws:ecs:${var.aws_region}:${local.app_account_id}:task/${local.application_name_prefix}-cluster/*"
      },
      {
        Sid    = "DeployApplicationServices"
        Effect = "Allow"
        Action = [
          "ecs:DescribeServices",
          "ecs:UpdateService"
        ]
        Resource = "arn:aws:ecs:${var.aws_region}:${local.app_account_id}:service/${local.application_name_prefix}-cluster/${var.application_role_prefix}*"
      },
      {
        Sid      = "PassApplicationRoles"
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = local.application_role_arns
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "ecs-tasks.amazonaws.com"
          }
        }
      }
    ]
  })
}
