# Usage, List Requests

- Summary: List request logs for the authenticated user with optional date filters.

## Request
- Method: GET
- Path: /api/usage/requests
- Auth: Bearer token
- Query params:
  - from (string, ISO8601 date or datetime, optional)
  - to (string, ISO8601 date or datetime, optional)
  - page (int, default 0)
  - size (int, default 25)
- Example:
```bash
curl -i \
  -H "Authorization: Bearer <user_token>" \
  -H "Accept: application/json" \
  "http://localhost:8080/api/usage/requests?from=2025-11-01&to=2025-11-02&page=0&size=25"
```

## Responses
- 200 OK, Page<RequestLogResponse>
- 401 Unauthorized

### 200 OK
Content-Type: application/json

RequestLogResponse fields:
- id (UUID)
- requestTs (string, yyyy-MM-dd'T'HH:mm:ss)
- service (string)
- status (enum SUCCESS|ERROR)
- durationMs (int)
- requestBytes (int)
- responseBytes (int)
- requestId (UUID)
- flowId (string)
- tokenPrefix (string)

Example body:
```json
{ "content": [ { "id": "...", "requestTs": "2025-11-01T12:00:00", "service": "core.image_solve", "status": "SUCCESS", "durationMs": 1200, "requestBytes": 102400, "responseBytes": 2048, "requestId": "9f9d3a4c-8b5a-4d6e-9c2b-1a2b3c4d5e6f", "flowId": "abc-123", "tokenPrefix": "tok_abc" } ], "totalPages": 1, "totalElements": 1, "size": 25, "number": 0 }
```
