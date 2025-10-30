# TRC Platform Authentication UAT Tests

This directory contains comprehensive User Acceptance Testing (UAT) scripts for the TRC Platform authentication system. These tests validate all authentication flows from admin management through user registration, email verification, and account management.

## Quick Start

### Prerequisites

1. **TRC Platform Application** running on `localhost:8080`
2. **PostgreSQL Database** with migrated schema
3. **Mailcatcher** running on ports 1025 (SMTP) and 1080 (Web UI)
4. **Python 3.13+** with UV installed

### Installation

```bash
# Install UV if not already installed
curl -LsSsf https://astral.sh/uv/install.sh | sh

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
uv run python test-01-admin-login.py

# Run all tests
uv run python run-all-tests.py

# Quick run (required tests only)
uv run python run-all-tests.py --required-only

# Run specific functionality
uv run python run-all-tests.py --filter admin
uv run python run-all-tests.py --filter user
uv run python run-all-tests.py --filter email
```

### Test Scripts Overview

| Test Script | Description | Duration |
|-------------|-------------|----------|
| `test-01_admin_login.py` | Admin authentication and JWT token generation | 5 min |
| `test-02_create_invite_codes.py` | Admin invite code creation and management | 10 min |
| `test-03_user_registration.py` | Complete user registration flow | 15 min |
| `test-04_email_verification.py` | Email verification workflow | 10 min |
| `test-05_resend_verification.py` | Resend verification email functionality | 10 min |
| `test_06_user_login.py` | User authentication and profile access | 10 min |
| `test_07_password_change.py` | User password change functionality | 10 min |
| `test_08_accept_terms.py` | Terms and disclaimer acceptance | 5 min |
| `test_09_error_scenarios.py` | Error handling and validation testing | 20 min |
| `test_10_complete_flow.py` | End-to-end integration testing | 30-45 min |

### Test Execution Order

Tests should be executed in this order for proper dependency management:

```
TEST-01 → TEST-02 → TEST-03 → TEST-04 → TEST-05 → TEST-06 → TEST-07 → TEST-08 → TEST-09 → TEST-10
```

## Test Data

### Bootstrap Admin User
- **Email**: `admin@trc-platform.local`
- **Password**: `Admin123!`
- **User ID**: `550e8400-e29b-41d4-a716-446655440000`

### Pre-loaded Invite Codes
- `TESTCODE123` - Expires: 2025-12-31 23:59:59
- `DEVINVITE456` - Expires: 2025-12-31 23:59:59
- `WELCOMETEST` - Expires: 2025-12-31 23:59:59

## Results and Reporting

Tests generate:
- **Colored console output** with clear pass/fail indicators
- **Detailed step-by-step logging**
- **JSON result files** for integration
- **Comprehensive error reporting**

Results are saved to `test-results.json` in the current directory.

## Architecture

### Framework Components
- **uat_config.py** - Centralized configuration management
- **uat_test_framework.py** - Base testing framework with utilities
- **Individual test scripts** - Specific test implementations
- **run_all_tests.py** - Test suite runner with reporting

### Key Features
- **Database Integration** - Direct database queries for state verification
- **Email Testing** - Mailcatcher API integration
- **Token Management** - Secure token storage and reuse
- **Error Handling** - Graceful failure with detailed messages
- **Flexible Execution** - Support for filtering and skipping tests

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
   mvn spring-boot:run -Dspring-boot.run.profiles=dev
   ```

4. **Permission Errors**
   ```bash
   # Create test data directory
   mkdir -p /tmp/uat-test-data
   chmod 777 /tmp/uat-test-data
   ```

### Debug Mode

Enable debug logging:
```bash
export UAT_LOG_LEVEL="DEBUG"
uv run python test-01-admin-login.py
```

### Cleanup

Clean up test data:
```bash
# Remove temporary files
rm -rf /tmp/uat-test-data/

# Clear test results
rm -f test-results.json
```

## Security Considerations

- Tokens are stored temporarily in `/tmp/uat-test-data/`
- Tests use example.com domains
- No real user data is used
- Database can be reset after testing

## Dependencies

The project uses modern Python dependencies managed by UV:

- **requests** - HTTP client
- **psycopg2-binary** - PostgreSQL adapter
- **PyJWT** - JWT token handling
- **colorama** - Colored console output
- **pydantic** - Data validation
- **python-dateutil** - Date utilities
- **python-dotenv** - Environment variables
- **pyyaml** - Configuration management
- **loguru** - Enhanced logging
- **faker** - Test data generation
- **jsonschema** - JSON validation
- **psutil** - Performance monitoring
- **cryptography** - Cryptographic utilities

## Development

### Adding New Tests

1. Follow the existing test script structure
2. Use the provided framework utilities
3. Add appropriate error handling and validation
4. Update run_all_tests.py if needed

### Development Dependencies

Install development dependencies for enhanced features:

```bash
uv sync --dev
```

This includes:
- pytest (testing framework)
- black (code formatting)
- flake8 (linting)
- mypy (type checking)
- httpx (alternative HTTP client)
- selenium (browser automation)

---

**Happy Testing! 🎉**

For questions or issues, refer to the test output logs or check the application status.