# Users, Register

- Summary: Register a new user account with invite code and terms acceptance.

## Request
- Method: POST
- Path: /api/customers/register
- Body schema (application/json):
  - email (string, email)
  - password (string, 8-128)
  - confirmPassword (string, must match password)
  - inviteCode (string, max 32)
  - userAcceptedTerms (boolean)
  - userAcknowledgedDisclaimer (boolean)
- Example:
```bash
curl -i -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "user12345",
    "confirmPassword": "user12345",
    "inviteCode": "WELCOME123",
    "userAcceptedTerms": true,
    "userAcknowledgedDisclaimer": true
  }' \
  "http://localhost:8080/api/customers/register"
```

## Responses
- 202 Accepted, registration queued and verification email sent
- 400 Bad Request, validation or invite code errors

### 202 Accepted
No body
