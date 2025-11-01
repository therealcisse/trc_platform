# Billing API Endpoints Documentation

## Overview

The Billing API provides comprehensive billing and usage tracking functionality for the TRC Platform. It includes user-facing endpoints for viewing billing information and admin endpoints for managing billing periods and payment statuses.

---

## User-Facing Endpoints (Requires Authentication)

Base Path: `/api`

### 1. Get Current Billing Period

**Endpoint**: `GET /billing/current`

**Authentication**: Bearer JWT Token (User)

**Purpose**: Retrieve the current billing period information for the authenticated user.

**Response**: `CurrentBillingResponse`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "isCurrent": true,
  "periodStart": "2025-01-01",
  "periodEnd": "2025-01-31",
  "periodLabel": "January 2025",
  "paymentStatus": "pending",
  "totalRequests": 90,
  "totalCostCents": 4500
}
```

**Response Fields**:
- `id` (UUID) - Unique identifier for the billing period
- `isCurrent` (Boolean) - Whether this is the current active billing period
- `periodStart` (Date) - Start date of the billing period (first day of month)
- `periodEnd` (Date) - End date of the billing period (last day of month)
- `periodLabel` (String) - Human-readable period label (e.g., "January 2025")
- `paymentStatus` (String) - Current payment status (pending, paid, overdue, waived)
- `totalRequests` (Integer) - Total API requests made in this period
- `totalCostCents` (Integer) - Total cost in cents (calculated as totalRequests * 50 cents per request)

**Business Logic**:
- Automatically creates a new billing period if the current one doesn't exist
- Returns the current month's billing period
- If current period doesn't exist, creates it on-the-fly
- Monthly periods: 1st to last day of each month
- Cost calculation: 50 cents per API request

---

### 2. List All Billing Periods

**Endpoint**: `GET /billing/periods`

**Authentication**: Bearer JWT Token (User)

**Purpose**: Retrieve a list of all billing periods for the authenticated user (up to 100 most recent).

**Response**: 
```json
{
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "periodLabel": "January 2025",
      "periodStart": "2025-01-01",
      "periodEnd": "2025-01-31",
      "totalRequests": 90,
      "totalCostCents": 4500,
      "isCurrent": true,
      "paymentStatus": "pending",
      "paidAt": null,
      "paidAmountCents": null,
      "paymentReference": null
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "periodLabel": "December 2024",
      "periodStart": "2024-12-01",
      "periodEnd": "2024-12-31",
      "totalRequests": 150,
      "totalCostCents": 7500,
      "isCurrent": false,
      "paymentStatus": "paid",
      "paidAt": "2025-01-05T14:30:00.000000Z",
      "paidAmountCents": 7500,
      "paymentReference": "INV-2024-12-001"
    }
  ]
}
```

**Response Fields** (array of `BillingPeriodResponse`):
- `id` (UUID) - Unique identifier for the billing period
- `periodLabel` (String) - Human-readable label (e.g., "January 2025")
- `periodStart` (Date) - First day of the billing period
- `periodEnd` (Date) - Last day of the billing period
- `totalRequests` (Integer) - Total API requests in this period
- `totalCostCents` (Integer) - Total cost in cents
- `isCurrent` (Boolean) - Whether this is the active billing period
- `paymentStatus` (String) - Payment status (pending, paid, overdue, waived)
- `paidAt` (DateTime) - When the period was marked as paid (null if unpaid)
- `paidAmountCents` (Integer) - Amount actually paid in cents (null if unpaid)
- `paymentReference` (String) - Reference number from payment processor (null if unpaid)

**Business Logic**:
- Returns up to 100 most recent periods (ordered by periodStart DESC)
- Includes both current and historical periods
- Useful for viewing billing history

---

### 3. Get Billing Period Details

**Endpoint**: `GET /billing/periods/{periodId}`

**Authentication**: Bearer JWT Token (User)

**Path Parameters**:
- `periodId` (UUID) - The billing period ID to retrieve details for

**Purpose**: Retrieve detailed information about a specific billing period, including all requests made during that period.

**Response**: `BillingPeriodDetailDto`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "periodStart": "2025-01-01",
  "periodEnd": "2025-01-31",
  "totalRequests": 90,
  "totalCostCents": 4500,
  "paymentStatus": "pending",
  "current": true,
  "requests": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440100",
      "status": "success",
      "durationMs": 450,
      "flowId": "flow-123-abc",
      "result": "solved"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440101",
      "status": "error",
      "durationMs": 320,
      "flowId": "flow-456-def",
      "result": "invalid_image"
    }
  ]
}
```

