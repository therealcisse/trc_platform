# Image Solve Platform - Backend

Production-ready Django backend for the Image Solve Platform, providing AI-powered image processing with mathematical problem-solving capabilities.

## Features

### Core Functionality
- **AI-Powered Image Processing**: Integration with OpenAI Vision API for mathematical problem solving
- **Mock Mode**: Development mode with simulated OpenAI responses for testing
- **Request ID Tracking**: Unique request IDs for debugging and monitoring

### Authentication & Security
- **Custom Email Authentication**: Email-based user authentication system
- **Invite Code System**: Registration requires valid invite codes
- **Email Verification**: Built-in email verification workflow
- **API Token Management**: Secure bearer token generation for API access
- **Argon2 Password Hashing**: Industry-standard secure password storage
- **CORS Support**: Configurable cross-origin resource sharing

### Usage & Billing
- **Request Tracking**: Comprehensive logging of all API requests
- **Usage Monitoring**: Track requests per user with detailed history
- **Billing Periods**: Automated billing period management
- **Cost Calculation**: Configurable per-request pricing

### Developer Experience
- **OpenAPI Documentation**: Auto-generated API docs via drf-spectacular
- **Type Safety**: Full mypy type checking with Django stubs
- **Code Quality**: Automated linting with Ruff and formatting with Black
- **Testing**: Comprehensive test suite with pytest
- **Docker Support**: Complete containerization with Docker Compose

## Requirements

- Python 3.12+
- PostgreSQL 14+ (or use Docker Compose)
- uv (recommended) or pip for package management

## Quick Start

### Using Docker Compose (Recommended)

1. **Start the services**:
```bash
# Start PostgreSQL, Adminer, and Mailcatcher
docker compose up -d

# Access services:
# - PostgreSQL: localhost:5432
# - Adminer UI: http://localhost:8090
# - Mailcatcher: http://localhost:1080
```

2. **Set up environment**:
```bash
# Create .env file from example (if it doesn't exist)
cp .env.example .env  # Make sure to create this if needed

# Or use the existing .env file
# Edit .env to add your OPENAI_API_KEY if needed
```

3. **Install dependencies** (using uv):
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
make install
# Or directly: uv add -e ".[dev]"
```

4. **Initialize database**:
```bash
# Run migrations
make migrate

# Create demo data (includes admin user)
uv run python manage.py bootstrap_demo
```

5. **Run development server**:
```bash
make dev
# Or directly: uv run python manage.py runserver
```

6. **Access the application**:
- API Documentation: http://localhost:8000/api/docs/
- Admin Interface: http://localhost:8000/admin/
- API Schema: http://localhost:8000/api/schema/

### Local Development Without Docker

1. **Set up PostgreSQL locally**
2. **Configure environment**:
```bash
# Edit .env file with your database URL
DATABASE_URL="postgres://user:password@localhost:5432/dbname"
```
3. Follow steps 3-6 from Docker setup above

## Development Commands

### Make Commands
```bash
make help        # Show all available commands
make install     # Install dependencies using uv
make dev         # Run development server
make test        # Run tests with pytest
make migrate     # Run database migrations
make superuser   # Create Django superuser
make typecheck   # Run mypy type checking
make lint        # Run ruff linter
make format      # Format code with black and ruff
make clean       # Clean up generated files
```

### Management Commands
```bash
# Bootstrap demo data (users, tokens, invite codes)
uv run python manage.py bootstrap_demo

# Billing period management
uv run python manage.py create_billing_periods
uv run python manage.py mark_overdue_periods

# Create a test user
uv run python create_staff_user.py
```

## API Documentation

### Public Endpoints

#### Registration and Authentication
- **POST** `/api/customers/register` - Register new user with invite code
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword",
    "invite_code": "DEMO1234"
  }
  ```

- **POST** `/api/customers/login` - Authenticate user
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword"
  }
  ```

- **GET** `/api/customers/verify-email?token=...` - Verify email address

### Authenticated Endpoints (Session-based)

#### Account Management
- **POST** `/api/customers/logout` - End user session
- **POST** `/api/customers/password/change` - Update password
- **POST** `/api/customers/password/reset` - Request password reset
- **POST** `/api/customers/resend-verification` - Resend verification email

#### API Token Management
- **GET** `/api/customers/tokens` - List all user's API tokens
- **POST** `/api/customers/tokens` - Generate new API token
  ```json
  {
    "name": "Production API Token"
  }
  ```
- **DELETE** `/api/customers/tokens/{id}` - Revoke specific token

#### Usage and Billing
- **GET** `/api/customers/usage/requests` - Paginated request history
- **GET** `/api/customers/usage/summary` - Usage statistics and totals

### Core API Endpoints (Bearer Token Required)

- **POST** `/api/core/solve` - Process image with AI
  ```bash
  curl -X POST http://localhost:8000/api/core/solve \
    -H "Authorization: Bearer tok_your_token_here" \
    -H "Content-Type: application/json" \
    -d '{
      "image": "base64_encoded_image_data",
      "prompt": "Solve this math problem"
    }'
  ```

- **GET** `/api/core/health` - Service health check

## Authentication Methods

### Session Authentication
- Used for web portal and admin interface
- Cookie-based session management
- CSRF protection enabled
- Suitable for browser-based interactions

### Bearer Token Authentication
- Used for programmatic API access
- Tokens prefixed with `tok_`
- Secure hash storage (only prefix stored in plain text)
- No default expiration (manually revocable)

#### Token Usage Example:
```bash
# Include in Authorization header
Authorization: Bearer tok_abc123xyz789...

