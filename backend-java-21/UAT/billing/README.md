# TRC Platform Billing API UAT Tests

Comprehensive User Acceptance Testing (UAT) suite for the Billing API in the TRC Platform Spring Boot backend. Tests all user-facing and admin endpoints for billing period management, payment processing, and usage tracking.

## Quick Start

### Prerequisites

1. **TRC Platform Application** running on `localhost:8080`
2. **PostgreSQL Database** with migrated schema
3. **Mailcatcher** running on ports 1025 (SMTP) and 1080 (Web UI)
4. **Python 3.13+** with UV installed

### Installation

```bash
# Navigate to billing test directory
cd UAT/billing

# Initialize project and install dependencies
uv sync

# Activate virtual environment (optional, uv handles automatically)
source .venv/bin/activate
```

### Configuration

Set environment variables (optional, defaults provided):

```bash
export UAT_APP_URL="http://localhost:8080"
export UAT_DATABASE_URL="postgresql://trc_user:trc_password@localhost:5432/trc_platform"
export UAT_MAILCATCHER_URL="http://localhost:1080"
export UAT_LOG_LEVEL="INFO"
```

## Running Tests

### Run All Tests

```bash
uv run python run-all-tests.py
```

### Run Required Tests Only

```bash
uv run python run-all-tests.py --required-only
```

### Run Individual Test

```bash
uv run python test-01-user-registration.py
uv run python test-02-current-billing-period.py
```

### Run with Filter

```bash
uv run python run-all-tests.py --filter admin
uv run python run-all-tests.py --filter lifecycle
uv run python run-all-tests.py --filter payment
```

## Test Suite Overview

### Total Tests: 11

| # | Test | Type | Priority | Status | Duration |
|---|------|------|----------|--------|----------|
| 01 | User Registration | Setup | HIGH | Implemented | 15 min |
| 02 | Current Billing Period | Read | HIGH | To Implement | 10 min |
| 03 | List Billing Periods | List | HIGH | To Implement | 10 min |
| 04 | Billing Period Details | Detail | HIGH | To Implement | 10 min |
| 05 | Usage Summary | Analytics | MEDIUM | To Implement | 5 min |
| 06 | Admin List Periods | Admin | LOW | To Implement | 5 min |
| 07 | Admin Mark Paid | Admin Write | HIGH | To Implement | 10 min |
| 08 | Admin Mark Overdue | Admin Write | MEDIUM | To Implement | 8 min |
| 09 | Admin Mark Waived | Admin Write | MEDIUM | To Implement | 8 min |
| 10 | Billing Period Lifecycle | Integration | HIGH | To Implement | 20 min |
| 11 | Cost Calculation | Validation | MEDIUM | To Implement | 10 min |

## Endpoints Tested

### User-Facing Endpoints

- `GET /api/billing/current` - Get current billing period
- `GET /api/billing/periods` - List all billing periods
- `GET /api/billing/periods/{periodId}` - Get period details with request logs
- `GET /api/usage/summary` - Get usage statistics

### Admin Endpoints

- `GET /api/v1/admin/billing/periods` - List all periods (with filtering)
- `POST /api/v1/admin/billing/periods/{periodId}/mark-paid` - Mark as paid
- `POST /api/v1/admin/billing/periods/{periodId}/mark-overdue` - Mark as overdue
- `POST /api/v1/admin/billing/periods/{periodId}/mark-waived` - Mark as waived

## Test Architecture

### Self-Contained Tests

Each test is completely independent:

1. **Setup**: Creates dedicated test user with timestamp-based email
2. **Execute**: Performs test operations using self-created data
3. **Cleanup**: Removes test-specific data (optional)

### No Shared Dependencies

- Tests can run in any order
- No data carried between tests
- Complete isolation guaranteed
- Can repeat tests without cleanup
- Run individual tests or full suite

### Test Data Management

**Storage Location**: `/tmp/uat-billing-test-data/`

**Files**:
- `billing_data.json` - Test period data and responses
- `admin_token.txt` - Admin authentication (within test)
- `user_credentials.txt` - User credentials (within test)

## Framework Components

### uat_config.py
Centralized configuration for all tests:
- API endpoints
- Database queries
- Response field validation
- Billing constants (50 cents per request)
- Payment statuses (pending, paid, overdue, waived)

### uat_test_framework.py
Base framework (reused from UAT/api_token/):
- `DatabaseHelper` - PostgreSQL operations
- `HTTPClient` - REST API calls with auth
- `EmailVerificationHelper` - Mailcatcher integration
- `TokenManager` - JWT and token storage
- `TestReporting` - Results formatting

### billing_helpers.py
Billing-specific utilities:
- `BillingHelper` - Billing validation and queries
- `BillingDataManager` - Test data persistence

## Test Execution Order

Recommended execution order (all tests independent):

1. TEST-01 → User Registration
2. TEST-02 → Current Billing Period
3. TEST-03 → List Billing Periods
4. TEST-04 → Period Details
5. TEST-05 → Usage Summary
6. TEST-06 → Admin List (stub)
7. TEST-07 → Mark Paid
8. TEST-08 → Mark Overdue
9. TEST-09 → Mark Waived
10. TEST-10 → Lifecycle
11. TEST-11 → Cost Calculation

## Test Plan

See [TEST_PLAN.md](TEST_PLAN.md) for comprehensive test specifications including:

- Detailed test steps
- Expected results
- Database verification queries
- API contract validation
- Edge cases and error scenarios

