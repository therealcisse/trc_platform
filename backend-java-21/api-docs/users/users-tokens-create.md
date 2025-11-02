# Users, Create API Token

- Summary: Create a new API token for the authenticated user.

## Request
- Method: POST
- Path: /api/customers/tokens
- Auth: Bearer token
- Body schema (application/json):
  - name (string, 1-100)
  - expiresAt (string, ISO datetime, optional)
- Example:
```bash
curl -i -X POST \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{ "name": "CI token", "expiresAt": "2026-01-01T00:00:00" }' \
  "http://localhost:8080/api/customers/tokens"
```

## Responses
- 201 Created, ApiTokenResponse
- 401 Unauthorized
- 400 Bad Request

### 201 Created
Content-Type: application/json

ApiTokenResponse fields:
- id (UUID)
- token (string, present only on creation)
- name (string)
- createdAt (string)
- lastUsedAt (string|null)
- expiresAt (string|null)
- revokedAt (string|null)
- tokenPrefix (string)

Example body:
```json
{
  "id": "bbbbbbbb-cccc-dddd-eeee-ffffffffffff",
  "token": "tok_XXXXXXXXXXXXXXXX",
  "name": "CI token",
  "createdAt": "2025-11-01T12:00:00",
  "lastUsedAt": null,
  "expiresAt": "2026-01-01T00:00:00",
  "revokedAt": null,
  "tokenPrefix": "tok_abc"
}
```
