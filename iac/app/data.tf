# Import existing Route 53 hosted zone
data "aws_route53_zone" "main" {
  provider     = aws.dns
  zone_id      = local.route53_hosted_zone_ids[var.domain_name]
  private_zone = false
}

data "aws_caller_identity" "current" {}