**Response Fields**:
- `id` (UUID) - Billing period identifier
- `periodStart` (Date) - First day of period
- `periodEnd` (Date) - Last day of period
- `totalRequests` (Integer) - Total requests in period
- `totalCostCents` (Integer) - Total cost
- `paymentStatus` (String) - Payment status
- `current` (Boolean) - Is this the current billing period
- `requests` (Array) - List of all API requests made during this period
  - `id` (UUID) - Request log ID
  - `status` (String) - Request status (success, error, etc.)
  - `durationMs` (Integer) - Request processing time in milliseconds
  - `flowId` (String) - Unique identifier for the request flow/session
  - `result` (String) - Result of the request (solved, invalid_image, timeout, etc.)

**Business Logic**:
- Only returns details for billing periods belonging to the authenticated user
- Throws `IllegalArgumentException` if period not found or doesn't belong to user
- Returns all requests associated with the period, ordered by timestamp DESC
- Useful for invoice generation and detailed auditing

---

### 4. Get Usage Summary

**Endpoint**: `GET /usage/summary`

**Authentication**: Bearer JWT Token (User)

**Purpose**: Retrieve quick usage statistics for various time periods (today, yesterday, last 7 days, this month).

**Response**: `UsageSummaryResponse`

```json
{
  "today": 25,
  "yesterday": 18,
  "last7Days": 142,
  "thisMonth": 450,
  "lastRequestAt": "2025-01-15T14:32:45.123456Z"
}
```

**Response Fields**:
- `today` (Integer) - Number of API requests made today
- `yesterday` (Integer) - Number of API requests made yesterday
- `last7Days` (Integer) - Number of requests in the last 7 days (including today)
- `thisMonth` (Integer) - Number of requests made in the current calendar month
- `lastRequestAt` (String) - ISO timestamp of the most recent request (null if no requests)

**Business Logic**:
- Calculates from request logs in the database
- Time periods:
  - Today: from 00:00:00 to now
  - Yesterday: from yesterday 00:00:00 to today 00:00:00
  - Last 7 days: from 7 days ago to now (includes today)
  - This month: from 1st of current month to now
- Queries directly from request log table for real-time data
- Useful for dashboard widgets and usage alerts

---

## Admin Endpoints (Requires Admin Role)

Base Path: `/api/v1/admin/billing/periods`

All admin endpoints require the `ADMIN` role and are protected with `@PreAuthorize("hasRole('ADMIN')")`.

### 1. List Billing Periods (Admin)

**Endpoint**: `GET /api/v1/admin/billing/periods`

**Authentication**: Bearer JWT Token (Admin User)

**Query Parameters**:
- `userId` (UUID, optional) - Filter by specific user
- `status` (String, optional) - Filter by payment status (pending, paid, overdue, waived)
- `page` (Integer, default: 0) - Zero-based page number for pagination
- `size` (Integer, default: 20) - Number of results per page

**Purpose**: List all billing periods across all users with optional filtering and pagination.

**Response**: Paginated `Page<BillingPeriodAdminResponse>`

```json
{
  "content": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "userId": "550e8400-e29b-41d4-a716-446655440010",
      "paymentStatus": "pending",
      "current": true,
      "totalRequests": 90,
      "totalCostCents": 4500,
      "paidAt": null,
      "paidAmountCents": null,
      "paymentReference": null,
      "notes": null
    }
  ],
  "pageable": {
    "pageNumber": 0,
    "pageSize": 20,
    "totalElements": 150,
    "totalPages": 8
  }
}
```

**Response Fields** (array of `BillingPeriodAdminResponse`):
- `id` (UUID) - Billing period ID
- `userId` (UUID) - User who owns this billing period
- `paymentStatus` (String) - Payment status
- `current` (Boolean) - Is this the current period
- `totalRequests` (Integer) - Total requests
- `totalCostCents` (Integer) - Total cost
- `paidAt` (DateTime) - When marked as paid
- `paidAmountCents` (Integer) - Amount paid
- `paymentReference` (String) - Payment reference
- `notes` (String) - Admin notes about this period

