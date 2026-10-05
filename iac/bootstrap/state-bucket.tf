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

resource "aws_kms_key" "terraform_state" {
  provider                = aws.app
  description             = "Encrypts Terraform state and saved plans in ${var.terraform_state_bucket_name}"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name      = "tcf-terraform-state"
    ManagedBy = "bootstrap-terraform"
  }
}

resource "aws_kms_alias" "terraform_state" {
  provider      = aws.app
  name          = "alias/tcf-terraform-state"
  target_key_id = aws_kms_key.terraform_state.key_id
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  provider = aws.app
  bucket   = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform_state.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_policy" "terraform_state" {
  provider = aws.app
  bucket   = aws_s3_bucket.terraform_state.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.terraform_state.arn,
          "${aws_s3_bucket.terraform_state.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.terraform_state]
}

resource "aws_s3_bucket_lifecycle_configuration" "terraform_state" {
  provider = aws.app
  bucket   = aws_s3_bucket.terraform_state.id

  rule {
    id     = "expire-old-app-state"
    status = "Enabled"

    filter {
      prefix = "app/"
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    expiration {
      expired_object_delete_marker = true
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }

  rule {
    id     = "expire-saved-plans"
    status = "Enabled"

    filter {
      prefix = "plans/"
    }

    expiration {
      days = 1
    }

    noncurrent_version_expiration {
      noncurrent_days = 1
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }

  depends_on = [aws_s3_bucket_versioning.terraform_state]
}
