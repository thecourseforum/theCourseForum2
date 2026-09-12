# The bootstrap stack creates the application Terraform state bucket.
# Bootstrap itself intentionally uses local state on its first run because
# this bucket does not exist until this resource is created.
resource "aws_s3_bucket" "terraform_state" {
  provider = aws.app
  bucket   = var.terraform_state_bucket_name

  tags = {
    Name      = var.terraform_state_bucket_name
    ManagedBy = "bootstrap-terraform"
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  provider = aws.app
  bucket   = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "terraform_state" {
  provider = aws.app
  bucket   = aws_s3_bucket.terraform_state.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  provider = aws.app
  bucket   = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  provider = aws.app
  bucket   = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
