locals {
  db_dump_reader_principal_arns = [
    "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/aws-reserved/sso.amazonaws.com/*AWSReservedSSO_AdministratorAccess_*"
  ]
}

resource "aws_s3_bucket" "db_dumps" {
  bucket = "${local.name_prefix}-db-dumps-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${local.name_prefix}-db-dumps"
  }
}

resource "aws_s3_bucket_public_access_block" "db_dumps" {
  bucket = aws_s3_bucket.db_dumps.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "db_dumps" {
  bucket = aws_s3_bucket.db_dumps.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "db_dumps" {
  bucket = aws_s3_bucket.db_dumps.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "db_dumps" {
  bucket = aws_s3_bucket.db_dumps.id

  rule {
    id     = "archive-old-dumps"
    status = "Enabled"

    filter {}

    transition {
      days          = 30
      storage_class = "GLACIER_IR"
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

resource "aws_s3_bucket_policy" "db_dumps" {
  bucket = aws_s3_bucket.db_dumps.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.db_dumps.arn,
          "${aws_s3_bucket.db_dumps.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
      {
        Sid       = "DenyReadsExceptAdmins"
        Effect    = "Deny"
        Principal = "*"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:GetObjectAttributes",
          "s3:RestoreObject"
        ]
        Resource = "${aws_s3_bucket.db_dumps.arn}/*"
        Condition = {
          ArnNotLike = {
            "aws:PrincipalArn" = local.db_dump_reader_principal_arns
          }
        }
      },
      {
        Sid       = "DenyDeletesExceptAdmins"
        Effect    = "Deny"
        Principal = "*"
        Action = [
          "s3:DeleteObject",
          "s3:DeleteObjectVersion"
        ]
        Resource = "${aws_s3_bucket.db_dumps.arn}/*"
        Condition = {
          ArnNotLike = {
            "aws:PrincipalArn" = local.db_dump_reader_principal_arns
          }
        }
      },
      {
        Sid       = "DenyWritesExceptDumpTask"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.db_dumps.arn}/*"
        Condition = {
          ArnNotEquals = {
            "aws:PrincipalArn" = aws_iam_role.db_dump_task.arn
          }
        }
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.db_dumps]
}

resource "aws_iam_role" "db_dump_task" {
  name                 = "${local.name_prefix}-db-dump-task-role"
  permissions_boundary = local.role_permissions_boundary_arn

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${local.name_prefix}-db-dump-task-role"
  }
}

resource "aws_iam_role_policy" "db_dump_task" {
  name = "${local.name_prefix}-db-dump-upload-policy"
  role = aws_iam_role.db_dump_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:AbortMultipartUpload"
        ]
        Resource = "${aws_s3_bucket.db_dumps.arn}/*"
      }
    ]
  })
}

resource "aws_ecs_task_definition" "db_dump" {
  family                   = "${local.name_prefix}-db-dump"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.db_dump_task.arn

  volume {
    name = "dump"
  }

  container_definitions = jsonencode([
    {
      name      = "pg-dump"
      image     = "public.ecr.aws/docker/library/postgres:18-alpine"
      essential = false
      command   = ["pg_dump", "--format=custom", "--clean", "--file=/dump/db.dump"]

      environment = [
        {
          name  = "PGSSLMODE"
          value = "require"
        }
      ]

      secrets = [
        {
          name      = "PGHOST"
          valueFrom = "${aws_secretsmanager_secret.db_credentials.arn}:host::"
        },
        {
          name      = "PGPORT"
          valueFrom = "${aws_secretsmanager_secret.db_credentials.arn}:port::"
        },
        {
          name      = "PGDATABASE"
          valueFrom = "${aws_secretsmanager_secret.db_credentials.arn}:dbname::"
        },
        {
          name      = "PGUSER"
          valueFrom = "${aws_secretsmanager_secret.db_credentials.arn}:username::"
        },
        {
          name      = "PGPASSWORD"
          valueFrom = "${aws_secretsmanager_secret.db_credentials.arn}:password::"
        }
      ]

      mountPoints = [
        {
          sourceVolume  = "dump"
          containerPath = "/dump"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "db-dump"
        }
      }
    },
    {
      name       = "upload"
      image      = "public.ecr.aws/aws-cli/aws-cli:2.37.9"
      essential  = true
      entryPoint = ["sh", "-c"]
      command    = ["aws s3 cp /dump/db.dump \"s3://$DUMP_BUCKET/$(date -u +%Y-%m-%dT%H%M%SZ).dump\""]

      dependsOn = [
        {
          containerName = "pg-dump"
          condition     = "SUCCESS"
        }
      ]

      environment = [
        {
          name  = "DUMP_BUCKET"
          value = aws_s3_bucket.db_dumps.id
        }
      ]

      mountPoints = [
        {
          sourceVolume  = "dump"
          containerPath = "/dump"
          readOnly      = true
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "db-dump"
        }
      }
    }
  ])

  depends_on = [
    aws_secretsmanager_secret_version.db_credentials,
    aws_iam_role_policy.ecs_task_execution_secrets,
    aws_iam_role_policy_attachment.ecs_task_execution
  ]

  tags = {
    Name = "${local.name_prefix}-db-dump-task"
  }
}

resource "aws_iam_role" "db_dump_scheduler" {
  name                 = "${local.name_prefix}-db-dump-scheduler-role"
  permissions_boundary = local.role_permissions_boundary_arn

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })

  tags = {
    Name = "${local.name_prefix}-db-dump-scheduler-role"
  }
}

resource "aws_iam_role_policy" "db_dump_scheduler" {
  name = "${local.name_prefix}-db-dump-scheduler-policy"
  role = aws_iam_role.db_dump_scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "ecs:RunTask"
        Resource = "${aws_ecs_task_definition.db_dump.arn_without_revision}:*"
        Condition = {
          ArnEquals = {
            "ecs:cluster" = aws_ecs_cluster.main.arn
          }
        }
      },
      {
        Effect = "Allow"
        Action = "iam:PassRole"
        Resource = [
          aws_iam_role.ecs_task_execution.arn,
          aws_iam_role.db_dump_task.arn
        ]
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "ecs-tasks.amazonaws.com"
          }
        }
      }
    ]
  })
}

resource "aws_scheduler_schedule" "db_dump" {
  name                         = "${local.name_prefix}-db-dump"
  description                  = "Dump the ${local.name_prefix} database to ${aws_s3_bucket.db_dumps.id}"
  schedule_expression          = var.db_dump_schedule
  schedule_expression_timezone = "America/New_York"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_ecs_cluster.main.arn
    role_arn = aws_iam_role.db_dump_scheduler.arn

    ecs_parameters {
      task_definition_arn = aws_ecs_task_definition.db_dump.arn
      launch_type         = "FARGATE"

      network_configuration {
        subnets          = aws_subnet.public[*].id
        security_groups  = [aws_security_group.ecs_tasks.id]
        assign_public_ip = true
      }
    }

    retry_policy {
      maximum_event_age_in_seconds = 3600
      maximum_retry_attempts       = 3
    }
  }
}
