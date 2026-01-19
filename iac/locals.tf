locals {
  # Common name prefix for resources
  name_prefix = "${var.project_name}-${var.environment}"

  # Subnet CIDR mappings
  public_subnet_cidrs = {
    0 = "10.0.1.0/24"
    1 = "10.0.2.0/24"
  }

  private_subnet_cidrs = {
    0 = "10.0.11.0/24"
    1 = "10.0.12.0/24"
  }

  # Common tags (merged with provider default_tags)
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}
