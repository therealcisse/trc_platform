# WARP.md

This file provides guidance to WARP when working with code in this repository.

## Project Overview

This is the Image Solve Platform, a full-stack application that provides AI-powered image processing with mathematical problem-solving capabilities. It consists of:

- **Backend**: Django 5.x REST API with PostgreSQL database
- **Frontend**: React 19 with TypeScript, Vite, and TailwindCSS

## Essential Commands

### Backend Development (from `/backend` directory)

```bash
# Start Docker services (PostgreSQL, Adminer, Mailcatcher)
docker compose up -d

# Install dependencies (using uv as per project rules)
make install
# OR: uv add -e ".[dev]"

# Run database migrations
make migrate
# OR: uv run python manage.py makemigrations && uv run python manage.py migrate

# Bootstrap demo data (creates test users and tokens)
uv run python manage.py bootstrap_demo
# Creates: admin@example.com/admin123 and user@example.com/user123

# Start development server
make dev
# OR: uv run python manage.py runserver

# Run tests
make test
# OR: uv run pytest

# Run specific test
uv run pytest tests/test_math_solver.py

# Type checking with mypy
make typecheck
# OR: uv run mypy .

# Code formatting
make format
# OR: uv run black . && uv run ruff check --fix .

# Linting
make lint
# OR: uv run ruff check .

# Create superuser
make superuser
# OR: uv run python manage.py createsuperuser

# Management commands
uv run python manage.py create_billing_periods  # Create billing periods
uv run python manage.py mark_overdue_periods    # Mark overdue periods
```

### Frontend Development (from `/frontend` directory)

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Type checking
npm run build  # TypeScript checks during build

# Linting
npm run lint

# Code formatting
npm run format
npm run format:check  # Check without fixing

# Preview production build
npm run preview
```

### Docker Services

```bash
# PostgreSQL: localhost:5432 (postgres/postgres)
# Adminer UI: http://localhost:8090
# Mailcatcher: http://localhost:1080 (SMTP on 1025)

# View all services status
docker compose ps

# Stop all services
docker compose down

# Reset database (careful!)
docker compose down -v && docker compose up -d
```

## Architecture Overview

### Backend Structure

The Django backend follows a modular app architecture with clear separation of concerns:

#### Core Apps

1. **config/** - Django project configuration
   - Main settings, URL routing, WSGI configuration
   - Environment-based configuration via .env file

2. **customers/** - Authentication and user management
   - Custom email-based authentication (no username)
   - Invite code system for registration
   - API token management with Bearer authentication
   - Email verification workflow

3. **core/** - Business logic and AI integration
   - OpenAI Vision API integration for image processing
   - Mock mode for development (USE_MOCK_OPENAI=true)
   - Request ID tracking for debugging
   - Service layer pattern for external integrations

4. **usage/** - Billing and usage tracking
   - Request logging with detailed history
   - Billing period management (monthly cycles)
   - Cost calculation (configurable per-request pricing)

#### Authentication Flow

The system uses dual authentication:
- **Session-based**: For web portal access (cookies + CSRF)
- **Bearer tokens**: For API access (prefixed with `tok_`)

Tokens are stored as secure hashes, with only the prefix visible in the database.

#### Key Middleware & Services

- Request ID middleware for tracing
- CORS configuration for frontend integration
- Argon2 password hashing
- Email verification tokens with expiration
- Camel case JSON transformation (djangorestframework-camel-case)

### Frontend Structure

React application with modern tooling:

#### Core Technologies
- React 19 with TypeScript
- Vite for build tooling
- React Query for server state management
- React Hook Form with Zod validation
- React Router v7 for navigation
- Axios for HTTP requests
- TailwindCSS for styling

#### Key Patterns

1. **Authentication Context**: Centralized auth state management
2. **Protected Routes**: Route guards for authenticated access
3. **Service Layer**: API calls abstracted in `/services`
4. **Custom Hooks**: Reusable logic in `/hooks`
5. **Type Safety**: Full TypeScript with strict mode

## API Endpoints

### Public Endpoints
- `POST /api/customers/register` - User registration with invite code
- `POST /api/customers/login` - User authentication
- `GET /api/customers/verify-email` - Email verification

### Session-Authenticated Endpoints
- `POST /api/customers/logout` - End session
- `GET /api/customers/me` - Current user info
- `POST /api/customers/password/change` - Change password
- `GET/POST /api/customers/tokens` - Manage API tokens
- `DELETE /api/customers/tokens/{id}` - Revoke token
- `GET /api/customers/usage/requests` - Request history
- `GET /api/customers/usage/summary` - Usage statistics
- `GET /api/customers/billing/*` - Billing information

### Bearer Token Endpoints
- `POST /api/core/solve` - Process image with AI (requires Bearer token)
- `GET /api/core/health` - Service health check

## Development Workflow

### Setting Up a New Feature

1. **Backend**: Create/modify Django app, add models, serializers, views, and URLs
2. **Frontend**: Create React components, add routes, implement API integration
3. **Testing**: Write pytest tests for backend, consider frontend tests
4. **Type Checking**: Ensure mypy passes for backend code
5. **Documentation**: Update API docs (auto-generated via drf-spectacular)

### Database Changes

```bash
# Create migrations after model changes
uv run python manage.py makemigrations

# Review migration SQL
uv run python manage.py sqlmigrate <app_name> <migration_number>

# Apply migrations
uv run python manage.py migrate
```

### Testing Strategy

- Backend: pytest with Django test client
- Mock external services (OpenAI) using USE_MOCK_OPENAI
- Test data generation with model-bakery
- API mocking with requests-mock

## Environment Configuration

Key environment variables (set in `.env`):

```bash
# Django
DJANGO_SECRET_KEY=<generated>
DJANGO_DEBUG=1  # 0 for production
ALLOWED_HOSTS=localhost,*********

# Database
DATABASE_URL=postgres://postgres:postgres@localhost:5432/app

# Email (Mailcatcher for dev)
EMAIL_HOST=localhost
EMAIL_PORT=1025

# OpenAI
OPENAI_API_KEY=sk-...
USE_MOCK_OPENAI=true  # false for production

# Billing
COST_PER_REQUEST_CENTS=100

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

## Access Points

### Development URLs
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/api/docs/
- Django Admin: http://localhost:8000/admin/
- Frontend: http://localhost:5173
- Mailcatcher: http://localhost:1080
- Adminer: http://localhost:8090

## Common Tasks

### Debug API Requests
1. Check request ID in response headers
2. Review RequestLog entries in Django admin
3. Check Mailcatcher for email issues

### Update Dependencies
```bash
# Backend
uv add package-name  # Add new package
uv sync              # Sync with pyproject.toml

# Frontend
npm install package-name
```

### Production Deployment Checklist
- Set DJANGO_DEBUG=0
- Generate strong DJANGO_SECRET_KEY
- Configure real email provider
- Set USE_MOCK_OPENAI=false with valid API key
- Enable HTTPS and security headers
- Configure proper CORS origins
- Set up monitoring and logging
- Configure database backups
