# Core, Test Solve

- Summary: Process an image using test pipeline for diagnostics.

## Request
- Method: POST
- Path: /api/core/test-solve
- Auth: Bearer token
- Content-Type: multipart/form-data
- Parts:
  - image (file, required)
- Example:
```bash
curl -i -X POST \
  -H "Authorization: Bearer <user_token>" \
  -H "Accept: application/json" \
  -F "image=@/path/to/image.png" \
  "http://localhost:8080/api/core/test-solve"
```

## Responses
- 200 OK, SolveResponse
- 400 Bad Request
- 401 Unauthorized
- 500 Internal Server Error
