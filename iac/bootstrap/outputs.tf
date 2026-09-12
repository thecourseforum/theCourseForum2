output "terraform_deployer_role_arn" {
  description = "Application-account role to use for Terraform deployments"
  value       = aws_iam_role.terraform_deployer.arn
}

output "dns_role_arn" {
  description = "DNS-account role ARN passed to iac/app as dns_role_arn"
  value       = aws_iam_role.dns.arn
}

output "terraform_state_bucket_name" {
  description = "S3 bucket used by iac/app for Terraform state"
  value       = aws_s3_bucket.terraform_state.id
}