# Example with curl
curl -H "Authorization: Bearer tok_abc123xyz789" \
  http://localhost:8000/api/core/solve
```

## Testing

### Running Tests
```bash
# Run all tests
make test

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_math_solver.py

# Run with coverage report
uv run pytest --cov=. --cov-report=html
# View report at htmlcov/index.html
```

### Test Structure
- Unit tests in each app's `tests.py` file
- Integration tests in `tests/` directory
- Test data generation with `model-bakery`
- External API mocking with `requests-mock`

## Code Quality

### Type Checking
```bash
# Run mypy with strict configuration
make typecheck

# Check specific module
uv run mypy customers/
```

### Linting and Formatting
```bash
# Run linter
make lint

# Auto-format code
make format

# Manual commands
uv run black .
uv run ruff check --fix .
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Django Configuration
DJANGO_SECRET_KEY="your-secret-key-here"
DJANGO_DEBUG=1  # Set to 0 in production
ALLOWED_HOSTS="localhost,127.0.0.1"

# Database
DATABASE_URL="postgres://postgres:postgres@localhost:5432/app"

# Email Configuration
DEFAULT_FROM_EMAIL="no-reply@example.com"
EMAIL_HOST="localhost"
EMAIL_PORT=1025  # Mailcatcher default port
EMAIL_HOST_USER=""
EMAIL_HOST_PASSWORD=""
EMAIL_USE_TLS=false

# OpenAI Integration
OPENAI_API_KEY="sk-..."  # Your OpenAI API key
OPENAI_MODEL="gpt-4-vision-preview"
OPENAI_TIMEOUT_S=30
USE_MOCK_OPENAI=true  # Set to false for production

# Billing Configuration
COST_PER_REQUEST_CENTS=100

# CORS Settings
CORS_ALLOWED_ORIGINS="http://localhost:5173,http://localhost:3000"
```

## Project Structure

```
backend/
├── config/              # Django project configuration
│   ├── settings.py      # Main settings file
│   ├── urls.py          # URL configuration
│   └── wsgi.py          # WSGI application
├── core/                # Core business logic
│   ├── services/        # External service integrations
│   ├── middleware/      # Custom middleware
│   └── management/      # Management commands
├── customers/           # User and authentication
│   ├── models.py        # User, ApiToken, InviteCode models
│   ├── serializers.py   # DRF serializers
│   └── views.py         # API views
├── usage/               # Usage tracking and billing
│   ├── models.py        # RequestLog, BillingPeriod models
│   └── utils.py         # Billing calculations
├── tests/               # Integration tests
├── docs/                # Additional documentation
└── manage.py            # Django management script
```

## Database Models

### Customers App
- **User**: Custom user model with email authentication
- **ApiToken**: Bearer tokens for API access
- **InviteCode**: Registration invite codes
- **EmailVerificationToken**: Email verification tracking

### Usage App
- **RequestLog**: API request tracking
- **BillingPeriod**: Monthly billing periods

### Core App
- **Settings**: Global application settings

## Demo Data

The `bootstrap_demo` command creates:
- Admin user: `admin@example.com` / `admin123`
- Regular user: `user@example.com` / `user123`
- Unused invite code: `DEMO1234`
- Sample API token for the regular user

## Docker Services

### PostgreSQL
- Port: 5432
- Database: app
- User: postgres
- Password: postgres

### Adminer
- Port: 8090
- Database UI for PostgreSQL
- Access at http://localhost:8090

### Mailcatcher
- SMTP Port: 1025
- Web UI Port: 1080
- View sent emails at http://localhost:1080

## Deployment Considerations

### Production Checklist
- Set `DJANGO_DEBUG=0`
- Generate strong `DJANGO_SECRET_KEY`
- Configure proper `ALLOWED_HOSTS`
- Set up real email provider (not Mailcatcher)
- Add real `OPENAI_API_KEY`
- Set `USE_MOCK_OPENAI=false`
- Enable HTTPS and security headers
- Configure proper CORS origins
- Set up monitoring and logging
- Configure database backups

### Security Notes
- Passwords hashed with Argon2
- API tokens stored as secure hashes
- CSRF protection enabled
- Request ID tracking for debugging
- Email verification required for new accounts

## License

Proprietary - All rights reserved
