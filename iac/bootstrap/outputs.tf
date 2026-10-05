output "terraform_deployer_role_arn" {
  description = "Application-account role to use for Terraform deployments"
  value       = aws_iam_role.terraform_deployer.arn
}

output "github_deployer_role_arn" {
  description = "Application-account role assumed by GitHub Actions for code deployments"
  value       = aws_iam_role.github_deployer.arn
}

output "application_role_boundary_arn" {
  description = "Permissions boundary required on IAM roles created by the application stack"
  value       = aws_iam_policy.application_role_boundary.arn
}

output "dns_role_arn" {
  description = "DNS-account role ARN passed to iac/app as dns_role_arn"
  value       = var.dns_role_arn
}

output "terraform_state_bucket_name" {
  description = "S3 bucket used by iac/app for Terraform state"
  value       = aws_s3_bucket.terraform_state.id
}
