# Billing API UAT Test Plan

## Test Suite Overview

The Billing API UAT consists of 11 comprehensive, self-contained tests covering all user-facing and admin endpoints. Each test creates its own isolated test data and cleans up afterward.

**Total Test Duration**: ~100 minutes (with all tests)
**Required Tests**: TEST-01, TEST-02, TEST-03, TEST-04 (7 dependent tests)
**Optional Tests**: TEST-05 through TEST-11 (4 independent advanced tests)

---

## Test Execution Order

All tests are independent and can run in any order, but recommended sequence:

1. TEST-01 → User Registration (create test user)
2. TEST-02 → Get Current Billing Period (basic read)
3. TEST-03 → List Billing Periods (list operations)
4. TEST-04 → Get Billing Period Details (detail view)
5. TEST-05 → Get Usage Summary (usage analytics)
6. TEST-06 → Admin List Periods (admin list - stub)
7. TEST-07 → Admin Mark Paid (admin operations)
8. TEST-08 → Admin Mark Overdue (admin operations)
9. TEST-09 → Admin Mark Waived (admin operations)
10. TEST-10 → Billing Period Lifecycle (end-to-end)
11. TEST-11 → Cost Calculation Verification (validation)

---

## TEST-01: User Registration for Billing API Testing

**File**: `test-01-user-registration.py`
**Type**: Setup/Functional
**Priority**: HIGH (Required)
**Duration**: 15 minutes
**Status**: IMPLEMENTED

### Purpose
Create a dedicated test user for billing API testing. Self-contained test with complete user registration workflow.

### Test Steps

1. **Setup Environment**
   - Connect to database
   - Authenticate as admin
   - Connect to Mailcatcher
   - Clear existing emails

2. **Create Invite Code**
   - Generate unique timestamp-based invite code
   - POST to `/api/v1/admin/invites` with admin auth
   - Validate 200 response
   - Verify code is active

3. **Register Test User**
   - Generate unique timestamp-based email
   - POST to `/api/customers/register` with invite code
   - Validate 202 Accepted response
   - Store credentials for future use

4. **Verify User Email**
   - Wait for verification email in Mailcatcher
   - Extract verification token
   - Update database to mark email as verified (testing shortcut)

5. **Authenticate Test User**
   - POST to `/api/customers/login` with registered credentials
   - Validate 200 response with JWT token
   - Store token for subsequent tests
   - Verify user ID matches

6. **Verify User in Database**
   - Query database for user
   - Verify email_verified_at is set
   - Verify terms_accepted and disclaimer_acknowledged flags
   - Confirm user record is complete

### Expected Results

- User successfully registered
- Email marked as verified
- User can authenticate
- User data stored in `/tmp/uat-billing-test-data/billing_data.json`
- All steps pass: 6/6

### Database Verification

```sql
SELECT id, email, email_verified_at, user_accepted_terms, user_acknowledged_disclaimer
FROM users WHERE email LIKE 'billing-test-%@example.com'
-- Should return 1 row with email_verified_at IS NOT NULL
```

---

## TEST-02: Get Current Billing Period

**File**: `test-02-current-billing-period.py`
**Type**: Functional (Read)
**Priority**: HIGH (Required)
**Duration**: 10 minutes
**Status**: TO IMPLEMENT

### Purpose
Test GET `/api/billing/current` endpoint. Verify current billing period data and auto-creation behavior.

### Test Steps

1. **Setup Environment** (5 steps same as TEST-01)

2. **Get Current Billing Period**
   - GET `/api/billing/current` with user auth token
   - Validate 200 response
   - Validate response structure:
     - id (UUID)
     - isCurrent (Boolean = true)
     - periodStart (Date, 1st of current month)
     - periodEnd (Date, last of current month)
     - periodLabel (String, "Month Year" format)
     - paymentStatus (String = "pending")
     - totalRequests (Integer >= 0)
     - totalCostCents (Integer >= 0)

3. **Verify Period Dates**
   - Check periodStart is 1st of current month
   - Check periodEnd is last day of current month
   - Validate date range is full calendar month

4. **Verify Response Format**
   - All dates in ISO 8601 format (YYYY-MM-DD)
   - Period label matches "MMMM YYYY" format
   - Payment status is "pending"

5. **Verify Database State**
   - Query billing_periods table
   - Find current period (is_current = true)
   - Verify period matches response data
   - Confirm period belongs to authenticated user