**Business Logic**:
- Currently returns null (implementation incomplete)
- Intended to support filtering by user and payment status
- Future implementation should use Spring Data specifications for filtering

---

### 2. Mark Billing Period as Paid

**Endpoint**: `POST /api/v1/admin/billing/periods/{periodId}/mark-paid`

**Authentication**: Bearer JWT Token (Admin User)

**Path Parameters**:
- `periodId` (UUID) - The billing period to mark as paid

**Request Body**: `MarkPaidRequest`

```json
{
  "paidAmountCents": 4500,
  "paymentReference": "TXN-2025-001",
  "paymentDate": "2025-01-15T14:30:00.000000Z",
  "notes": "Paid via credit card"
}
```

**Request Fields**:
- `paidAmountCents` (Integer, required) - Amount paid in cents (must be >= 0)
- `paymentReference` (String, required) - Payment reference number (max 255 chars)
- `paymentDate` (DateTime, optional) - Date of payment (defaults to now if not provided)
- `notes` (String, optional) - Admin notes about the payment

**Response**: `BillingPeriodAdminResponse`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "550e8400-e29b-41d4-a716-446655440010",
  "paymentStatus": "paid",
  "current": true,
  "totalRequests": 90,
  "totalCostCents": 4500,
  "paidAt": "2025-01-15T14:30:00.000000Z",
  "paidAmountCents": 4500,
  "paymentReference": "TXN-2025-001",
  "notes": "Paid via credit card"
}
```

**Validation**:
- `paidAmountCents` must be >= 0
- `paymentReference` must not be blank and max 255 characters
- `paymentDate` must be valid ISO timestamp format

**Business Logic**:
- Changes payment status to `paid`
- Sets `paidAt` to provided paymentDate or current timestamp if not provided
- Updates `paidAmountCents` with the amount paid
- Updates `paymentReference` with the transaction reference
- Appends notes if provided
- Throws `IllegalArgumentException` if billing period not found
- Uses @Transactional to ensure atomic updates

---

### 3. Mark Billing Period as Overdue

**Endpoint**: `POST /api/v1/admin/billing/periods/{periodId}/mark-overdue`

**Authentication**: Bearer JWT Token (Admin User)

**Path Parameters**:
- `periodId` (UUID) - The billing period to mark as overdue

**Request Body**: `MarkOverdueRequest`

```json
{
  "notes": "Invoice sent, no payment received after 30 days"
}
```

**Request Fields**:
- `notes` (String, optional) - Admin notes about the overdue status

**Response**: `BillingPeriodAdminResponse`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "550e8400-e29b-41d4-a716-446655440010",
  "paymentStatus": "overdue",
  "current": false,
  "totalRequests": 90,
  "totalCostCents": 4500,
  "paidAt": "2025-01-15T14:30:00.000000Z",
  "paidAmountCents": null,
  "paymentReference": null,
  "notes": "Invoice sent, no payment received after 30 days"
}
```

**Business Logic**:
- Changes payment status to `overdue`
- Sets `paidAt` to current timestamp (note: this is different from the "paid" endpoint)
- Does NOT modify `paidAmountCents` or `paymentReference`
- Used to track accounts that have not paid within expected timeframe
- Throws `IllegalArgumentException` if billing period not found

---

### 4. Mark Billing Period as Waived

**Endpoint**: `POST /api/v1/admin/billing/periods/{periodId}/mark-waived`

**Authentication**: Bearer JWT Token (Admin User)

**Path Parameters**:
- `periodId` (UUID) - The billing period to mark as waived

**Request Body**: `MarkWaivedRequest`

```json
{
  "notes": "Waived due to service issues during this period"
}
```

**Request Fields**:
- `notes` (String, optional) - Reason for waiving the charge

