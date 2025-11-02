# Admin, Deactivate Invite Code

- Summary: Deactivate an invite code.

## Request
- Method: POST
- Path: /api/v1/admin/invites/{code}/deactivate
- Auth: Bearer token with ADMIN role
- Path params:
  - code (string)
- Example:
```bash
curl -i -X POST \
  -H "Authorization: Bearer <admin_token>" \
  -H "Accept: application/json" \
  "http://localhost:8080/api/v1/admin/invites/WELCOME123/deactivate"
```

## Responses
- 200 OK, InviteCodeResponse
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found
