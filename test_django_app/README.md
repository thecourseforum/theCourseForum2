# Django App

A Django application configured for deployment on AWS with RDS PostgreSQL and S3 static file storage.

## Features

- Django 6.0+ with PostgreSQL support
- AWS S3 integration for static and media files
- Docker containerization
- Separate settings for local development and production
- ECS-ready deployment configuration

## Prerequisites

- Python 3.12+
- uv package manager
- Docker (for containerized deployment)

## Local Development Setup

1. **Clone the repository and navigate to the project directory**

2. **Install dependencies using uv**
   ```bash
   uv sync
   ```

3. **Create a local .env file**
   ```bash
   cp .env.example .env
   ```
   Update the `.env` file with your local settings. For local development, the default SQLite database will be used.

4. **Run migrations**
   ```bash
   source .venv/bin/activate
   python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Application: http://localhost:8000
   - Admin interface: http://localhost:8000/admin

## Production Deployment

The application is configured to run on AWS ECS with:
- RDS PostgreSQL database
- S3 for static and media files
- CloudFront CDN for content delivery

### Environment Variables (Production)

Set these environment variables in your ECS task definition or container environment:

- `DJANGO_SETTINGS_MODULE=tcf_core.settings.prod`
- `SECRET_KEY` - Django secret key (stored in AWS Secrets Manager)
- `DEBUG=False`
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `AWS_RDS_NAME` - RDS database name
- `AWS_RDS_USER` - RDS database user
- `AWS_RDS_PASSWORD` - RDS database password
- `AWS_RDS_HOST` - RDS endpoint
- `AWS_RDS_PORT=5432`
- `AWS_STORAGE_BUCKET_NAME` - S3 bucket name
- `AWS_S3_REGION_NAME` - AWS region
- `AWS_S3_CUSTOM_DOMAIN` - CloudFront domain for static files
- `CSRF_TRUSTED_ORIGINS` - Comma-separated list of trusted origins

### Building the Docker Image

```bash
docker build -t django-app .
```

### Running the Container Locally

```bash
docker run -p 8000:8000 --env-file .env django-app
```

## Project Structure

```
.
├── config/                 # Django project configuration
│   ├── settings/          # Settings modules
│   │   ├── __init__.py
│   │   ├── base.py       # Base settings
│   │   ├── local.py      # Local development settings
│   │   └── prod.py       # Production settings
│   ├── asgi.py
│   ├── urls.py
│   └── wsgi.py
├── requirements/          # Requirements files
│   ├── base.txt          # Base dependencies
│   ├── dev.txt           # Development dependencies
│   └── prod.txt          # Production dependencies
├── scripts/              # Deployment scripts
│   └── container-startup.sh
├── Dockerfile            # Docker configuration
├── manage.py            # Django management script
└── README.md           # This file
```

## Settings Modules

- `tcf_core.settings.base` - Base settings shared across all environments
- `tcf_core.settings.local` - Local development settings (SQLite, debug mode)
- `tcf_core.settings.prod` - Production settings (PostgreSQL, S3, security hardened)

## Infrastructure

The infrastructure configuration can be found in `../iac/` and includes:
- VPC with public and private subnets
- RDS PostgreSQL instance
- S3 bucket for static/media files
- CloudFront distribution
- ECS Fargate cluster
- Application Load Balancer
- Route53 DNS configuration

## Management Commands

- `python manage.py migrate` - Run database migrations
- `python manage.py collectstatic` - Collect static files (to S3 in production)
- `python manage.py createsuperuser` - Create admin user
- `python manage.py clearsessions` - Clear expired sessions

## License

[Your License Here]
