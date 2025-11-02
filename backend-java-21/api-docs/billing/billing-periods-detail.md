# Billing, Get Billing Period Detail

- Summary: Get detailed information for a billing period.

## Request
- Method: GET
- Path: /api/billing/periods/{periodId}
- Auth: Bearer token
- Path params:
  - periodId (UUID)
- Example:
```bash
curl -i \
  -H "Authorization: Bearer <user_token>" \
  -H "Accept: application/json" \
  "http://localhost:8080/api/billing/periods/c1a2b3c4-d5e6-7890-ab12-cd34ef56ab78"
```

## Responses
- 200 OK, BillingPeriodDetailDto
- 401 Unauthorized
- 404 Not Found

### 200 OK
Content-Type: application/json

BillingPeriodDetailDto fields:
- id (UUID)
- periodStart (string, yyyy-MM-dd)
- periodEnd (string, yyyy-MM-dd)
- totalRequests (int)
- totalCostCents (int)
- paymentStatus (enum)
- current (boolean)
- requests (array of RequestLogDto)

RequestLogDto:
- id (UUID)
- status (string)
- durationMs (int)
- flowId (string)
- result (string)

Example body:
```json
{
  "id": "c1a2b3c4-d5e6-7890-ab12-cd34ef56ab78",
  "periodStart": "2025-11-01",
  "periodEnd": "2025-11-30",
  "totalRequests": 2,
  "totalCostCents": 200,
  "paymentStatus": "pending",
  "current": true,
  "requests": [
    { "id": "...", "status": "SUCCESS", "durationMs": 1234, "flowId": "flow-1", "result": "x=1" }
  ]
}
```
