# Users, Change Password

- Summary: Change the authenticated user's password.

## Request
- Method: POST
- Path: /api/auth/password/change
- Auth: Bearer token
- Body schema (application/json):
  - currentPassword (string)
  - newPassword (string, 8-128, must include uppercase, lowercase, digit, special)
  - confirmPassword (string, must match newPassword)
- Example:
```bash
curl -i -X POST \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -d '{ "currentPassword": "oldPass1!", "newPassword": "NewPass1!", "confirmPassword": "NewPass1!" }' \
  "http://localhost:8080/api/auth/password/change"
```

## Responses
- 200 OK
- 401 Unauthorized
- 400 Bad Request, validation failures