**Response**: `BillingPeriodAdminResponse`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "550e8400-e29b-41d4-a716-446655440010",
  "paymentStatus": "waived",
  "current": false,
  "totalRequests": 90,
  "totalCostCents": 4500,
  "paidAt": "2025-01-15T14:30:00.000000Z",
  "paidAmountCents": null,
  "paymentReference": null,
  "notes": "Waived due to service issues during this period"
}
```

**Business Logic**:
- Changes payment status to `waived`
- Sets `paidAt` to current timestamp
- Does NOT modify payment amount or reference (remains null)
- Used when a billing period is forgiven (e.g., due to service outages, credits, promotions)
- Throws `IllegalArgumentException` if billing period not found

---

## Data Models

### BillingPeriod Entity

```java
@Entity
@Table(name = "billing_periods")
public class BillingPeriod {
    
    public enum PaymentStatus {
        pending,    // Invoice created but not yet paid
        paid,       // Payment received
        overdue,    // Payment due date passed, not paid
        waived      // Charges waived/forgiven
    }
    
    private UUID id;                          // Unique identifier
    private User user;                        // User who owns this period
    private LocalDate periodStart;            // First day of billing period
    private LocalDate periodEnd;              // Last day of billing period
    private Integer totalRequests = 0;        // Count of API requests
    private Integer totalCostCents = 0;       // Total cost (requests * 50 cents)
    private Boolean current = false;          // Is this the active period
    private PaymentStatus paymentStatus;      // Current payment status
    private LocalDateTime paidAt;             // When payment was received/processed
    private Integer paidAmountCents;          // Amount paid in cents
    private String paymentReference;          // Reference from payment processor
    private String notes;                     // Admin notes
    private Long version;                     // Optimistic lock version
    private Set<RequestLog> requests;         // Associated API request logs
}
```

### Payment Status Flow

```
pending → paid (successful payment)
pending → overdue (past due date, unpaid)
pending/overdue → waived (charges forgiven)
paid → (final state)
waived → (final state)
overdue → paid (payment received after overdue)
```

---

## Business Logic Summary

### Cost Calculation
- **Per-request cost**: 50 cents (0.50 USD)
- **Total cost formula**: `totalRequests * 50` (in cents)
- Updated via `updateBillingPeriodCosts()` method

### Billing Period Lifecycle

1. **Creation**: Automatic, one per calendar month (1st to last day)
2. **Current Status**: Only one billing period per user marked as `current = true`
3. **Request Logging**: Each API request logs to the current billing period
4. **Cost Update**: Costs recalculated when requests are added
5. **Payment Processing**: Admin marks period as paid/overdue/waived
6. **Archival**: Previous periods become read-only records

### Monthly Period Assignment
- Periods automatically span from 1st to last day of each month
- Always based on calendar month in Berlin timezone
- New period created automatically when users authenticate in a new month

---

## Error Handling

### Common Error Responses

**404 - Billing Period Not Found**
```
Status: 404
Message: "Billing period not found"
```

**401 - Unauthorized**
```
Status: 401
Message: "Authentication required"
```

**403 - Forbidden (User accessing another user's billing data)**
```
Status: 403
Message: "Access denied"
```

**400 - Bad Request (Admin endpoints with invalid input)**
```
Status: 400
Message: "Paid amount must be non-negative"
         "Payment reference is required"
         "Payment reference must not exceed 255 characters"
```

---

## Database Schema

```sql
CREATE TABLE billing_periods (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_requests INTEGER NOT NULL DEFAULT 0,
    total_cost_cents INTEGER NOT NULL DEFAULT 0,
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    payment_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    paid_at TIMESTAMP NULL,
    paid_amount_cents INTEGER NULL,
    payment_reference VARCHAR(255) NULL,
    notes TEXT NULL,
    version BIGINT,
    INDEX idx_user_period (user_id, period_start),
    INDEX idx_current_period (is_current)
);

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

---

## Integration Points

### With Request Logging System
- Every API request is logged to `RequestLog` table
- RequestLog references the current billing period
- Costs are calculated from RequestLog count

### With User Authentication
- Billing periods are user-specific
- Authentication context used to filter data
- Admin role required for management endpoints

### With Berlin Time Zone
- All periods based on calendar month in Berlin timezone
- Configuration in Django backend: `TIME_ZONE = 'Europe/Berlin'`
- Should match in Spring implementation