### Expected Results

- Current period retrieved successfully
- Period spans full calendar month
- Status is "pending"
- Period was auto-created if needed
- All response fields present and formatted correctly
- All steps pass: 5/5

### Database Verification

```sql
SELECT * FROM billing_periods
WHERE is_current = true AND user_id = $1
-- Should return 1 row with period_start on 1st, period_end on last day
```

### API Contract Validation

```json
GET /api/billing/current
Authorization: Bearer {user_token}

Response 200:
{
  "id": "UUID",
  "isCurrent": true,
  "periodStart": "2025-01-01",
  "periodEnd": "2025-01-31",
  "periodLabel": "January 2025",
  "paymentStatus": "pending",
  "totalRequests": 0,
  "totalCostCents": 0
}
```

---

## TEST-03: List Billing Periods

**File**: `test-03-list-billing-periods.py`
**Type**: Functional (List/Pagination)
**Priority**: HIGH (Required)
**Duration**: 10 minutes
**Status**: TO IMPLEMENT

### Purpose
Test GET `/api/billing/periods` endpoint. Verify listing, pagination, and response wrapping.

### Test Steps

1. **Setup Environment** (create user)

2. **Get Current Period First**
   - Ensures at least one period exists

3. **List All Periods**
   - GET `/api/billing/periods` with user auth
   - Validate 200 response
   - Validate response structure: `{"results": [...]}`
   - Verify results is array

4. **Validate Period Responses**
   - For each period in results array:
     - Verify required fields present
     - Validate period dates (1st to last of month)
     - Check payment status valid
     - Ensure costs >= 0

5. **Verify Ordering**
   - Periods ordered by periodStart DESC (newest first)
   - If multiple periods exist, verify ordering

6. **Verify Pagination**
   - Results limited to 100 items max
   - All returned periods belong to authenticated user

7. **Validate Payment Fields**
   - Current period: paidAt null, paidAmountCents null
   - Historical periods: fields present (null or populated)
   - paymentReference field present

### Expected Results

- List retrieved successfully
- Results wrapped in `{"results": [...]}`
- Current period included in list
- Periods ordered newest first
- All fields present and valid
- All steps pass: 7/7

### Database Verification

```sql
SELECT id, user_id, is_current FROM billing_periods
WHERE user_id = $1 ORDER BY period_start DESC LIMIT 100
-- Should return current period + any historical periods
```

---

## TEST-04: Get Billing Period Details

**File**: `test-04-billing-period-details.py`
**Type**: Functional (Detail View)
**Priority**: HIGH (Required)
**Duration**: 10 minutes
**Status**: TO IMPLEMENT

### Purpose
Test GET `/api/billing/periods/{periodId}` endpoint. Verify detail view with nested request logs.

### Test Steps

1. **Setup Environment** (create user)

2. **Get Current Period ID**
   - Get current period first to have valid period ID

3. **Get Period Details**
   - GET `/api/billing/periods/{periodId}` with user auth
   - Validate 200 response
   - Validate response structure includes:
     - id, periodStart, periodEnd
     - totalRequests, totalCostCents
     - paymentStatus, current (Boolean)
     - requests (Array)

4. **Validate Request Logs Array**
   - For each request in requests array:
     - Verify fields: id, status, durationMs, flowId, result
     - All fields non-null
     - durationMs >= 0
     - status is valid (success, error, etc.)

5. **Verify Period Belongs to User**
   - Ensure period belongs to authenticated user
   - Test: Try accessing another user's period (403 Forbidden)

6. **Verify Request Log Ordering**
   - Requests ordered by timestamp DESC (newest first)
   - If multiple requests, verify ordering

7. **Verify Cost Calculation**
   - totalCostCents = totalRequests * 50
   - Formula correct for number of requests

### Expected Results

- Period details retrieved
- Request logs included (even if empty array)
- All fields present and valid
- User can only access own periods
- Cost calculation correct
- All steps pass: 7/7

### Database Verification

```sql
SELECT id, user_id, total_requests, total_cost_cents
FROM billing_periods WHERE id = $1 AND user_id = $2

SELECT COUNT(*) as req_count FROM request_logs
WHERE billing_period_id = $1
-- Verify request count matches totalRequests
```

---

## TEST-05: Get Usage Summary

