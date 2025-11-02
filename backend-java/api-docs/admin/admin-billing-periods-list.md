# Admin, List Billing Periods

- Summary: List billing periods filtered by user and payment status.

## Request
- Method: GET
- Path: /api/v1/admin/billing/periods
- Auth: Bearer token with ADMIN role
- Query params:
  - userId (UUID, optional)
  - status (enum: pending, paid, overdue, waived, optional)
  - page (int, default 0)
  - size (int, default 20)
- Example:
```bash
curl -i \
  -H "Authorization: Bearer <admin_token>" \
  -H "Accept: application/json" \
  "http://localhost:8080/api/v1/admin/billing/periods?userId=3b4a2f1e-0a3f-4c8c-9b5f-1f2e3d4c5b6a&status=pending&page=0&size=20"
```

## Responses
- 200 OK, paged list of BillingPeriodAdminResponse
- 400 Bad Request, invalid query
- 401 Unauthorized, missing or invalid token
- 403 Forbidden, not admin
- 500 Internal Server Error

### 200 OK
Content-Type: application/json

Data shape (Spring Page):
- content: BillingPeriodAdminResponse[]
- pageable, totalPages, totalElements, size, number, sort, first, last, numberOfElements, empty

BillingPeriodAdminResponse:
- id (UUID)
- userId (UUID)
- paymentStatus (enum)
- current (boolean)
- totalRequests (int)
- totalCostCents (int)
- paidAt (string, yyyy-MM-dd'T'HH:mm:ss.SSSSSS)
- paidAmountCents (int)
- paymentReference (string)
- notes (string)

Example body:
```json
{
  "content": [
    {
      "id": "c1a2b3c4-d5e6-7890-ab12-cd34ef56ab78",
      "userId": "3b4a2f1e-0a3f-4c8c-9b5f-1f2e3d4c5b6a",
      "paymentStatus": "pending",
      "current": true,
      "totalRequests": 42,
      "totalCostCents": 4200,
      "paidAt": null,
      "paidAmountCents": null,
      "paymentReference": null,
      "notes": null
    }
  ],
  "pageable": { "sort": { "sorted": false, "unsorted": true, "empty": true }, "offset": 0, "pageNumber": 0, "pageSize": 20, "paged": true, "unpaged": false },
  "totalPages": 1,
  "totalElements": 1,
  "last": true,
  "size": 20,
  "number": 0,
  "sort": { "sorted": false, "unsorted": true, "empty": true },
  "numberOfElements": 1,
  "first": true,
  "empty": false
}
```

Example curl response headers:
```
HTTP/1.1 200 OK
Content-Type: application/json
```
