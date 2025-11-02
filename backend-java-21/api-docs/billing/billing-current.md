# Billing, Get Current Billing

- Summary: Get the current billing period for the authenticated user.

## Request
- Method: GET
- Path: /api/billing/current
- Auth: Bearer token
- Example:
```bash
curl -i \
  -H "Authorization: Bearer <user_token>" \
  -H "Accept: application/json" \
  "http://localhost:8080/api/billing/current"
```

## Responses
- 200 OK, CurrentBillingResponse
- 401 Unauthorized

### 200 OK
Content-Type: application/json

CurrentBillingResponse fields:
- id (UUID)
- isCurrent (boolean)
- periodStart (string, yyyy-MM-dd)
- periodEnd (string, yyyy-MM-dd)
- periodLabel (string)
- paymentStatus (string)
- totalRequests (int)
- totalCostCents (int)

Example body:
```json
{
  "id": "c1a2b3c4-d5e6-7890-ab12-cd34ef56ab78",
  "isCurrent": true,
  "periodStart": "2025-11-01",
  "periodEnd": "2025-11-30",
  "periodLabel": "November 2025",
  "paymentStatus": "pending",
  "totalRequests": 42,
  "totalCostCents": 4200
}
```
