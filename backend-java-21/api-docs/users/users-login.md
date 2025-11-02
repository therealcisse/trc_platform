# Users, Login

- Summary: Authenticate a user and obtain a session token.

## Request
- Method: POST
- Path: /api/customers/login
- Body schema (application/json):
  - email (string, email)
  - password (string, 8-128 chars)
- Example:
```bash
curl -i -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{ "email": "user@example.com", "password": "user12345" }' \
  "http://localhost:8080/api/customers/login"
```

## Responses
- 200 OK, login payload
- 400 Bad Request, invalid credentials

### 200 OK
Content-Type: application/json

Example body:
```json
{ "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "email": "user@example.com", "token": "<jwt>" }
```
