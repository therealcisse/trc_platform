# Admin, Mark Billing Period Paid

- Summary: Mark a billing period as paid with amount and reference.

## Request
- Method: POST
- Path: /api/v1/admin/billing/periods/{periodId}/mark-paid
- Auth: Bearer token with ADMIN role
- Path params:
  - periodId (UUID)
- Body schema (application/json):
  - paidAmountCents (int, required, >= 0)
  - paymentReference (string, required, max 255)
  - paymentDate (string, yyyy-MM-dd'T'HH:mm:ss.SSSSSSXXX, optional)
  - notes (string, optional)
- Example:
```bash
curl -i -X POST \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "paidAmountCents": 4200,
    "paymentReference": "INV-2025-0001",
    "paymentDate": "2025-11-01T12:00:00.000000+01:00",
    "notes": "Manual settlement"
  }' \
  "http://localhost:8080/api/v1/admin/billing/periods/c1a2b3c4-d5e6-7890-ab12-cd34ef56ab78/mark-paid"
```

## Responses
- 200 OK, BillingPeriodAdminResponse
- 400 Bad Request, validation error
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found, period missing
- 500 Internal Server Error

### 200 OK
Content-Type: application/json

BillingPeriodAdminResponse fields:
- id (UUID)
- userId (UUID)
- paymentStatus (enum)
- current (boolean)
- totalRequests (int)
- totalCostCents (int)
- paidAt (string)
- paidAmountCents (int)
- paymentReference (string)
- notes (string)

Example body:
```json
{
  "id": "c1a2b3c4-d5e6-7890-ab12-cd34ef56ab78",
  "userId": "3b4a2f1e-0a3f-4c8c-9b5f-1f2e3d4c5b6a",
  "paymentStatus": "paid",
  "current": false,
  "totalRequests": 42,
  "totalCostCents": 4200,
  "paidAt": "2025-11-01T12:00:00.000000",
  "paidAmountCents": 4200,
  "paymentReference": "INV-2025-0001",
  "notes": "Manual settlement"
}
```

Example curl response headers:
```
HTTP/1.1 200 OK
Content-Type: application/json
```
