# Core, Solve

- Summary: Process an image to solve a math problem.

## Request
- Method: POST
- Path: /api/core/solve
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
  "http://localhost:8080/api/core/solve"
```

## Responses
- 200 OK, SolveResponse
- 400 Bad Request
- 401 Unauthorized
- 500 Internal Server Error

### 200 OK
Content-Type: application/json

SolveResponse fields:
- requestId (string, UUID)
- result (string)
- durationMs (int)
- timings (map<string,int>)

Example body:
```json
{
  "requestId": "9f9d3a4c-8b5a-4d6e-9c2b-1a2b3c4d5e6f",
  "result": "x = 42",
  "durationMs": 1234,
  "timings": { "upload": 50, "inference": 1100 }
}
```
