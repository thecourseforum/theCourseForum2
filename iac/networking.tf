# Use the default VPC (matching production architecture)
data "aws_vpc" "main" {
  default = true
}

# Get default subnets in the default VPC for the specified availability zones
data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "availability-zone"
    values = var.availability_zones
  }

  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}
