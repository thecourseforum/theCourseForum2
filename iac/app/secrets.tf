# Generate random Django secret key
resource "random_password" "django_secret_key" {
  length           = 50
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Valkey auth token for in-transit TLS + AUTH
resource "random_password" "redis_auth_token" {
  length  = 32
  special = false
}

# Django Secret Key in Secrets Manager
resource "aws_secretsmanager_secret" "django_secret_key" {
  name_prefix = "${local.name_prefix}/django-secret-key-"
  description = "Django SECRET_KEY for application"

  tags = {
    Name = "${local.name_prefix}-django-secret-key"
  }
}

resource "aws_secretsmanager_secret_version" "django_secret_key" {
  secret_id     = aws_secretsmanager_secret.django_secret_key.id
  secret_string = random_password.django_secret_key.result
}

# Database Credentials in Secrets Manager
resource "aws_secretsmanager_secret" "db_credentials" {
  name_prefix = "${local.name_prefix}/db-credentials-"
  description = "Database credentials for RDS PostgreSQL"

  tags = {
    Name = "${local.name_prefix}-db-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db_password.result
    host     = aws_db_instance.postgres.address
    port     = "5432"
    dbname   = var.db_name
  })
}

# Cognito Credentials
resource "aws_secretsmanager_secret" "cognito_credentials" {
  name_prefix = "${local.name_prefix}/cognito-credentials-"
  description = "Cognito user pool credentials"

  tags = {
    Name = "${local.name_prefix}-cognito-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "cognito_credentials" {
  secret_id = aws_secretsmanager_secret.cognito_credentials.id
  secret_string = jsonencode({
    user_pool_id      = aws_cognito_user_pool.main.id
    app_client_id     = aws_cognito_user_pool_client.main.id
    app_client_secret = aws_cognito_user_pool_client.main.client_secret
    domain            = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com"
    region            = var.aws_region
  })
}

# Redis auth token in Secrets Manager
resource "aws_secretsmanager_secret" "redis_auth_token" {
  name_prefix = "${local.name_prefix}/redis-auth-token-"
  description = "Valkey auth token for ${local.name_prefix}"

  tags = {
    Name = "${local.name_prefix}-redis-auth-token"
  }
}

resource "aws_secretsmanager_secret_version" "redis_auth_token" {
  secret_id     = aws_secretsmanager_secret.redis_auth_token.id
  secret_string = random_password.redis_auth_token.result
}

# Redis URL in Secrets Manager
resource "aws_secretsmanager_secret" "redis_url" {
  name_prefix = "${local.name_prefix}/redis-url-"
  description = "Redis connection URL for ElastiCache Valkey"

  tags = {
    Name = "${local.name_prefix}-redis-url"
  }
}

resource "aws_secretsmanager_secret_version" "redis_url" {
  secret_id     = aws_secretsmanager_secret.redis_url.id
  secret_string = "rediss://:${random_password.redis_auth_token.result}@${aws_elasticache_replication_group.valkey.primary_endpoint_address}:${aws_elasticache_replication_group.valkey.port}"
}
