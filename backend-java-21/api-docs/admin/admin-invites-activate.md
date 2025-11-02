# Admin, Activate Invite Code

- Summary: Activate an invite code.

## Request
- Method: POST
- Path: /api/v1/admin/invites/{code}/activate
- Auth: Bearer token with ADMIN role
- Path params:
  - code (string)
- Example:
```bash
curl -i -X POST \
  -H "Authorization: Bearer <admin_token>" \
  -H "Accept: application/json" \
  "http://localhost:8080/api/v1/admin/invites/WELCOME123/activate"
```

## Responses
- 200 OK, InviteCodeResponse
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found

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
