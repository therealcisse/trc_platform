# Users, List API Tokens

- Summary: List API tokens for the authenticated user.

## Request
- Method: GET
- Path: /api/customers/tokens
- Auth: Bearer token
- Query params:
  - page (int, default 0)
  - size (int, default 20)
- Example:
```bash
curl -i \
  -H "Authorization: Bearer <user_token>" \
  -H "Accept: application/json" \
  "http://localhost:8080/api/customers/tokens?page=0&size=20"
```

## Responses
- 200 OK, Page<ApiTokenListResponse>
- 401 Unauthorized

### 200 OK
Content-Type: application/json

ApiTokenListResponse fields:
- id (UUID)
- name (string)
- createdAt (string)
- lastUsedAt (string|null)
- expiresAt (string|null)
- revokedAt (string|null)
- tokenPrefix (string)

Example body:
```json
{ "content": [ { "id": "...", "name": "CI token", "createdAt": "2025-11-01T12:00:00", "lastUsedAt": null, "expiresAt": "2026-01-01T00:00:00", "revokedAt": null, "tokenPrefix": "tok_abc" } ], "totalPages": 1, "totalElements": 1, "size": 20, "number": 0 }
```
