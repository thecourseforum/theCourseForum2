# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "${local.name_prefix}-cache-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${local.name_prefix}-cache-subnet-group"
  }
}

# ElastiCache Replication Group (Valkey, provisioned)
resource "aws_elasticache_replication_group" "valkey" {
  replication_group_id          = "${local.name_prefix}-cache"
  description                   = "Valkey cache for ${local.name_prefix}"
  engine                        = "valkey"
  engine_version                = "8.2"
  node_type                     = "cache.t4g.micro"
  number_cache_clusters         = 1
  port                          = 6379
  automatic_failover_enabled    = false
  multi_az_enabled              = false
  subnet_group_name             = aws_elasticache_subnet_group.main.name
  security_group_ids            = [aws_security_group.elasticache.id]
  snapshot_retention_limit      = 0
  at_rest_encryption_enabled    = true
  transit_encryption_enabled    = true
  auth_token                    = random_password.redis_auth_token.result

  log_delivery_configuration {
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "slow-log"

    destination_details {
      cloudwatch_logs_details {
        log_group = aws_cloudwatch_log_group.redis.name
      }
    }
  }

  tags = {
    Name = "${local.name_prefix}-cache"
  }
}
