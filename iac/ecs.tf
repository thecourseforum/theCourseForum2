# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"

  tags = {
    Name = "${local.name_prefix}-cluster"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "django" {
  family                   = "${local.name_prefix}-django"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

# NOTE: changed image to use prod image for testing
  container_definitions = jsonencode([
    {
      name      = "django-app"
      image     = "396913701887.dkr.ecr.us-east-1.amazonaws.com/tcf/thecourseforum2:2fca38b280e737d11f20b33aef32b0286869cef5"
      command   = ["/app/scripts/container-startup.sh"]
      essential = true

      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "DJANGO_SETTINGS_MODULE"
          value = "tcf_core.settings.prod"
        },
        {
          name  = "AWS_STORAGE_BUCKET_NAME"
          value = aws_s3_bucket.static.id
        },
        {
          name  = "AWS_S3_REGION_NAME"
          value = var.aws_region
        },
        {
          name  = "AWS_S3_CUSTOM_DOMAIN"
          value = aws_cloudfront_distribution.main.domain_name
        },
        {
          name  = "ALLOWED_HOSTS"
          value = "${var.domain_name},${aws_cloudfront_distribution.main.domain_name},${aws_lb.main.dns_name}"
        },
        {
          name  = "CORS_ALLOWED_ORIGINS"
          value = "https://${var.domain_name}"
        },
        {
          name  = "AWS_LOG_LEVEL"
          value = "DEBUG"
        },
        {
          name  = "AWS_ACCESS_KEY_ID"
          value = ""
        },
        {
          name  = "AWS_SECRET_ACCESS_KEY"
          value = ""
        }
      ]

      secrets = [
        {
          name      = "SECRET_KEY"
          valueFrom = aws_secretsmanager_secret.django_secret_key.arn
        },
        {
          name      = "AWS_RDS_HOST"
          valueFrom = "${aws_secretsmanager_secret.db_credentials.arn}:host::"
        },
        {
          name      = "AWS_RDS_PORT"
          valueFrom = "${aws_secretsmanager_secret.db_credentials.arn}:port::"
        },
        {
          name      = "AWS_RDS_NAME"
          valueFrom = "${aws_secretsmanager_secret.db_credentials.arn}:dbname::"
        },
        {
          name      = "AWS_RDS_USER"
          valueFrom = "${aws_secretsmanager_secret.db_credentials.arn}:username::"
        },
        {
          name      = "AWS_RDS_PASSWORD"
          valueFrom = "${aws_secretsmanager_secret.db_credentials.arn}:password::"
        },
        {
          name      = "COGNITO_USER_POOL_ID"
          valueFrom = "${aws_secretsmanager_secret.cognito_credentials.arn}:user_pool_id::"
        },
        {
          name      = "COGNITO_APP_CLIENT_ID"
          valueFrom = "${aws_secretsmanager_secret.cognito_credentials.arn}:app_client_id::"
        },
        {
          name      = "COGNITO_APP_CLIENT_SECRET"
          valueFrom = "${aws_secretsmanager_secret.cognito_credentials.arn}:app_client_secret::"
        },
        {
          name      = "COGNITO_DOMAIN"
          valueFrom = "${aws_secretsmanager_secret.cognito_credentials.arn}:domain::"
        },
        {
          name      = "COGNITO_REGION_NAME"
          valueFrom = "${aws_secretsmanager_secret.cognito_credentials.arn}:region::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "django"
        }
      }
    }
  ])

  depends_on = [
    aws_secretsmanager_secret_version.django_secret_key,
    aws_secretsmanager_secret_version.db_credentials,
    aws_secretsmanager_secret_version.cognito_credentials,
    aws_iam_role_policy.ecs_task_execution_secrets,
    aws_iam_role_policy_attachment.ecs_task_execution
  ]

  tags = {
    Name = "${local.name_prefix}-django-task"
  }
}

# ECS Service
resource "aws_ecs_service" "django" {
  name             = "${local.name_prefix}-django-service"
  cluster          = aws_ecs_cluster.main.id
  task_definition  = aws_ecs_task_definition.django.arn
  desired_count    = var.ecs_desired_count
  launch_type      = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets          = data.aws_subnets.public.ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ecs.arn
    container_name   = "django-app"
    container_port   = 80
  }

  health_check_grace_period_seconds = 300

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  depends_on = [
    aws_lb_listener.https,
    aws_lb_listener.http
  ]

  tags = {
    Name = "${local.name_prefix}-django-service"
  }
}
