# Configuration Management Guide

This guide explains how to configure and manage the TRC Platform backend application using the Figment-based configuration system.

## Table of Contents

- [Overview](#overview)
- [Configuration Files](#configuration-files)
- [Environment Variables](#environment-variables)
- [Configuration Priority](#configuration-priority)
- [Environment Setup](#environment-setup)
- [Configuration Reference](#configuration-reference)
- [Security Considerations](#security-considerations)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Testing Configuration](#testing-configuration)
- [Troubleshooting](#troubleshooting)

## Overview

The TRC Platform uses a hierarchical configuration system built with [Figment](https://github.com/rust-cli/figment). This system provides:

- **Type Safety**: All configuration values are validated at compile-time and runtime
- **Multiple Sources**: Support for TOML files, JSON files, and environment variables
- **Environment-Specific**: Different configurations for development, test, and production
- **Validation**: Comprehensive validation with clear error messages
- **Hot Reload**: Configuration reloading in development mode

## Configuration Files

The application loads configuration from multiple files in the following order:

1. `config/default.toml` - Base configuration for all environments
2. `config/{environment}.toml` - Environment-specific overrides
3. `config/local.toml` - Local development overrides (git-ignored)

### File Structure

```
backend-rs/
├── config/
│   ├── default.toml           # Base configuration
│   ├── development.toml       # Development overrides
│   ├── test.toml             # Test environment overrides
│   ├── production.toml       # Production overrides
│   └── local.toml.example    # Template for local configuration
├── docs/
│   └── configuration.md      # This documentation
└── src/
    └── config/
        ├── settings.rs       # Configuration structs
        └── service.rs        # Configuration service
```

## Environment Variables

All configuration values can be overridden using environment variables with the `TRC_` prefix.

### Naming Convention

- Use `TRC_` prefix
- Use double underscore (`__`) for nested configuration
- Use uppercase letters and underscores

### Examples

```bash
# Server configuration
export TRC_SERVER__PORT=9000
export TRC_SERVER__HOST=0.0.0.0

# Database configuration
export TRC_DATABASE__URL="postgresql://user:password@localhost:5432/db"
export TRC_DATABASE__MAX_CONNECTIONS=20

# OpenAI configuration
export TRC_OPENAI__API_KEY="sk-your-api-key"
export TRC_OPENAI__MODEL="gpt-4"

# JWT configuration
export TRC_JWT__SECRET="your-super-secret-key"
export TRC_JWT__EXPIRATION_HOURS=24
```

## Configuration Priority

Configuration is loaded in order of priority (highest to lowest):

1. **Environment Variables** (`TRC_*`)
2. **Local Configuration** (`config/local.toml`)
3. **Environment-Specific** (`config/{environment}.toml`)
4. **Default Configuration** (`config/default.toml`)

## Environment Setup

### Development Environment

The development environment is optimized for local development with:

- Verbose logging and debugging features
- Relaxed security settings for easier testing
- Local database and service connections
- Hot reload capabilities

#### Setup Steps

1. **Copy local configuration template:**
   ```bash
   cp config/local.toml.example config/local.toml
   ```

2. **Edit `config/local.toml` with your local settings**

3. **Set up environment variables (optional):**
   ```bash
   export TRC_OPENAI__API_KEY="your-api-key"
   export TRC_JWT__SECRET="your-jwt-secret"
   ```

4. **Run the application:**
   ```bash
   cargo run
   # or with explicit environment
   RUST_ENV=development cargo run
   ```

### Test Environment

The test environment is configured for automated testing with:

- Isolated test database
- Mock external services
- Minimal logging
- High limits for load testing

### Production Environment

The production environment is optimized for security and performance with:

- Restrictive security settings
- Structured JSON logging
- Performance optimizations
- Comprehensive monitoring

## Configuration Reference

### Server Configuration

```toml
[server]
host = "127.0.0.1"          # Server bind address
port = 8080                 # Server port
read_timeout = 30           # Read timeout in seconds
write_timeout = 30          # Write timeout in seconds
workers = 0                 # Worker threads (0 = auto)
```

### Database Configuration

```toml
[database]
url = "postgresql://user:password@host:port/database"
max_connections = 10        # Maximum connections in pool
min_connections = 1         # Minimum connections in pool
acquire_timeout_seconds = 30 # Connection acquisition timeout
idle_timeout_seconds = 600  # Idle connection timeout
max_lifetime_seconds = 1800 # Connection maximum lifetime
```

### OpenAI Configuration

```toml
[openai]
api_key = ""               # OpenAI API key (use env var in production)
base_url = "https://api.openai.com/v1"
model = "gpt-4"           # Default model
max_tokens = 4096         # Maximum tokens per request
temperature = 0.7         # Response randomness (0.0-2.0)
timeout_seconds = 60      # Request timeout
```

### JWT Configuration

```toml
[jwt]
secret = ""                # JWT secret (use env var in production)
expiration_hours = 24      # Token expiration time
refresh_expiration_days = 7 # Refresh token expiration
issuer = "trc-platform"    # Token issuer
```

### Email Configuration

```toml
[email]
from_address = "noreply@trcplatform.com"
from_name = "TRC Platform"
smtp_host = "localhost"    # SMTP server host
smtp_port = 587           # SMTP server port
smtp_username = ""        # SMTP username
smtp_password = ""        # SMTP password
use_tls = true           # Use TLS encryption
```

### Cache Configuration

```toml
[cache]
redis_url = "redis://localhost:6379"
default_ttl_seconds = 3600  # Default cache TTL
max_connections = 10        # Maximum Redis connections
```

### Logging Configuration

```toml
[logging]
level = "info"           # Log level: trace, debug, info, warn, error
format = "json"          # Log format: json, pretty
output = "stdout"        # Log output: stdout, stderr, file
targets = ["trc_platform"] # Log targets to include
```

### CORS Configuration

```toml
[cors]
allow_origins = ["http://localhost:3000"]  # Allowed origins
allow_methods = ["GET", "POST", "PUT", "DELETE"]  # Allowed methods
allow_headers = ["*"]                      # Allowed headers
allow_credentials = true                   # Allow credentials
max_age_seconds = 3600                     # Cache max age
```

## Security Considerations

### Sensitive Data

Never commit sensitive configuration to version control:

- API keys (OpenAI, email services)
- Database passwords
- JWT secrets
- Third-party service credentials

### Environment Variables in Production

Always use environment variables for sensitive data in production:

```bash
# Required environment variables for production
export TRC_DATABASE__URL="your-production-db-url"
export TRC_OPENAI__API_KEY="your-production-api-key"
export TRC_JWT__SECRET="your-super-strong-jwt-secret"
export TRC_EMAIL__SMTP_PASSWORD="your-smtp-password"
```

### Security Headers

Production environment includes security headers:

- Strict Transport Security (HSTS)
- Content Type Options
- Frame Options
- XSS Protection
- Referrer Policy

## Development Setup

### Prerequisites

1. **PostgreSQL** (local or Docker)
2. **Redis** (local or Docker)
3. **Rust** (latest stable)
4. **Optional**: Mailhog for email testing

### Docker Compose Setup

Create a `docker-compose.yml` for local development:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: trc_platform_dev
      POSTGRES_USER: trc_platform_dev
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI

volumes:
  postgres_data:
```

### Local Development Workflow

1. **Start services:**
   ```bash
   docker-compose up -d
   ```

2. **Setup configuration:**
   ```bash
   cp config/local.toml.example config/local.toml
   # Edit config/local.toml as needed
   ```

3. **Set environment variables:**
   ```bash
   export TRC_OPENAI__API_KEY="your-api-key"
   export TRC_JWT__SECRET="your-jwt-secret"
   ```

4. **Run database migrations:**
   ```bash
   cargo run -- migrate
   ```

5. **Start the application:**
   ```bash
   cargo run
   ```

## Production Deployment

### Required Environment Variables

Production deployment requires these environment variables:

```bash
# Database
export TRC_DATABASE__URL="postgresql://user:password@host:port/database"

# OpenAI
export TRC_OPENAI__API_KEY="sk-your-api-key"

# JWT
export TRC_JWT__SECRET="your-super-strong-jwt-secret"

# Email (if using email features)
export TRC_EMAIL__SMTP_HOST="your-smtp-host"
export TRC_EMAIL__SMTP_USERNAME="your-smtp-username"
export TRC_EMAIL__SMTP_PASSWORD="your-smtp-password"

# Cache (if using Redis)
export TRC_CACHE__REDIS_URL="redis://your-redis-host:6379"

# CORS (if different from default)
export TRC_CORS__ALLOW_ORIGINS="https://yourdomain.com,https://api.yourdomain.com"
```

### Docker Production Example

```dockerfile
FROM rust:1.75 as builder
WORKDIR /app
COPY . .
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/target/release/trc-platform /usr/local/bin/
EXPOSE 8080
CMD ["trc-platform"]
```

### Environment Detection

The application detects the environment using:

1. `RUST_ENV` environment variable (development, test, staging, production)
2. `APP_ENVIRONMENT` environment variable
3. Falls back to `development` if not specified

## Testing Configuration

### Running Tests

```bash
# Run with test configuration
cargo test

# Run with explicit test environment
RUST_ENV=test cargo test

# Run integration tests
cargo test --test integration
```

### Test Configuration Features

- Uses separate test database
- Mock external services
- High rate limits for load testing
- Minimal logging output
- Automatic cleanup between tests

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Error**: `Database connection failed`

**Solution**: Check database URL and ensure PostgreSQL is running:

```bash
# Test database connection
psql "postgresql://user:password@localhost:5432/database"

# Check if PostgreSQL is running
docker ps | grep postgres
```

#### 2. Redis Connection Failed

**Error**: `Redis connection failed`

**Solution**: Verify Redis is running and URL is correct:

```bash
# Test Redis connection
redis-cli -u redis://localhost:6379 ping

# Check if Redis is running
docker ps | grep redis
```

#### 3. Configuration Validation Error

**Error**: `Configuration validation failed`

**Solution**: Check configuration file syntax and required fields:

```bash
# Validate TOML syntax
cat config/default.toml | python -c "import sys, toml; toml.load(sys.stdin)"

# Check required environment variables
env | grep TRC_
```

#### 4. JWT Secret Missing

**Error**: `JWT secret is required`

**Solution**: Set JWT secret via environment variable:

```bash
export TRC_JWT__SECRET="your-super-secret-key"
```

### Debug Mode

Enable debug mode for verbose configuration logging:

```bash
RUST_LOG=debug RUST_ENV=development cargo run
```

### Configuration Dump

To view the loaded configuration:

```bash
RUST_LOG=trc_platform::config=debug cargo run
```

This will show the configuration hierarchy and final values without exposing sensitive data.

## Advanced Configuration

### Custom Configuration Sections

You can extend the configuration system by adding new sections to:

1. `src/config/settings.rs` - Add configuration structs
2. Configuration files - Add new sections
3. Environment variables - Use `TRC_CUSTOM__*` prefix

### Configuration Validation

The configuration system includes validation for:

- Required fields
- Data types
- Value ranges
- String patterns
- URL formats

### Hot Reload (Development)

In development mode, the application watches for configuration file changes and reloads automatically:

```toml
[development]
auto_reload = true
```

## Support

For configuration-related issues:

1. Check this documentation first
2. Review the GitHub issues
3. Create a new issue with your configuration details (remove sensitive data)
4. Include the error message and your environment setup