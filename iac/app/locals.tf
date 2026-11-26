locals {
  # Common name prefix for resources
  name_prefix = "${var.project_name}-${var.environment}"

  role_permissions_boundary_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/${local.name_prefix}-role-boundary"

  # Common tags (merged with provider default_tags)
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
  }

  # Hosted zones owned by the DNS account (011713309463).
  route53_hosted_zone_ids = {
    "thecourseforum.com"     = "Z06158912Y7SI8FYZM5IA"
    "thecourseforumtest.com" = "Z09238113JE0PLS5VY8RQ"
  }

  waf_enabled  = local.waf_mode != "off"
  waf_acl_name = "tcf-web-acl"

  certificate_domains = flatten([
    for zone in sort(keys(local.route53_hosted_zone_ids)) : [zone, "origin.${zone}"]
  ])
}
