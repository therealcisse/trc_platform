# Admin, List Invite Codes

- Summary: List invite codes with pagination.

## Request
- Method: GET
- Path: /api/v1/admin/invites
- Auth: Bearer token with ADMIN role
- Query params:
  - page (int, default 0)
  - size (int, default 20)
- Example:
```bash
curl -i \
  -H "Authorization: Bearer <admin_token>" \
  -H "Accept: application/json" \
  "http://localhost:8080/api/v1/admin/invites?page=0&size=20"
```

## Responses
- 200 OK, Page<InviteCodeResponse>
- 401 Unauthorized
- 403 Forbidden

### 200 OK
Content-Type: application/json

InviteCodeResponse fields:
- id (UUID)
- code (string)
- active (boolean)
- createdAt (string)
- expiresAt (string)
- usedAt (string|null)
- usedByUserId (UUID|null)
- createdByUserId (UUID)
- createdByUserEmail (string)

Example body:
```json
{
  "content": [
    {
      "id": "11111111-2222-3333-4444-555555555555",
      "code": "WELCOME123",
      "active": true,
      "createdAt": "2025-11-01T10:00:00",
      "expiresAt": "2025-12-01T00:00:00",
      "usedAt": null,
      "usedByUserId": null,
      "createdByUserId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
      "createdByUserEmail": "admin@example.com"
    }
  ],
  "pageable": { "pageNumber": 0, "pageSize": 20 },
  "totalPages": 1,
  "totalElements": 1,
  "size": 20,
  "number": 0,
  "numberOfElements": 1,
  "first": true,
  "last": true,
  "empty": false
}
```
