# Usage, Summary

- Summary: Get usage summary metrics for the authenticated user.

## Request
- Method: GET
- Path: /api/usage/summary
- Auth: Bearer token
- Example:
```bash
curl -i \
  -H "Authorization: Bearer <user_token>" \
  -H "Accept: application/json" \
  "http://localhost:8080/api/usage/summary"
```

## Responses
- 200 OK, UsageSummaryResponse
- 401 Unauthorized

### 200 OK
Content-Type: application/json

UsageSummaryResponse fields:
- today (int)
- yesterday (int)
- last7Days (int)
- thisMonth (int)
- lastRequestAt (string|null)

Example body:
```json
{ "today": 3, "yesterday": 5, "last7Days": 22, "thisMonth": 50, "lastRequestAt": "2025-11-01T12:34:56" }
```
