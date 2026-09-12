# Dedicated origin hostname for CloudFront-to-ALB HTTPS.
resource "aws_route53_record" "origin" {
  provider = aws.dns

  zone_id = data.aws_route53_zone.main.zone_id
  name    = "origin.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = false
  }
}

# Route 53 A Record pointing to CloudFront
resource "aws_route53_record" "root" {
  provider = aws.dns

  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = false
  }
}
