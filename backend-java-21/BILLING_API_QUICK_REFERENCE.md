# Billing API Quick Reference

## All Endpoints at a Glance

### User-Facing Endpoints

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/billing/current` | Get current billing period | Bearer Token |
| GET | `/api/billing/periods` | List all billing periods (100 max) | Bearer Token |
| GET | `/api/billing/periods/{periodId}` | Get period details with request logs | Bearer Token |
| GET | `/api/usage/summary` | Get usage stats (today, yesterday, etc) | Bearer Token |

### Admin Endpoints

| Method | Endpoint | Purpose | Auth | Status |
|--------|----------|---------|------|--------|
| GET | `/api/v1/admin/billing/periods` | List all periods with filters | Admin | Stub (returns null) |
| POST | `/api/v1/admin/billing/periods/{periodId}/mark-paid` | Mark period as paid | Admin | Implemented |
| POST | `/api/v1/admin/billing/periods/{periodId}/mark-overdue` | Mark period as overdue | Admin | Implemented |
| POST | `/api/v1/admin/billing/periods/{periodId}/mark-waived` | Mark period as waived/forgiven | Admin | Implemented |

---

## User Endpoints Details

### 1. GET /api/billing/current

**What it does**: Retrieves the current billing period for the logged-in user

**Key response fields**:
- `id` - Period UUID
- `isCurrent` - Always true
- `periodStart`, `periodEnd` - Calendar month dates
- `periodLabel` - "January 2025"
- `paymentStatus` - pending/paid/overdue/waived
- `totalRequests` - Number of API calls this month
- `totalCostCents` - Cost = totalRequests * 50 cents

**Notes**: 
- Automatically creates current period if doesn't exist
- Monthly billing: 1st to last day of calendar month
- Cost: 50 cents per request

---

### 2. GET /api/billing/periods

**What it does**: Lists all billing periods (up to 100)

**Response**: `{"results": [...]}`

**Each period includes**:
- All fields from current endpoint plus:
- `paidAt` - When paid (null if unpaid)
- `paidAmountCents` - Amount paid
- `paymentReference` - Transaction reference

**Notes**:
- Ordered by periodStart DESC (newest first)
- Includes all historical periods
- Wraps in `results` object

---

### 3. GET /api/billing/periods/{periodId}

**What it does**: Gets detailed billing period with all API requests

**URL Parameters**:
- `periodId` - UUID of the period

**Response includes**:
- Period info (dates, costs, status)
- Array of requests made during that period
- Each request has: id, status, durationMs, flowId, result

**Notes**:
- Only returns if period belongs to authenticated user
- All requests ordered by timestamp DESC
- Great for invoice generation or auditing

---

### 4. GET /api/usage/summary

**What it does**: Quick usage stats for different time periods

**Response fields**:
- `today` - Requests made today
- `yesterday` - Requests made yesterday
- `last7Days` - Requests in last 7 days
- `thisMonth` - Requests this calendar month
- `lastRequestAt` - ISO timestamp of most recent request

**Notes**:
- Real-time data from request logs
- Perfect for dashboard widgets
- Null lastRequestAt if no requests ever

---

## Admin Endpoints Details

### 1. GET /api/v1/admin/billing/periods

**Status**: STUB (currently returns null)

**Query Parameters**:
- `userId` (UUID, optional) - Filter by user
- `status` (String, optional) - pending/paid/overdue/waived
- `page` (int, default: 0)
- `size` (int, default: 20)

**Notes**: 
- Filtering not yet implemented
- Will support pagination when complete

---

### 2. POST /api/v1/admin/billing/periods/{periodId}/mark-paid

**What it does**: Record payment received for a billing period

**Request body**:
```json
{
  "paidAmountCents": 4500,
  "paymentReference": "TXN-2025-001",
  "paymentDate": "2025-01-15T14:30:00.000000Z",  // optional, defaults to now
  "notes": "Paid via credit card"  // optional
}
```

**Validation**:
- `paidAmountCents` >= 0 (required)
- `paymentReference` not blank, max 255 chars (required)
- `paymentDate` valid ISO timestamp (optional)

**Updates**:
- Status → paid
- Sets `paidAt` timestamp
- Records `paidAmountCents`
- Stores `paymentReference`
- Appends notes if provided

---

### 3. POST /api/v1/admin/billing/periods/{periodId}/mark-overdue

**What it does**: Mark a billing period as overdue (unpaid past due date)

**Request body**:
```json
{
  "notes": "Invoice sent, no payment after 30 days"  // optional
}
```

**Updates**:
- Status → overdue
- Sets `paidAt` to now
- Does NOT update paid amount/reference
- Appends notes if provided

**Notes**:
- Tracks accounts that haven't paid within expected timeframe
- Keep existing paid fields empty/null for overdue status

---

### 4. POST /api/v1/admin/billing/periods/{periodId}/mark-waived

**What it does**: Forgive/waive charges for a billing period

**Request body**:
```json
{
  "notes": "Waived due to service outage"  // optional
}
```

**Updates**:
- Status → waived
- Sets `paidAt` to now
- Keeps paid amount/reference null
- Appends notes if provided

**Notes**:
- Used for credits, promotions, service issues
- Charges are forgiven (no payment expected)

---

## Payment Status Lifecycle

```
PENDING (default)
  ↓
  ├→ PAID (payment received) [mark-paid]
  ├→ OVERDUE (unpaid past due) [mark-overdue]
  └→ WAIVED (charges forgiven) [mark-waived]

