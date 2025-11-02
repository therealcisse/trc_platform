# Users, Verify Email

- Summary: Verify a user's email with a token.

## Request
- Method: POST
- Path: /api/auth/verify-email
- Body schema (application/json):
  - token (string)
- Example:
```bash
curl -i -X POST \
  -H "Content-Type: application/json" \
  -d '{ "token": "<verification_token>" }' \
  "http://localhost:8080/api/auth/verify-email"
```

## Responses
- 200 OK
- 400 Bad Request, invalid or expired token
