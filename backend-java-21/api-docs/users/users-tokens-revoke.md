# Users, Revoke API Token

- Summary: Revoke an API token by ID.

## Request
- Method: DELETE
- Path: /api/customers/tokens/{tokenId}
- Auth: Bearer token
- Path params:
  - tokenId (UUID)
- Example:
```bash
curl -i -X DELETE \
  -H "Authorization: Bearer <user_token>" \
  "http://localhost:8080/api/customers/tokens/bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
```

## Responses
- 204 No Content
- 401 Unauthorized
- 404 Not Found
