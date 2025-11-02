# Core, Health

- Summary: Service health check.

## Request
- Method: GET
- Path: /api/core/health
- Example:
```bash
curl -i -H "Accept: application/json" "http://localhost:8080/api/core/health"
```

## Responses
- 200 OK, HealthResponse

### 200 OK
Content-Type: application/json

HealthResponse fields:
- status (string)
- checks (map<string,boolean>)

Example body:
```json
{ "status": "ok", "checks": { "database": true, "openai": true } }
```