**File**: `test-05-usage-summary.py`
**Type**: Functional (Analytics)
**Priority**: MEDIUM
**Duration**: 5 minutes
**Status**: TO IMPLEMENT

### Purpose
Test GET `/api/usage/summary` endpoint. Verify usage statistics calculation.

### Test Steps

1. **Setup Environment** (create user)

2. **Get Usage Summary**
   - GET `/api/usage/summary` with user auth
   - Validate 200 response
   - Validate response fields:
     - today (Integer >= 0)
     - yesterday (Integer >= 0)
     - last7Days (Integer >= 0)
     - thisMonth (Integer >= 0)
     - lastRequestAt (String ISO timestamp or null)

3. **Verify Data Types**
   - today/yesterday/last7Days/thisMonth are integers
   - lastRequestAt is ISO timestamp or null

4. **Verify Logical Consistency**
   - thisMonth >= last7Days (if last7 days is in current month)
   - yesterday can be 0 if no requests yesterday
   - All counts >= 0

5. **Handle Empty State**
   - If user has no requests:
     - All counts should be 0
     - lastRequestAt should be null

### Expected Results

- Usage summary retrieved
- All fields present and valid
- Data types correct
- Logical consistency verified
- All steps pass: 5/5

### Database Verification

```sql
SELECT COUNT(*) as today_count FROM request_logs
WHERE user_id = $1 AND request_ts >= CURRENT_DATE

SELECT COUNT(*) as week_count FROM request_logs
WHERE user_id = $1 AND request_ts >= CURRENT_DATE - INTERVAL '7 days'
```

---

## TEST-06: Admin List Billing Periods

**File**: `test-06-admin-list-periods.py`
**Type**: Functional (Admin)
**Priority**: LOW
**Duration**: 5 minutes
**Status**: TO IMPLEMENT
**Note**: Endpoint currently returns null (stub)

### Purpose
Test GET `/api/v1/admin/billing/periods` endpoint. Verify admin listing with filtering.

### Test Steps

1. **Setup Environment** (create admin and user)

2. **Attempt List Without Filtering**
   - GET `/api/v1/admin/billing/periods` with admin token
   - Currently expects null response (stub)

3. **Test Query Parameters**
   - Test with `page=0&size=20` (pagination)
   - Test with `userId={userId}` (user filtering)
   - Test with `status=pending` (status filtering)
   - Test with combined filters

4. **Verify Authentication Required**
   - GET without auth token: 401 Unauthorized
   - GET with user token (non-admin): 403 Forbidden
   - GET with admin token: 200 (or null in stub)

5. **When Implemented: Verify Response**
   - Response is Page<BillingPeriodAdminResponse>
   - Includes content, pageable metadata
   - Filtering works correctly

### Expected Results (Current - Stub)

- Endpoint returns null
- Non-admin users get 403
- Admin users can access endpoint

### Expected Results (When Implemented)

- Pagination works correctly
- Filtering by userId works
- Filtering by status works
- Combined filters work
- Response format matches Spring Page<>

---

## TEST-07: Admin Mark Period as Paid

**File**: `test-07-admin-mark-paid.py`
**Type**: Functional (Admin Write)
**Priority**: HIGH
**Duration**: 10 minutes
**Status**: TO IMPLEMENT

### Purpose
Test POST `/api/v1/admin/billing/periods/{periodId}/mark-paid` endpoint. Verify payment recording.

### Test Steps

1. **Setup Environment** (create user and get admin token)

2. **Create Test Period**
   - Get or create billing period for test

3. **Mark Period as Paid**
   - POST to `/api/v1/admin/billing/periods/{periodId}/mark-paid`
   - With admin auth token
   - Request body:
     ```json
     {
       "paidAmountCents": 5000,
       "paymentReference": "TXN-TEST-001",
       "paymentDate": "2025-01-15T14:30:00.000000Z",
       "notes": "Test payment"
     }
     ```
   - Validate 200 response

4. **Validate Response**
   - paymentStatus = "paid"
   - paidAt set to paymentDate provided
   - paidAmountCents = 5000
   - paymentReference = "TXN-TEST-001"
   - notes = "Test payment"

5. **Verify Database Update**
   - Query billing_periods
   - Verify payment_status = "paid"
   - Verify paid_at timestamp
   - Verify paid_amount_cents = 5000
   - Verify payment_reference = "TXN-TEST-001"

