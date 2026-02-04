# API Reference

Complete reference for the Incoming Webhook API.

## Base URL

```
http://<your-home-assistant>:<port>
```

Default port is `8099`.

## Endpoints

### GET /

Returns server information.

**Request:**
```bash
curl http://localhost:8099/
```

**Response:**
```json
{
  "name": "Incoming Webhook Integration",
  "version": "2.0.0",
  "status": "running",
  "switches_configured": 2
}
```

---

### GET /health

Health check endpoint for monitoring.

**Request:**
```bash
curl http://localhost:8099/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

---

### POST /webhook

Control switch entities.

**Authentication:** Required (JWT Bearer token)

**Headers:**
```http
Authorization: Bearer <jwt-token>
Content-Type: application/json
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `switch_id` | string | Yes | ID of the switch (as configured) |
| `action` | string | Yes | One of: `on`, `off`, `toggle`, `status` |
| `attributes` | object | No | Key-value pairs to store with the entity |

**Example Request:**
```bash
curl -X POST http://localhost:8099/webhook \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5..." \
  -H "Content-Type: application/json" \
  -d '{
    "switch_id": "doorbell",
    "action": "on",
    "attributes": {
      "source": "api",
      "triggered_by": "john"
    }
  }'
```

**Success Response (200):**
```json
{
  "status": "success",
  "switch_id": "doorbell",
  "action": "on",
  "state": "on",
  "attributes": {
    "source": "api",
    "triggered_by": "john",
    "last_triggered_at": "2026-02-05T12:30:00+00:00"
  }
}
```

## Actions

| Action | Description |
|--------|-------------|
| `on` | Turn the switch on |
| `off` | Turn the switch off |
| `toggle` | Flip the current state |
| `status` | Get current state without changing it |

## Error Responses

### 401 Unauthorized

Missing or invalid JWT token.

```json
{
  "detail": "Invalid token"
}
```

**Common causes:**
- Token is expired
- Wrong secret was used to sign the token
- Missing `Authorization` header
- Typo in `Bearer` prefix

### 404 Not Found

Switch ID doesn't exist.

```json
{
  "detail": "Switch 'unknown_switch' not found"
}
```

**Fix:** Check that `switch_id` matches your configuration exactly (case-sensitive).

### 422 Unprocessable Entity

Invalid request format or unknown action.

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "switch_id"],
      "msg": "Field required"
    }
  ]
}
```

### 500 Internal Server Error

Something went wrong on the server side.

```json
{
  "detail": "Internal server error"
}
```

**Check Home Assistant logs for details.**

## JWT Token

Tokens must be signed with HS256 algorithm using the secret from your integration config.

**Required claims:**
- `exp` - Expiration timestamp (recommended: 1 year)

**Optional claims:**
- `iss` - Issuer (for your reference)
- Any custom claims you want

**Example token generation:**
```python
import jwt
from datetime import datetime, timedelta, timezone

token = jwt.encode(
    {
        "iss": "my-service",
        "exp": datetime.now(timezone.utc) + timedelta(days=365)
    },
    "your-secret-here",
    algorithm="HS256"
)
```

## Rate Limits

Currently no rate limiting is implemented. Consider adding your own if exposing to the internet.

## Security Notes

- Always use HTTPS when exposing to the internet (use a reverse proxy)
- Keep your JWT secret secure
- Use long expiration times for service-to-service tokens
- Rotate secrets periodically
