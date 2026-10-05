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

variable "terraform_github_environments" {
  description = "GitHub Actions environments permitted to assume the Terraform deployer role"
  type        = list(string)
  default     = ["terraform-plan", "terraform-test"]
}

variable "code_deploy_github_environments" {
  description = "GitHub Actions environments permitted to assume the GitHub deployer role"
  type        = list(string)
  default     = ["aws-deploy"]
}

variable "github_repository" {
  description = "GitHub owner/repository permitted to assume the deployer roles through OIDC"
  type        = string
  default     = "thecourseforum/theCourseForum2"
}

variable "github_deployer_role_name" {
  description = "Role assumed by GitHub Actions through OIDC for application code deployments"
  type        = string
  default     = "tcf-github-deployer"
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
  description = "Prefix for application resources and IAM roles that the deployers may manage"
  type        = string
  default     = "iac-test-"
}

variable "terraform_state_bucket_name" {
  description = "Globally unique S3 bucket name for application Terraform state"
  type        = string
  default     = "tcf-terraform-state-099933383052"
}