6. **Test Validation**
   - Missing paidAmountCents: 400 Bad Request
   - Missing paymentReference: 400 Bad Request
   - Negative paidAmountCents: 400 Bad Request
   - paymentReference > 255 chars: 400 Bad Request

7. **Test Authorization**
   - Non-admin user: 403 Forbidden
   - No auth token: 401 Unauthorized

### Expected Results

- Period marked as paid successfully
- Database updated correctly
- Validation works (rejects invalid data)
- Authorization enforced
- All steps pass: 7/7

---

## TEST-08: Admin Mark Period as Overdue

**File**: `test-08-admin-mark-overdue.py`
**Type**: Functional (Admin Write)
**Priority**: MEDIUM
**Duration**: 8 minutes
**Status**: TO IMPLEMENT

### Purpose
Test POST `/api/v1/admin/billing/periods/{periodId}/mark-overdue` endpoint. Verify overdue marking.

### Test Steps

1. **Setup Environment** (create user and get admin token)

2. **Create Test Period**
   - Get or create billing period

3. **Mark Period as Overdue**
   - POST to `/api/v1/admin/billing/periods/{periodId}/mark-overdue`
   - With admin auth token
   - Request body:
     ```json
     {
       "notes": "Payment not received after 30 days"
     }
     ```
   - Validate 200 response

4. **Validate Response**
   - paymentStatus = "overdue"
   - paidAt set to now (within 1 second)
   - paidAmountCents remains null (NOT updated)
   - paymentReference remains null (NOT updated)
   - notes = "Payment not received after 30 days"

5. **Verify Database Update**
   - payment_status = "overdue"
   - paid_at is not null (now)
   - paid_amount_cents is null (unchanged)
   - payment_reference is null (unchanged)

6. **Test Transition from Overdue to Paid**
   - Mark as overdue first
   - Then mark as paid
   - Verify status changes to paid
   - Verify paid_amount_cents updated

### Expected Results

- Period marked as overdue successfully
- Database updated correctly
- Only status and paidAt changed
- Payment fields remain null
- Transition to paid works
- All steps pass: 6/6

---

## TEST-09: Admin Mark Period as Waived

**File**: `test-09-admin-mark-waived.py`
**Type**: Functional (Admin Write)
**Priority**: MEDIUM
**Duration**: 8 minutes
**Status**: TO IMPLEMENT

### Purpose
Test POST `/api/v1/admin/billing/periods/{periodId}/mark-waived` endpoint. Verify charge forgiveness.

### Test Steps

1. **Setup Environment** (create user and get admin token)

2. **Create Test Period**
   - Get or create billing period

3. **Mark Period as Waived**
   - POST to `/api/v1/admin/billing/periods/{periodId}/mark-waived`
   - With admin auth token
   - Request body:
     ```json
     {
       "notes": "Waived due to service outage"
     }
     ```
   - Validate 200 response

4. **Validate Response**
   - paymentStatus = "waived"
   - paidAt set to now
   - paidAmountCents remains null
   - paymentReference remains null
   - notes = "Waived due to service outage"

5. **Verify Database Update**
   - payment_status = "waived"
   - paid_at is not null
   - paid_amount_cents is null
   - payment_reference is null

6. **Verify Waived is Final State**
   - Cannot transition from waived to paid
   - Cannot transition from waived to overdue
   - Waived periods are forgiven

### Expected Results

- Period marked as waived successfully
- Database updated correctly
- Waived is final state (charges forgiven)
- All steps pass: 6/6

---

## TEST-10: Billing Period Lifecycle

**File**: `test-10-billing-period-lifecycle.py`
**Type**: Integration (End-to-End)
**Priority**: HIGH
**Duration**: 20 minutes
**Status**: TO IMPLEMENT

### Purpose
Test complete billing period lifecycle: pending → overdue → paid.

### Test Steps

1. **Setup Environment** (create user and admin)

2. **Get Current Period (Initial State)**
   - GET current period
   - Verify paymentStatus = "pending"
   - Verify paidAt = null
   - Store period ID

3. **Mark as Overdue**
   - POST mark-overdue for the period
   - Verify paymentStatus = "overdue"
   - Verify paidAt is set

