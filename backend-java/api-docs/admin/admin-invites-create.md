# Admin, Create Invite Code

- Summary: Create a new invite code, optionally with expiration.

## Request
- Method: POST
- Path: /api/v1/admin/invites
- Auth: Bearer token with ADMIN role
- Body schema (application/json):
  - code (string, 6-32 chars)
  - expiresAt (string, future, yyyy-MM-dd'T'HH:mm:ss, optional)
- Example:
```bash
curl -i -X POST \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{ "code": "WELCOME123", "expiresAt": "2025-12-01T00:00:00" }' \
  "http://localhost:8080/api/v1/admin/invites"
```

## Responses
- 200 OK, InviteCodeResponse
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden

### 200 OK
Content-Type: application/json

Example body:
```json
{
  "id": "11111111-2222-3333-4444-555555555555",
  "code": "WELCOME123",
  "active": true,
  "createdAt": "2025-11-01T10:00:00",
  "expiresAt": "2025-12-01T00:00:00",
  "usedAt": null,
  "usedByUserId": null,
  "createdByUserId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "createdByUserEmail": "admin@example.com"
}
```
