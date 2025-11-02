# Admin, Mark Billing Period Waived

- Summary: Mark a billing period as waived with optional notes.

## Request
- Method: POST
- Path: /api/v1/admin/billing/periods/{periodId}/mark-waived
- Auth: Bearer token with ADMIN role
- Path params:
  - periodId (UUID)
- Body schema (application/json):
  - notes (string, optional)
- Example:
```bash
curl -i -X POST \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{ "notes": "Courtesy credit" }' \
  "http://localhost:8080/api/v1/admin/billing/periods/c1a2b3c4-d5e6-7890-ab12-cd34ef56ab78/mark-waived"
```

## Responses
- 200 OK, BillingPeriodAdminResponse
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found
- 500 Internal Server Error

### 200 OK
Content-Type: application/json

Example body:
```json
{
  "id": "c1a2b3c4-d5e6-7890-ab12-cd34ef56ab78",
  "userId": "3b4a2f1e-0a3f-4c8c-9b5f-1f2e3d4c5b6a",
  "paymentStatus": "waived",
  "current": true,
  "totalRequests": 42,
  "totalCostCents": 4200,
  "paidAt": null,
  "paidAmountCents": null,
  "paymentReference": null,
  "notes": "Courtesy credit"
}
```

Example curl response headers:
```
HTTP/1.1 200 OK
Content-Type: application/json
```
