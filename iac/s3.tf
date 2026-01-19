# S3 Bucket for Static Files
resource "aws_s3_bucket" "static" {
  bucket_prefix = "${local.name_prefix}-static-"

  tags = {
    Name = "${local.name_prefix}-static"
  }
}

# Block Public Access
resource "aws_s3_bucket_public_access_block" "static" {
  bucket = aws_s3_bucket.static.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versioning (disabled for cost optimization)
resource "aws_s3_bucket_versioning" "static" {
  bucket = aws_s3_bucket.static.id

  versioning_configuration {
    status = "Disabled"
  }
}

# CORS Configuration
resource "aws_s3_bucket_cors_configuration" "static" {
  bucket = aws_s3_bucket.static.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = [
      "https://${var.domain_name}",
      "https://*.cloudfront.net"
    ]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}
