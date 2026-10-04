locals {
  app_account_id          = data.aws_caller_identity.app.account_id
  application_name_prefix = trimsuffix(var.application_role_prefix, "-")
  application_role_arns   = "arn:aws:iam::${local.app_account_id}:role/${var.application_role_prefix}*"
  application_secret_arns = "arn:aws:secretsmanager:${var.aws_region}:${local.app_account_id}:secret:${local.application_name_prefix}/*"
  application_bucket_arns = "arn:aws:s3:::${local.application_name_prefix}-static-*"
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
              for environment in var.github_environments :
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
        Sid      = "ListStateBucket"
        Effect   = "Allow"
        Action   = "s3:ListBucket"
        Resource = aws_s3_bucket.terraform_state.arn
      },
      {
        Sid    = "UseApplicationState"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.terraform_state.arn}/app/*"
      },
      {
        Sid      = "AssumeDnsRole"
        Effect   = "Allow"
        Action   = "sts:AssumeRole"
        Resource = var.dns_role_arn
      },
      {
        Sid    = "ManageApplicationServices"
        Effect = "Allow"
        Action = [
          "acm:*",
          "cloudfront:*",
          "cognito-idp:*",
          "ecr:*",
          "ecs:*",
          "elasticache:*",
          "elasticloadbalancing:*",
          "lambda:*",
          "logs:*",
          "rds:*"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = var.aws_region
          }
        }
      },
      {
        Sid    = "ManageNetworking"
        Effect = "Allow"
        Action = [
          "ec2:Describe*",
          "ec2:GetManagedPrefixListEntries",
          "ec2:CreateTags",
          "ec2:DeleteTags",
          "ec2:CreateVpc",
          "ec2:DeleteVpc",
          "ec2:ModifyVpcAttribute",
          "ec2:CreateSubnet",
          "ec2:DeleteSubnet",
          "ec2:ModifySubnetAttribute",
          "ec2:CreateInternetGateway",
          "ec2:DeleteInternetGateway",
          "ec2:AttachInternetGateway",
          "ec2:DetachInternetGateway",
          "ec2:CreateRouteTable",
          "ec2:DeleteRouteTable",
          "ec2:AssociateRouteTable",
          "ec2:DisassociateRouteTable",
          "ec2:ReplaceRouteTableAssociation",
          "ec2:CreateRoute",
          "ec2:DeleteRoute",
          "ec2:ReplaceRoute",
          "ec2:CreateSecurityGroup",
          "ec2:DeleteSecurityGroup",
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:AuthorizeSecurityGroupEgress",
          "ec2:RevokeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupEgress",
          "ec2:UpdateSecurityGroupRuleDescriptionsIngress",
          "ec2:UpdateSecurityGroupRuleDescriptionsEgress",
          "ec2:ModifySecurityGroupRules",
          "ec2:DeleteNetworkInterface"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = var.aws_region
          }
        }
      },
      {
        Sid      = "ManageApplicationSecrets"
        Effect   = "Allow"
        Action   = "secretsmanager:*"
        Resource = local.application_secret_arns
      },
      {
        Sid    = "ManageStaticBucket"
        Effect = "Allow"
        Action = "s3:*"
        Resource = [
          local.application_bucket_arns,
          "${local.application_bucket_arns}/*"
        ]
      },
      {
        Sid    = "UseManagedKeysThroughServices"
        Effect = "Allow"
        Action = [
          "kms:DescribeKey",
          "kms:CreateGrant",
          "kms:Decrypt",
          "kms:GenerateDataKey*"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = [
              "rds.${var.aws_region}.amazonaws.com",
              "elasticache.${var.aws_region}.amazonaws.com",
              "secretsmanager.${var.aws_region}.amazonaws.com"
            ]
          }
        }
      },
      {
        Sid    = "ManageBoundedApplicationRoles"
        Effect = "Allow"
        Action = [
          "iam:CreateRole",
          "iam:PutRolePermissionsBoundary",
          "iam:PutRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy"
        ]
        Resource = local.application_role_arns
        Condition = {
          StringEquals = {
            "iam:PermissionsBoundary" = aws_iam_policy.application_role_boundary.arn
          }
        }
      },
      {
        Sid    = "ReadAndMaintainApplicationRoles"
        Effect = "Allow"
        Action = [
          "iam:GetRole",
          "iam:DeleteRole",
          "iam:UpdateRole",
          "iam:UpdateRoleDescription",
          "iam:UpdateAssumeRolePolicy",
          "iam:TagRole",
          "iam:UntagRole",
          "iam:ListRoleTags",
          "iam:GetRolePolicy",
          "iam:ListRolePolicies",
          "iam:ListAttachedRolePolicies",
          "iam:ListInstanceProfilesForRole"
        ]
        Resource = local.application_role_arns
      },
      {
        Sid      = "PassApplicationRoles"
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = local.application_role_arns
        Condition = {
          StringEquals = {
            "iam:PassedToService" = [
              "ecs-tasks.amazonaws.com",
              "lambda.amazonaws.com"
            ]
          }
        }
      },
      {
        Sid    = "ReadManagedPolicies"
        Effect = "Allow"
        Action = [
          "iam:GetPolicy",
          "iam:GetPolicyVersion",
          "iam:ListPolicies"
        ]
        Resource = "*"
      },
      {
        Sid      = "CreateServiceLinkedRoles"
        Effect   = "Allow"
        Action   = "iam:CreateServiceLinkedRole"
        Resource = "arn:aws:iam::${local.app_account_id}:role/aws-service-role/*"
      },
      {
        Sid      = "KeepRoleBoundaries"
        Effect   = "Deny"
        Action   = "iam:DeleteRolePermissionsBoundary"
        Resource = "*"
      }
    ]
  })
}
