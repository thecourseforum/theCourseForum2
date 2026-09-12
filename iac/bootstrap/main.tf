provider "aws" {
  alias   = "app"
  profile = var.app_profile
  region  = var.aws_region
}

provider "aws" {
  alias   = "dns"
  profile = var.dns_profile
  region  = "us-east-1"
}

data "aws_caller_identity" "app" {
  provider = aws.app
}

resource "aws_iam_role" "terraform_deployer" {
  provider = aws.app
  name     = var.terraform_deployer_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = {
        AWS = var.deployer_principal_arn
      }
    }]
  })

  tags = {
    Name      = var.terraform_deployer_role_name
    ManagedBy = "bootstrap-terraform"
  }
}

# Broad non-IAM access for initial testing. Replace with a reviewed policy
# before using this role for production deployments.
resource "aws_iam_role_policy_attachment" "terraform_deployer_power_user" {
  provider   = aws.app
  role       = aws_iam_role.terraform_deployer.name
  policy_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
}

# PowerUserAccess intentionally excludes IAM. These permissions allow the
# deployment role to create the IAM roles used by the application stack.
resource "aws_iam_role_policy" "terraform_deployer_iam" {
  provider = aws.app
  name     = "${var.terraform_deployer_role_name}-iam"
  role     = aws_iam_role.terraform_deployer.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:GetRole",
          "iam:UpdateAssumeRolePolicy",
          "iam:TagRole",
          "iam:UntagRole",
          "iam:ListRoleTags",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy",
          "iam:PutRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:GetRolePolicy",
          "iam:ListRolePolicies",
          "iam:ListAttachedRolePolicies",
          "iam:ListInstanceProfilesForRole",
          "iam:GetPolicy",
          "iam:ListPolicies",
          "iam:CreateServiceLinkedRole"
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = "arn:aws:iam::${data.aws_caller_identity.app.account_id}:role/${var.application_role_prefix}*"
      },
      {
        Effect   = "Allow"
        Action   = "sts:AssumeRole"
        Resource = aws_iam_role.dns.arn
      }
    ]
  })
}

resource "aws_iam_role" "dns" {
  provider = aws.dns
  name     = var.dns_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = {
        AWS = aws_iam_role.terraform_deployer.arn
      }
    }]
  })

  tags = {
    Name      = var.dns_role_name
    ManagedBy = "bootstrap-terraform"
  }
}

resource "aws_iam_role_policy" "dns_route53" {
  provider = aws.dns
  name     = "${var.dns_role_name}-route53"
  role     = aws_iam_role.dns.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "route53:GetHostedZone",
          "route53:ListResourceRecordSets",
          "route53:ListTagsForResource",
          "route53:ChangeResourceRecordSets"
        ]
        Resource = [
          "arn:aws:route53:::hostedzone/Z06158912Y7SI8FYZM5IA",
          "arn:aws:route53:::hostedzone/Z09238113JE0PLS5VY8RQ"
        ]
      },
      {
        Effect   = "Allow"
        Action   = "route53:GetChange"
        Resource = "arn:aws:route53:::change/*"
      }
    ]
  })
}
