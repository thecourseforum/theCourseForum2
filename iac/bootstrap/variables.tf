variable "app_profile" {
  description = "AWS CLI profile with administrator access in the application account"
  type        = string
}

variable "aws_region" {
  description = "Region for application-account IAM operations"
  type        = string
  default     = "us-east-1"
}

variable "deployer_principal_arn" {
  description = "IAM user or role allowed to assume the application Terraform deployer role"
  type        = string
}

variable "github_repository" {
  description = "GitHub owner/repository permitted to assume the Terraform deployer role from the terraform-test environment"
  type        = string
  default     = "thecourseforum/theCourseForum2"
}

variable "terraform_deployer_role_name" {
  description = "Role created in the application account for Terraform deployments"
  type        = string
  default     = "tcf-terraform-deployer"
}

variable "dns_role_arn" {
  description = "Existing DNS-account role that the deployer may assume for Route 53 changes"
  type        = string
  default     = "arn:aws:iam::011713309463:role/tcf-terraform-dns"
}

variable "application_role_prefix" {
  description = "Prefix for application IAM roles that the deployer may pass to ECS"
  type        = string
  default     = "iac-test-"
}

variable "terraform_state_bucket_name" {
  description = "Globally unique S3 bucket name for application Terraform state"
  type        = string
  default     = "tcf-terraform-state-099933383052"
}
