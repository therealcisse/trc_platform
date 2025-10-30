# TRC Platform API Token UAT Tests

This directory contains comprehensive User Acceptance Testing (UAT) scripts for the TRC Platform API token system. These tests validate complete API token functionality including creation, authentication, listing, revocation, and security scenarios.

## Quick Start

### Prerequisites

1. **TRC Platform Application** running on `localhost:8080`
2. **PostgreSQL Database** with migrated schema
3. **Mailcatcher** running on ports 1025 (SMTP) and 1080 (Web UI)
4. **Python 3.13+** with UV installed

**Note**: Tests are now self-contained and do not require any prior UAT/auth test execution. Each test creates its own users and data for complete isolation.

### Installation

```bash
# Install UV if not already installed
curl -LsSsf https://astral.sh/uv/install.sh | sh

# Navigate to API token test directory
cd UAT/api_token

# Initialize the project and install dependencies
uv sync

# Activate virtual environment (optional, uv handles this automatically)
source .venv/bin/activate
```

### Configuration

Set environment variables:

```bash
# Application URLs
export UAT_APP_URL="http://localhost:8080"
export UAT_DATABASE_URL="postgresql://localhost:5432/trc_platform"
export UAT_MAILCATCHER_URL="http://localhost:1080"

# Optional: Log level
export UAT_LOG_LEVEL="INFO"
```

## Running Tests

### Individual Tests

```bash
# Run individual test
uv run python test-01-user-registration.py

# Run all tests
uv run python run-all-tests.py

# Quick run (required tests only)
uv run python run-all-tests.py --required-only

# Run specific functionality
uv run python run-all-tests.py --filter token
uv run python run-all-tests.py --filter authentication
uv run python run-all-tests.py --filter creation
```

### Test Scripts Overview

| Test Script | Description | Duration | Required |
|-------------|-------------|----------|----------|
| `test-01_user_registration.py` | Create dedicated user for API token testing (self-contained) | 15 min | Yes |
| `test-02_api_token_creation.py` | API token creation with various configurations (self-contained) | 10 min | Yes |
| `test-03_api_token_authentication.py` | API token authentication via headers (self-contained) | 10 min | Yes |
| `test-04_api_token_listing.py` | API token listing and pagination (self-contained) | 5 min | No |
| `test-05_api_token_revocation.py` | API token revocation functionality (self-contained) | 10 min | No |
| `test-06_token_security_scenarios.py` | Token security and validation scenarios (self-contained) | 15 min | No |
| `test-07_token_expiration_handling.py` | Token expiration and time-based scenarios (self-contained) | 10 min | No |

### Test Execution Order

Tests can be executed in any order as they are **completely self-contained**. Each test:
- Creates its own unique test user
- Generates its own API tokens
- Cleans up all created data automatically

For organized execution, the recommended order is:
```
TEST-01 → TEST-02 → TEST-03 → TEST-04 → TEST-05 → TEST-06 → TEST-07
```

However, any test can be run independently without dependencies on other tests.

## Architecture Overview

### Framework Components
- **uat_config.py** - Centralized configuration management for API token testing
- **uat_test_framework.py** - Base testing framework with API token utilities
- **Individual test scripts** - Specific API token test implementations
- **run-all-tests.py** - Test suite runner with comprehensive reporting

### Key Features
- **Complete Test Isolation** - Each test is self-contained with its own users and data
- **Automatic Cleanup** - Tests clean up all created data to ensure no persistence between tests
- **Database Integration** - Direct database queries for API token state verification
- **Token Authentication Testing** - Both X-API-Token and Authorization Bearer formats
- **Security Validation** - Token format, BCrypt hash validation, and rejection testing
- **Usage Tracking** - Verification of token usage monitoring
- **Test-Driven Approach** - Tests work with simulated responses when endpoints aren't implemented

### Test Isolation & Cleanup

Each test follows a strict isolation pattern:

1. **Setup Phase**:
   - Creates unique test user with timestamp-based email
   - Generates its own API tokens for testing scenarios
   - Establishes dedicated database connections

2. **Test Execution Phase**:
   - Performs all test operations using self-created data
   - No dependency on external token storage or previous tests
   - Validates database state and API responses

3. **Cleanup Phase**:
   - Deletes all created API tokens from database
   - Removes test user from database
   - Clears all in-memory test data
   - Ensures no data persistence between test runs

