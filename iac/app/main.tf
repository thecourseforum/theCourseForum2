provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(local.common_tags, {
      ManagedBy = "terraform"
    })
  }
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = merge(local.common_tags, {
      ManagedBy = "terraform"
    })
  }
}

# Route 53 is hosted in a separate AWS account. The deployment identity must
# be allowed to assume this role in the DNS account.
provider "aws" {
  alias  = "dns"
  region = "us-east-1"

  assume_role {
    role_arn = var.dns_role_arn
  }

  default_tags {
    tags = merge(local.common_tags, {
      ManagedBy = "terraform"
    })
  }
}