## Database Verification

### Billing Periods Table

```sql
CREATE TABLE billing_periods (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_requests INTEGER NOT NULL DEFAULT 0,
    total_cost_cents INTEGER NOT NULL DEFAULT 0,
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    payment_status VARCHAR(50) NOT NULL,
    paid_at TIMESTAMP NULL,
    paid_amount_cents INTEGER NULL,
    payment_reference VARCHAR(255) NULL,
    notes TEXT NULL,
    version BIGINT,
    INDEX idx_user_period (user_id, period_start),
    INDEX idx_current_period (is_current)
);
```

### Request Logs Table

```sql
CREATE TABLE request_logs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    billing_period_id UUID NOT NULL REFERENCES billing_periods(id),
    request_ts TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL,
    duration_ms INTEGER NOT NULL,
    flow_id VARCHAR(255) NOT NULL,
    result TEXT NULL
);
```

## Key Business Rules

1. **Billing Periods**
   - One period per calendar month (1st to last day)
   - Automatic creation on-the-fly
   - Monthly assignment based on Berlin timezone

2. **Cost Calculation**
   - 50 cents per API request
   - Formula: `totalCostCents = totalRequests * 50`
   - Updated automatically

3. **Payment Status Flow**
   ```
   pending → paid (normal payment)
   pending → overdue (unpaid past due)
   pending → waived (charges forgiven)
   overdue → paid (late payment)
   overdue → waived (late charges forgiven)
   ```

4. **User Isolation**
   - Users can only view their own billing
   - Admin can view all periods
   - Admin can modify payment status

5. **Current Period**
   - Only ONE period per user marked as `current = true`
   - Auto-created if missing
   - New period created on 1st of each month

## Error Handling

### HTTP Status Codes

| Code | Scenario |
|------|----------|
| 200 | Success |
| 400 | Bad request (invalid data) |
| 401 | Unauthorized (no auth) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not found (period doesn't exist) |

### Validation Errors

**Mark Paid Endpoint**:
- `paidAmountCents` must be >= 0
- `paymentReference` must be provided and max 255 chars
- `paymentDate` must be valid ISO timestamp

**Authorization**:
- Non-admin users get 403 for admin endpoints
- Unauthenticated requests get 401
- Users can only access own billing data

## Integration with UAT/api_token

The Billing UAT shares infrastructure with UAT/api_token:

1. **Shared Framework**: Uses `uat_test_framework.py` from api_token
2. **Separate Config**: Own `uat_config.py` for billing-specific settings
3. **Separate Helpers**: Own `billing_helpers.py` for billing utilities
4. **Independent Tests**: Completely independent test suite

No dependencies on api_token tests - this is a standalone suite.

## Production Readiness Checklist

When all tests pass:

- **GET /api/billing/current** - Working
- **GET /api/billing/periods** - Working
- **GET /api/billing/periods/{periodId}** - Working
- **GET /api/usage/summary** - Working
- **POST mark-paid** - Working with validation
- **POST mark-overdue** - Working
- **POST mark-waived** - Working
- **Cost calculation** - Verified (50 cents per request)
- **Authorization** - Enforced for admin endpoints
- **Database integrity** - Confirmed
- **User isolation** - Verified
- **Payment status flow** - All transitions working

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

1. Create new test file: `test-XX-name.py`
2. Follow existing test class structure
3. Use `BillingHelper` for validation
4. Update `run-all-tests.py` if needed
5. Document in `TEST_PLAN.md`

### Code Style

- Python 3.13+ with type hints
- Use provided helpers (don't reinvent)
- Self-contained tests (no dependencies)
- Comprehensive error handling
- Detailed logging and output

### Testing New Functionality

1. Write test cases first (TDD)
2. Implement endpoint in backend
3. Run test to verify
4. Commit test + implementation

## Troubleshooting

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose ps db

# Test connection
psql -h localhost -U trc_user -d trc_platform -c "SELECT 1;"
```

### Mailcatcher Connection Failed

```bash
# Check Mailcatcher is running
docker-compose ps mailcatcher

# Verify ports
telnet localhost 1080
telnet localhost 1025
```

### Application Not Responding

```bash
# Check application health
curl http://localhost:8080/api/core/health

# Check application logs
cd ../..
./gradlew bootRun
```

### Permission Errors

```bash
# Create test data directory
mkdir -p /tmp/uat-billing-test-data
chmod 777 /tmp/uat-billing-test-data
```

### Debug Mode

```bash
export UAT_LOG_LEVEL="DEBUG"
uv run python test-01-user-registration.py
```

### Clean Up Test Data

```bash
# Remove temporary files
rm -rf /tmp/uat-billing-test-data/

# Clear test results
rm -f test-results.json
```

## CI/CD Integration

The tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Billing API UAT
  run: |
    cd UAT/billing
    uv sync
    uv run python run-all-tests.py --required-only
```

## Contributing

1. Ensure tests are self-contained
2. Follow existing patterns
3. Add comprehensive documentation
4. Update TEST_PLAN.md
5. Run full suite before committing

## License

MIT

## Support

For questions or issues:

1. Check TEST_PLAN.md for detailed specifications
2. Review test output logs for debugging
3. Check application logs for backend errors
4. Verify database state with provided SQL queries

---

**Last Updated**: January 2025
**Version**: 1.0.0
**Test Framework**: TRC Platform UAT Suite v1
