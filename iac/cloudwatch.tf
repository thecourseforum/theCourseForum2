# CloudWatch Log Group for ECS
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${local.name_prefix}-django"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${local.name_prefix}-ecs-logs"
  }
}

# CloudWatch Log Group for ElastiCache slow logs
resource "aws_cloudwatch_log_group" "redis" {
  name              = "redis-cache"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${local.name_prefix}-redis-logs"
  }
}
