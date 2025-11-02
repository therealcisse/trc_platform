# Admin, Delete Expired Invites

- Summary: Permanently delete expired invite codes.

## Request
- Method: DELETE
- Path: /api/v1/admin/invites/expired
- Auth: Bearer token with ADMIN role
- Example:
```bash
curl -i -X DELETE \
  -H "Authorization: Bearer <admin_token>" \
  "http://localhost:8080/api/v1/admin/invites/expired"
```

## Responses
- 204 No Content
- 401 Unauthorized
- 403 Forbidden
