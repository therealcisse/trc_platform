# Users, Me

- Summary: Get details of the authenticated user.

## Request
- Method: GET
- Path: /api/customers/me
- Auth: Bearer token
- Example:
```bash
curl -i \
  -H "Authorization: Bearer <user_token>" \
  -H "Accept: application/json" \
  "http://localhost:8080/api/customers/me"
```

## Responses
- 200 OK, user info
- 401 Unauthorized

### 200 OK
Content-Type: application/json

Fields:
- id (UUID)
- email (string)
- isEmailVerified (boolean)
- userAcceptedTerms (boolean)
- userAcknowledgedDisclaimer (boolean)
- dateJoined (string)

Example body:
```json
{
  "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "email": "user@example.com",
  "isEmailVerified": true,
  "userAcceptedTerms": true,
  "userAcknowledgedDisclaimer": true,
  "dateJoined": "2025-10-01T09:30:00"
}
```
