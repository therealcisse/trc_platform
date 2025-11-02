# Users, Resend Verification Email

- Summary: Resend the email verification message.

## Request
- Method: POST
- Path: /api/auth/resend-verification
- Body schema (application/json):
  - email (string, email)
- Example:
```bash
curl -i -X POST \
  -H "Content-Type: application/json" \
  -d '{ "email": "user@example.com" }' \
  "http://localhost:8080/api/auth/resend-verification"
```

## Responses
- 200 OK
- 400 Bad Request, already verified or invalid email
