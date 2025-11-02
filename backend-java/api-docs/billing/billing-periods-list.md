# Billing, List Billing Periods

- Summary: List billing periods for the authenticated user.

## Request
- Method: GET
- Path: /api/billing/periods
- Auth: Bearer token
- Query params:
  - page (int, default 0)
  - size (int, default 20)
- Example:
```bash
curl -i \
  -H "Authorization: Bearer <user_token>" \
  -H "Accept: application/json" \
  "http://localhost:8080/api/billing/periods?page=0&size=20"
```

## Responses
- 200 OK, Page<BillingPeriodResponse>
- 401 Unauthorized

### 200 OK
Content-Type: application/json

BillingPeriodResponse fields:
- id (UUID)
- periodLabel (string)
- periodStart (string, yyyy-MM-dd)
- periodEnd (string, yyyy-MM-dd)
- totalRequests (int)
- totalCostCents (int)
- isCurrent (boolean)
- paymentStatus (string)
- paidAt (string, yyyy-MM-dd'T'HH:mm:ss.SSSSSS|null)
- paidAmountCents (int|null)
- paymentReference (string|null)

Example body:
```json
{ "content": [ { "id": "...", "periodLabel": "November 2025", "periodStart": "2025-11-01", "periodEnd": "2025-11-30", "totalRequests": 42, "totalCostCents": 4200, "isCurrent": true, "paymentStatus": "pending", "paidAt": null, "paidAmountCents": null, "paymentReference": null } ], "totalPages": 1, "totalElements": 1, "size": 20, "number": 0 }
```