OVERDUE
  ↓
  └→ PAID (late payment received) [mark-paid]
```

---

## Key Business Rules

1. **One period per calendar month** - Always 1st to last day
2. **Cost calculation** - 50 cents per API request
3. **Current period** - Only ONE marked as current per user
4. **Automatic creation** - Current period created on-the-fly if missing
5. **User isolation** - Users can only view their own billing
6. **Admin-only mutations** - Only admins can mark periods paid/overdue/waived

---

## Error Status Codes

| Code | Scenario |
|------|----------|
| 200 | Success |
| 400 | Invalid request (bad amounts, missing fields) |
| 401 | Not authenticated |
| 403 | Unauthorized (non-admin accessing admin endpoint, or accessing other user's billing) |
| 404 | Period not found or doesn't belong to user |

---

## Implementation Status

### Complete (Production Ready)
- `GET /api/billing/current` ✅
- `GET /api/billing/periods` ✅
- `GET /api/billing/periods/{periodId}` ✅
- `GET /api/usage/summary` ✅
- `POST /api/v1/admin/billing/periods/{periodId}/mark-paid` ✅
- `POST /api/v1/admin/billing/periods/{periodId}/mark-overdue` ✅
- `POST /api/v1/admin/billing/periods/{periodId}/mark-waived` ✅

### Stub/Incomplete
- `GET /api/v1/admin/billing/periods` (returns null, filtering not implemented)

---

## Response Wrapping

Most responses are direct JSON objects, except:
- `GET /api/billing/periods` wraps in `{"results": [...]}`

All datetimes use ISO 8601 format with timezone.

---

## Key DTOs

1. **CurrentBillingResponse** - Current period data
2. **BillingPeriodResponse** - Period summary (list endpoint)
3. **BillingPeriodDetailDto** - Period details + request logs
4. **UsageSummaryResponse** - Quick stats
5. **BillingPeriodAdminResponse** - Admin view of period
6. **MarkPaidRequest** - Admin action payload
7. **MarkOverdueRequest** - Admin action payload
8. **MarkWaivedRequest** - Admin action payload

---

## Integration with Request Logging

Every API request automatically:
1. Creates a `RequestLog` entry
2. Associates with current billing period
3. Updates total request count
4. Recalculates period cost (requests * 50 cents)

---

## Database Indexes

```sql
INDEX idx_user_period (user_id, period_start)
INDEX idx_current_period (is_current)
```

Optimized for:
- Finding user's periods
- Finding current period quickly