This approach guarantees:
- ✅ **No test dependencies** - Any test can run independently
- ✅ **Complete data isolation** - No shared state between tests
- ✅ **Clean environment** - No leftover test data
- ✅ **Reproducible results** - Same results on every run

## Test Coverage

### Core Functionality Tests

#### TEST-01: User Registration for API Token Testing
- Creates dedicated test user for API token functionality (self-contained)
- Follows same pattern as UAT/auth but with complete isolation
- Tests user creation, authentication, and verification workflow
- Cleans up all user data after test completion

#### TEST-02: API Token Creation
- Tests token creation without expiration
- Tests token creation with custom expiration dates
- Validates token format (tok_ prefix, base64url encoding)
- Verifies database storage (BCrypt hashing, prefix extraction)
- Tests token creation validation scenarios

#### TEST-03: API Token Authentication
- Tests X-API-Token header authentication
- Tests Authorization Bearer token format
- Validates token usage tracking (last_used_at timestamps)
- Tests invalid token rejection scenarios
- Verifies token format validation

### Advanced Functionality Tests

#### TEST-04: API Token Listing
- Tests GET /api/customers/tokens endpoint
- Verifies pagination structure
- Validates token metadata (no actual tokens exposed)
- Tests filtering by active/revoked status

#### TEST-05: API Token Revocation
- Tests DELETE /api/customers/tokens/{id} endpoint
- Verifies token revocation in database
- Tests that revoked tokens no longer authenticate
- Validates audit trail (revoked_at timestamps)

#### TEST-06: Token Security Scenarios
- Tests malformed token rejection
- Tests expired token handling
- Tests revoked token rejection
- Validates BCrypt hash security
- Tests authentication bypass prevention

#### TEST-07: Token Expiration Handling
- Tests token creation with expiration
- Validates expiration checking logic
- Tests timezone handling
- Verifies expired token rejection

## Expected API Endpoints (Test-Driven Contract)

### Create API Token
```http
POST /api/customers/tokens
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "name": "My API Token",
  "expiresAt": "2025-12-31T23:59:59"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "token": "tok_abcdefghijklmnopqrstuvwxyz123456",
  "name": "My API Token",
  "createdAt": "2025-01-15T10:30:00",
  "expiresAt": "2025-12-31T23:59:59"
}
```

### List API Tokens
```http
GET /api/customers/tokens
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "content": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "My API Token",
      "tokenPrefix": "tok_abcdefghij",
      "createdAt": "2025-01-15T10:30:00",
      "lastUsedAt": "2025-01-15T14:20:00",
      "expiresAt": "2025-12-31T23:59:59",
      "revokedAt": null
    }
  ],
  "pageable": {
    "pageNumber": 0,
    "pageSize": 20,
    "totalElements": 1,
    "totalPages": 1
  }
}
```

### Revoke API Token
```http
DELETE /api/customers/tokens/{token_id}
Authorization: Bearer <jwt_token>
```

**Response:** 204 No Content

### Authenticate with API Token
```http
GET /api/customers/me
X-API-Token: tok_abcdefghijklmnopqrstuvwxyz123456
```

OR

```http
GET /api/customers/me
Authorization: Bearer tok_abcdefghijklmnopqrstuvwxyz123456
```

## Database Validation

The tests verify the following database state:

### API Tokens Table
```sql
CREATE TABLE api_tokens (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  token_hash VARCHAR(255) NOT NULL UNIQUE,
  token_prefix VARCHAR(64) NOT NULL,
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL,
  last_used_at TIMESTAMP NULL,
  expires_at TIMESTAMP NULL,
  revoked_at TIMESTAMP NULL
);
```

### Verification Points
- **BCrypt Hash Storage** - Tokens are never stored in plain text
- **Token Prefix** - First 12 characters stored for easy identification
- **Usage Tracking** - `last_used_at` field updated on authentication
- **Revocation Audit** - `revoked_at` timestamp set when tokens are revoked
- **User Association** - Tokens properly linked to user accounts

## Security Testing

### Token Format Validation
- Tokens must start with `tok_` prefix
- Token body must be valid base64url encoding
- Total length must be 47 characters (4 + 43)
- BCrypt hash validation for stored tokens

### Authentication Security
- Both `X-API-Token` and `Authorization: Bearer` headers supported
- Invalid tokens properly rejected with 401 status
- Expired tokens rejected appropriately
- Revoked tokens immediately invalidated

