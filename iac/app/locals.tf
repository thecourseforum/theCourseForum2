locals {
  # Common name prefix for resources
  name_prefix = "${var.project_name}-${var.environment}"

  # Common tags (merged with provider default_tags)
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}
