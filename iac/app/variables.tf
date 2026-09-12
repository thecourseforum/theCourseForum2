variable "project_name" {
  description = "Project name used in resource naming"
  type        = string
  default     = "iac"
}

variable "environment" {
  description = "Environment name (test, staging, prod)"
  type        = string
  default     = "test"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "thecourseforumtest.com"

  validation {
    condition     = contains(["thecourseforum.com", "thecourseforumtest.com"], var.domain_name)
    error_message = "domain_name must be either thecourseforum.com or thecourseforumtest.com."
  }
}

variable "dns_role_arn" {
  description = "ARN of the role Terraform assumes in the separate Route 53 account"
  type        = string

  validation {
    condition     = can(regex("^arn:aws:iam::011713309463:role/.+", var.dns_role_arn))
    error_message = "dns_role_arn must be an IAM role ARN in Route 53 account 011713309463."
  }
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "availability_zones" {
  description = "Availability zones for multi-AZ deployment"
  type        = list(string)
  default     = ["us-east-1c", "us-east-1f"]
}

variable "ecs_task_cpu" {
  description = "CPU units for ECS task (256 = 0.25 vCPU)"
  type        = number
  default     = 512
}

variable "ecs_task_memory" {
  description = "Memory for ECS task in MB"
  type        = number
  default     = 2048
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 1
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "rds_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "18.1"
}

variable "ecr_image_tag" {
  description = "ECR image tag to deploy"
  type        = string
  default     = "latest"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "tcf_db"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "tcf_admin"
}