### Usage Monitoring
- Token usage tracked in request logs
- Last used timestamps updated on authentication
- Usage counts maintained for billing/audit

## Test Data Management

### Token Storage
- Created tokens stored in `/tmp/uat-test-data/api_tokens.json`
- Individual tokens accessible via TokenManager
- Cross-test token sharing for end-to-end scenarios

### User Credentials
- Test user credentials stored in `/tmp/uat-test-data/api_token_user_credentials.txt`
- Email verification tokens preserved for account activation
- Admin tokens stored for setup operations

### Cleanup
- Test data automatically cleaned up between runs
- Temporary files managed in `/tmp/uat-test-data/`
- Database state verified but not modified by tests

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check PostgreSQL is running
   docker-compose ps db

   # Test connection
   psql -h localhost -U trc_user -d trc_platform -c "SELECT 1;"
   ```

2. **Mailcatcher Connection Failed**
   ```bash
   # Check Mailcatcher is running
   docker-compose ps mailcatcher

   # Verify ports
   telnet localhost 1080
   telnet localhost 1025
   ```

3. **Application Not Responding**
   ```bash
   # Check application health
   curl http://localhost:8080/api/core/health

   # Check application logs
   ./gradlew bootRun
   ```

4. **Missing Dependencies**
   ```bash
   # Run TEST-01 from UAT/auth first
   cd ../auth
   uv run python run-all-tests.py --required-only

   # Then return to API token tests
   cd ../api_token
   ```

5. **Permission Errors**
   ```bash
   # Create test data directory
   mkdir -p /tmp/uat-test-data
   chmod 777 /tmp/uat-test-data
   ```

### Debug Mode

Enable debug logging:
```bash
export UAT_LOG_LEVEL="DEBUG"
uv run python test-01-user-registration.py
```

### Cleanup

Clean up test data:
```bash
# Remove temporary files
rm -rf /tmp/uat-test-data/

# Clear test results
rm -f test-results.json
```

## Integration with UAT/auth

The API token tests depend on the UAT/auth test suite for:

1. **Bootstrap Admin User** - Uses admin credentials from auth tests
2. **Invite Code System** - Leverages existing invite code functionality
3. **User Registration Flow** - Reuses registration email verification
4. **Authentication Framework** - Extends auth testing framework

Run the auth tests first:
```bash
cd ../auth
uv run python run-all-tests.py --required-only
cd ../api_token
uv run python run-all-tests.py --required-only
```

## Production Readiness

When all tests pass, the following production readiness criteria are met:

✅ **API Token Lifecycle Management**
- Token creation with optional expiration
- Token listing with proper pagination
- Token revocation with audit trail

✅ **Authentication Security**
- Multiple authentication header formats supported
- Token format validation implemented
- BCrypt hash security verified

✅ **Usage Monitoring**
- Token usage tracking functional
- Last used timestamps maintained
- Integration with request logging system

✅ **Error Handling**
- Comprehensive error responses
- Invalid token rejection
- Proper HTTP status codes

✅ **Database Integration**
- Secure token storage with hashing
- Audit trail maintenance
- Performance optimized queries

## Dependencies

The project uses modern Python dependencies managed by UV:

- **requests** - HTTP client for API calls
- **psycopg2-binary** - PostgreSQL database adapter
- **bcrypt** - Password hashing for token validation
- **PyJWT** - JWT token handling
- **colorama** - Colored console output
- **pydantic** - Data validation
- **python-dateutil** - Date utilities
- **python-dotenv** - Environment variables
- **loguru** - Enhanced logging
- **faker** - Test data generation

## Development

### Adding New Tests

1. Follow the existing test script structure
2. Use the provided framework utilities and ApiTokenHelper
3. Add appropriate error handling and validation
4. Update run-all-tests.py if needed
5. Document test scenarios in README

### Test-Driven Development

The tests are designed to work with simulated responses when API endpoints aren't implemented yet. This allows for:

- **Test-driven development** - Write tests before implementing endpoints
- **Contract validation** - Define expected API contracts
- **Incremental development** - Implement endpoints gradually
- **Continuous testing** - Run tests throughout development

### Development Dependencies

Install development dependencies for enhanced features:

```bash
uv sync --dev
```

This includes testing, formatting, linting, and type checking tools.

---

**Happy Testing! 🎉**

For questions or issues, refer to the test output logs or check the application status.