4. **Verify Cannot Create New Requests**
   - Current period is now overdue
   - New requests should still work (payment doesn't block API)
   - Verify new requests still log to this period

5. **Transition from Overdue to Paid**
   - POST mark-paid with payment details
   - Verify paymentStatus = "paid"
   - Verify paid_amount_cents set
   - Verify payment_reference set

6. **Verify Final State**
   - GET period details
   - Verify all payment fields populated
   - Verify status is paid

7. **Test Alternative Flow (pending → paid)**
   - Create new period
   - Mark directly as paid (skip overdue)
   - Verify transitions correctly

8. **Test Alternative Flow (pending → waived)**
   - Create new period
   - Mark as waived
   - Verify final state

### Expected Results

- All state transitions work
- Status and timestamps update correctly
- Payment information recorded accurately
- Multiple flow paths work correctly
- All steps pass: 8/8

### Payment Status Flow Verification

```
pending → overdue → paid ✓
pending → paid ✓
pending → waived ✓
overdue → paid ✓
```

---

## TEST-11: Cost Calculation Verification

**File**: `test-11-cost-calculation.py`
**Type**: Validation
**Priority**: MEDIUM
**Duration**: 10 minutes
**Status**: TO IMPLEMENT

### Purpose
Verify billing cost calculation: totalCostCents = totalRequests * 50 cents.

### Test Steps

1. **Setup Environment** (create user)

2. **Get Current Period**
   - Note initial totalRequests and totalCostCents

3. **Verify Cost Formula**
   - For each period in billing history:
     - Calculate expectedCost = totalRequests * 50
     - Verify totalCostCents == expectedCost
     - Log any discrepancies

4. **Test with Zero Requests**
   - New period with no requests
   - Verify totalRequests = 0
   - Verify totalCostCents = 0

5. **Test with Various Request Counts**
   - Query periods with different request counts
   - Verify formula for each:
     - 1 request = 50 cents
     - 10 requests = 500 cents
     - 100 requests = 5000 cents
     - 1000 requests = 50000 cents

6. **Verify Cost Consistency**
   - For same period queried multiple times:
     - Cost should be consistent
     - No cost drift or rounding errors

### Expected Results

- Cost calculation correct for all periods
- Formula: 50 cents per request
- No rounding errors
- Consistency maintained
- All steps pass: 6/6

### Database Verification

```sql
SELECT id, total_requests, total_cost_cents,
       (total_requests * 50) as expected_cost
FROM billing_periods
WHERE total_requests > 0
-- Verify total_cost_cents equals expected_cost for all rows
```

---

## Test Data Management

### Self-Contained Test Pattern

Each test follows this pattern:

```
1. Setup: Create dedicated test user with timestamp-based email
   - Email: {test-type}-{timestamp}@example.com
   - Ensures no conflicts between test runs

2. Execute: Perform test operations
   - All operations use self-created data
   - No shared state with other tests

3. Cleanup: Remove all test data
   - Delete test user (optional, tests don't delete by design)
   - Clear stored tokens
   - Leave database clean for next run
```

### Data Storage

- **Location**: `/tmp/uat-billing-test-data/`
- **Files**:
  - `billing_data.json` - Shared test data (periods, responses)
  - `admin_token.txt` - Admin authentication token (within test)
  - `user_credentials.txt` - User email/password (within test)

### No Shared Test Dependencies

- Each test can run independently
- No test data carried across tests
- Each test has complete isolation
- Can run tests in any order
- Can repeat tests without cleanup

---

## Test Execution

### Run All Tests

```bash
cd UAT/billing
uv sync
uv run python run-all-tests.py
```

### Run Required Tests Only

```bash
uv run python run-all-tests.py --required-only
```

### Run Specific Test

```bash
uv run python test-01-user-registration.py
uv run python test-02-current-billing-period.py
```

### Run with Filter

```bash
uv run python run-all-tests.py --filter admin
uv run python run-all-tests.py --filter lifecycle
```

---

## Expected Outcomes

### All Tests Pass

- Billing API fully implemented
- All endpoints functional
- Data correctly stored and retrieved
- Admin operations working
- Cost calculations accurate
- Authorization enforced

### Production Ready Checklist

- GET `/api/billing/current` - Working
- GET `/api/billing/periods` - Working
- GET `/api/billing/periods/{periodId}` - Working
- GET `/api/usage/summary` - Working
- POST mark-paid - Working
- POST mark-overdue - Working
- POST mark-waived - Working
- Cost calculation - Verified
- Authorization - Enforced
- Database integrity - Confirmed

