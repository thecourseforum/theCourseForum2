variable "project_name" {
  description = "Project name used in resource naming"
  type        = string
  default     = "tcf"
}

variable "environment" {
  description = "Environment name (test, staging, prod)"
  type        = string
  default     = "prod"
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

variable "waf_mode" {
  description = "WAF protection level: off, common or targeted Bot Control"
  type        = string
  default     = "targeted"

  validation {
    condition     = contains(["off", "common", "targeted"], var.waf_mode)
    error_message = "waf_mode must be off, common or targeted."
  }
}

variable "dns_role_arn" {
  description = "ARN of the role Terraform assumes in the separate Route 53 account"
  type        = string
  ephemeral   = true

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

variable "ecs_min_count" {
  description = "Minimum number of ECS tasks the service scales down to"
  type        = number
  default     = 1
}

variable "ecs_max_count" {
  description = "Maximum number of ECS tasks the service scales up to"
  type        = number
  default     = 10
}

variable "ecs_cpu_target" {
  description = "Average service CPU utilization percentage that autoscaling holds the service at"
  type        = number
  default     = 60
}

variable "ecs_memory_target" {
  description = "Average service memory utilization percentage that autoscaling holds the service at"
  type        = number
  default     = 75
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
  description = "Retention in days for extra logs: ALB access, VPC flow, RDS, Redis and Lambda"
  type        = number
  default     = 7
}

variable "app_logs_retention_days" {
  description = "Retention in days for the Django app (ECS) logs"
  type        = number
  default     = 30
}

variable "waf_logs_enabled" {
  description = "Send WAF request logs to CloudWatch Logs"
  type        = bool
  default     = true
}

variable "waf_logs_retention_days" {
  description = "Retention in days for WAF request logs"
  type        = number
  default     = 30
}

variable "cloudfront_logs_enabled" {
  description = "Send CloudFront access logs to CloudWatch Logs"
  type        = bool
  default     = false
}

variable "cloudfront_logs_retention_days" {
  description = "Retention in days for CloudFront access logs"
  type        = number
  default     = 30
}

variable "alb_access_logs_enabled" {
  description = "Write ALB access logs to the logs bucket"
  type        = bool
  default     = false
}

variable "rds_logs_enabled" {
  description = "Export PostgreSQL logs to CloudWatch Logs"
  type        = bool
  default     = false
}

variable "vpc_flow_logs_enabled" {
  description = "Write VPC flow logs to the logs bucket"
  type        = bool
  default     = false
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

variable "db_dump_schedule" {
  description = "EventBridge Scheduler expression for database dumps, in America/New_York time"
  type        = string
  default     = "cron(0 4 * * ? *)"
}
