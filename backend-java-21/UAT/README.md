# TRC Platform Consolidated UAT Test Suite

> **Consolidated User Acceptance Testing Framework** - Authentication, API Token, Billing, and Usage domains

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![UV Package Manager](https://img.shields.io/badge/uv-✓-green.svg)](https://github.com/astral-sh/uv)
[![Tests](https://img.shields.io/badge/tests-31%20total-blue.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-4%20domains-green.svg)](tests/)

## 🎯 Overview

This is the **consolidated UAT test suite** for the TRC Platform, bringing together four separate testing domains into a single, unified framework. The consolidation achieved a **35% reduction in code** while eliminating **80% of duplication** and adding powerful cross-domain testing capabilities.

### 📊 Test Coverage

- **37 comprehensive tests** across 5 domains
- **Authentication (7 tests)** - User management, JWT tokens, email verification
- **API Token (7 tests)** - Programmatic access, token lifecycle, security
- **Billing (11 tests)** - Usage tracking, cost calculation, payment management
- **Usage (6 tests)** - Usage requests API, date filtering, pagination, security
- **Image Solve (6 tests)** - Image-based math problem solving and API validation

### 🏗️ Architecture

```
UAT/
├── 📁 tests/                     # Test implementations
│   ├── auth/                     # Authentication domain (7 tests)
│   ├── api_token/                # API token domain (7 tests)
│   ├── billing/                  # Billing domain (11 tests)
│   ├── usage/                    # Usage domain (6 tests)
│   └── image_solve/              # Image solve domain (6 tests)
│       └── images/               # Test images for math problems (27 files)
├── 🐍 uat_framework.py           # Core testing framework (1,007 lines)
├── 🛠️ auth_helpers.py            # Authentication utilities (775 lines)
├── 🛠️ api_token_helpers.py       # API token utilities (908 lines)
├── 🛠️ billing_helpers.py         # Billing utilities (1,168 lines)
├── 🛠️ usage_helpers.py           # Usage utilities (1,200+ lines)
├── 🛠️ image_solve_helpers.py     # Image solve utilities (400+ lines)
├── ⚙️ uat_config.py              # Consolidated configuration (372 lines)
├── 🚀 run_all_tests.py           # Unified test runner (850+ lines)
├── 📋 pyproject.toml             # Dependencies and tooling
└── 📖 README.md                  # This documentation
```

## 🚀 Quick Start

### Prerequisites

Ensure you have these services running:

1. **TRC Platform Application** - `localhost:8080`
   ```bash
   cd ../ && ./gradlew bootRun --args=--spring.profiles.active=dev
   ```

2. **PostgreSQL Database** - `localhost:5432/trc_platform`
   ```bash
   # Database should be migrated via Flyway (automatic on app startup)
   cd ../ && docker compose up
   ```

3. **Mailcatcher** - Ports 1025 (SMTP) & 1080 (Web UI)
   ```bash
   cd ../ && docker compose up
   ```

4. **Python 3.13+ & UV** - Package management
   ```bash
   # Install UV if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Installation

```bash
# Navigate to UAT directory
cd UAT

# Install dependencies and create virtual environment
uv sync

# Verify installation
uv run --version
```

### Environment Configuration

Set environment variables (optional - defaults provided):

```bash
# Application URLs
export UAT_APP_URL="http://localhost:8080"
export UAT_DATABASE_URL="postgresql://trc_user:trc_password@localhost:5432/trc_platform"
export UAT_MAILCATCHER_URL="http://localhost:1080"

# Optional: Logging
export UAT_LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
```

## 🧪 Running Tests

### Basic Commands

```bash
# Run all tests across all domains
uv run run_all_tests.py

# Run tests for specific domain
uv run run_all_tests.py --domain auth        # Authentication only
uv run run_all_tests.py --domain api_token   # API tokens only
uv run run_all_tests.py --domain billing     # Billing only
uv run run_all_tests.py --domain usage       # Usage only
uv run run_all_tests.py --domain image_solve # Image solve only

# Filter tests by name, ID, or description
uv run run_all_tests.py --filter "user registration"
uv run run_all_tests.py --filter "AUTH-01"
uv run run_all_tests.py --filter "billing"

# Show test plan without execution
uv run run_all_tests.py --dry-run

# Enable verbose output
uv run run_all_tests.py --verbose
```

### Advanced Usage

```bash
# Combine filters and domains
uv run run_all_tests.py --domain auth --filter "login"

# Run multiple tests matching pattern
uv run run_all_tests.py --filter "token.*security"

# Quick test execution
uv run run_all_tests.py --filter "setup"  # Run setup tests only
```

## 📋 Test Details

### Authentication Domain (`AUTH-01` to `AUTH-07`)

| Test ID | Description | Key Features |
|---------|-------------|--------------|
| `AUTH-01` | Admin Login | Admin authentication, JWT validation |
| `AUTH-02` | Create Invite Codes | Bulk invite code generation |
| `AUTH-03` | User Registration | Complete user signup workflow |
| `AUTH-04` | Email Verification | Email verification via Mailcatcher |
| `AUTH-05` | Resend Verification | Email resend functionality |
| `AUTH-06` | User Login | User authentication, token refresh |
| `AUTH-07` | Password Change | Secure password updates |

### API Token Domain (`TOKEN-01` to `TOKEN-07`)

| Test ID | Description | Key Features |
|---------|-------------|--------------|
| `TOKEN-01` | User Setup | API token user preparation |
| `TOKEN-02` | Token Creation | Create tokens with custom settings |
| `TOKEN-03` | Token Authentication | Validate API token authentication |
| `TOKEN-04` | Token Listing | List and manage API tokens |
| `TOKEN-05` | Token Revocation | Secure token revocation |
| `TOKEN-06` | Token Security | Security scenario testing |
| `TOKEN-07` | Token Expiration | Handle token lifecycle |

### Billing Domain (`BILL-01` to `BILL-11`)

| Test ID | Description | Key Features |
|---------|-------------|--------------|
| `BILL-01` | User Setup | Billing user preparation |
| `BILL-02` | Current Billing Period | Active period management |
| `BILL-03` | List Billing Periods | Period history and pagination |
| `BILL-04` | Billing History | Complete billing audit trail |
| `BILL-05` | Usage Summary | Usage statistics and costs |
| `BILL-06` | Mark Period Paid | Payment status management |
| `BILL-07` | Mark Period Overdue | Overdue handling |
| `BILL-08` | Apply Waiver | Billing waivers and adjustments |
| `BILL-09` | Period Lifecycle | Complete period workflow |
| `BILL-10` | Cost Verification | Cost calculation accuracy |
| `BILL-11` | Admin Summary | Administrative billing overview |

### Usage Domain (`USAGE-01` to `USAGE-06`)

| Test ID | Description | Key Features |
|---------|-------------|--------------|
| `USAGE-01` | User Setup for Usage Testing | Create test user with request log data |
| `USAGE-02` | Basic Usage Requests Retrieval | API authentication and response validation |
| `USAGE-03` | Date Filtering Validation | Multiple date formats and range filtering |
| `USAGE-04` | Pagination Testing | Page sizes, navigation, and boundaries |
| `USAGE-05` | Data Security and Isolation | User data isolation and access control |
| `USAGE-06` | Error Handling and Edge Cases | Invalid inputs and error scenarios |

### Image Solve Domain (`IMG-01` to `IMG-06`)

| Test ID | Description | Key Features |
|---------|-------------|--------------|
| `IMG-01` | User Setup for Image Solve Testing | 6-step setup with API token creation |
| `IMG-02` | Basic Image Solve Functionality | Image upload with API token authentication |
| `IMG-03` | Response Structure Validation | Complete response schema and timing validation |
| `IMG-04` | Error Handling and Edge Cases | Authentication errors, invalid formats, boundaries |
| `IMG-05` | Billing Integration Verification | Request logs and billing period assignment |
| `IMG-06` | Comprehensive Image Suite Test | All 27 test images with performance metrics |

## 🏛️ Framework Architecture

### Core Components

#### `uat_framework.py` - The Testing Engine
- **Database Operations** - PostgreSQL connection, queries, cleanup
- **HTTP Client** - Request handling, authentication, response validation
- **Email Verification** - Mailcatcher integration for email testing
- **Token Management** - JWT and API token generation/validation
- **Test Reporting** - Results tracking, logging, status reporting
- **Utility Functions** - Common helpers, validation, formatting

#### Domain-Specific Helpers

- **`auth_helpers.py`** (775 lines)
  - Authentication validation and user management
  - Email verification workflows
  - Password security utilities

- **`api_token_helpers.py`** (908 lines)
  - API token lifecycle management
  - Token security and validation
  - Permission testing utilities

- **`billing_helpers.py`** (1,168 lines)
  - Billing period calculations
  - Cost verification and accuracy validation
  - Payment status management

- **`usage_helpers.py`** (1,200+ lines)
  - Usage request tracking and validation
  - Data generation and cleanup utilities
  - Pagination and filtering test helpers

- **`image_solve_helpers.py`** (400+ lines)
  - Image processing and validation
  - API token authentication for image solving
  - Performance metrics and billing integration

### Test Design Principles

Each test follows these principles:

- ✅ **Self-Contained** - Creates and manages its own test data
- ✅ **Isolated** - No dependencies on other tests
- ✅ **Reproducible** - Consistent results across runs
- ✅ **Comprehensive** - Complete setup → execute → validate → cleanup
- ✅ **Documented** - Clear test purposes and validation steps

## 🛠️ Development Guide

### Adding New Tests

1. **Create Test File**
   ```bash
   # Choose appropriate domain
   touch tests/{domain}/test-XX-descriptive-name.py
   ```

2. **Follow Template Structure**
   ```python
   """
   Test: [Test Description]
   Domain: [auth|api_token|billing]
   Test ID: [DOMAIN-XX]
   """

   from uat_framework import *
   from {domain}_helpers import *

   def main():
       # Setup → Execute → Validate → Cleanup pattern
       pass
   ```

3. **Update Test Runner**
   - Add test definition to `run_all_tests.py`
   - Include proper metadata (ID, name, description, domain)

4. **Test Validation**
   ```bash
   # Verify test discovery
   uv run run_all_tests.py --dry-run --filter "your-test"

   # Run isolated test
   uv run tests/your-domain/test-XX-name.py
   ```

### Framework Extensions

- **New Domains** - Follow existing helper patterns
- **Enhanced Reporting** - Extend `TestResult` class
- **Additional Utilities** - Add to `uat_framework.py` or domain helpers
- **Configuration Updates** - Modify `uat_config.py`

## 🔧 Troubleshooting

### Common Issues & Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **Database Connection** | `Connection refused`, `authentication failed` | - Verify PostgreSQL running: `pg_isready`<br>- Check connection string in `UAT_DATABASE_URL`<br>- Ensure database migrated via app startup |
| **Mailcatcher Issues** | Email verification failures | - Start Mailcatcher: `mailcatcher`<br>- Check Web UI: http://localhost:1080<br>- Verify SMTP on port 1025 |
| **Application Unavailable** | `Connection refused` on port 8080 | - Start TRC Platform: `../gradlew bootRun`<br>- Check health: `curl http://localhost:8080/actuator/health` |
| **Import/Module Errors** | `ModuleNotFoundError`, import failures | - Run `uv sync` to refresh dependencies<br>- Verify correct working directory<br>- Check virtual environment activation |
| **Test Failures** | Validation errors, assertions failing | - Enable verbose output: `--verbose`<br>- Check individual test logs<br>- Verify environment configuration<br>- Run with `--dry-run` to verify selection |

### Debugging Commands

```bash
# Environment validation
uv run -c "from uat_config import UATConfig; print(UATConfig())"

# Database connectivity test
uv run -c "
from uat_framework import DatabaseHelper
db = DatabaseHelper()
print('Database connection:', '✅' if db.test_connection() else '❌')
"

# Email service validation
uv run -c "
import requests
response = requests.get('http://localhost:1080')
print('Mailcatcher:', '✅' if response.status_code == 200 else '❌')
"

# Test framework validation
uv run run_all_tests.py --dry-run --verbose
```

### Environment Variables Reference

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `UAT_APP_URL` | `http://localhost:8080` | TRC Platform base URL | `https://api.trc-platform.com` |
| `UAT_DATABASE_URL` | `postgresql://trc_user:trc_password@localhost:5432/trc_platform` | PostgreSQL connection | `postgresql://user:pass@host:5432/db` |
| `UAT_MAILCATCHER_URL` | `http://localhost:1080` | Mailcatcher Web UI | `http://mailcatcher.internal:1080` |
| `UAT_LOG_LEVEL` | `INFO` | Logging verbosity | `DEBUG` for detailed output |

## 📊 Metrics & Performance

### Consolidation Achievements

- **Code Reduction**: 35% decrease (9,418 → 6,000 lines)
- **Duplication Elimination**: 80% reduction in duplicate code
- **Framework Unification**: 3 separate frameworks → 1 consolidated
- **Test Coverage**: 25 tests across 3 domains maintained
- **Performance**: Faster execution through shared utilities

### Test Execution Metrics

```bash
# Quick performance check
time uv run run_all_tests.py --dry-run

# Individual test performance
time uv run run_all_tests.py --domain auth
```

## 🔒 Security Considerations

### Test Data Security

- **Isolated Test Database** - Uses dedicated test database
- **Temporary Email Addresses** - Uses `@uat-test.trc-platform.local` domain
- **Secure Password Handling** - Test passwords follow security policies
- **Token Cleanup** - All test tokens are revoked after testing

### Authentication Testing

- **Admin Account Isolation** - Dedicated admin credentials for testing
- **JWT Token Validation** - Comprehensive token lifecycle testing
- **API Token Security** - Revocation, expiration, and permission testing
- **Password Security** - Secure password change workflows validated

## 📈 Future Enhancements

### Planned Improvements

- **Cross-Domain Integration Tests** - Complete user workflow testing
- **Parallel Test Execution** - Faster test runs for large suites
- **HTML Test Reports** - Enhanced visualization and archiving
- **Performance Metrics** - Test execution time tracking
- **Test Data Fixtures** - Reusable test data across domains
- **Environment Profiles** - Support for multiple deployment environments

### Extension Points

- **New Domains** - Easy addition following existing patterns
- **Custom Helpers** - Domain-specific utilities
- **Enhanced Reporting** - Pluggable reporting systems
- **CI/CD Integration** - Automated pipeline integration

## 📞 Support & Contributing

### Getting Help

1. **Check this README** - Most common questions are answered here
2. **Review Troubleshooting Section** - Systematic issue resolution
3. **Check Test Logs** - Detailed error messages and stack traces
4. **Verify Environment** - Ensure all prerequisites are running

### Contributing Guidelines

1. **Follow Existing Patterns** - Maintain consistency with current tests
2. **Update Documentation** - Keep README and test documentation current
3. **Test Thoroughly** - Validate new tests work in isolation and suite
4. **Code Quality** - Follow Python best practices and existing style

## 📄 License

This UAT test suite is part of the TRC Platform project.

---

**Last Updated**: November 1, 2025
**Version**: 1.2.0
**Status**: ✅ Production Ready
**Tests**: 37 tests across 5 domains
**Framework**: Consolidated from 4 separate projects
