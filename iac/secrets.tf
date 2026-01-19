# Generate random Django secret key
resource "random_password" "django_secret_key" {
  length           = 50
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
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
    domain            = aws_cognito_user_pool_domain.main.domain
    region            = var.aws_region
  })
}
