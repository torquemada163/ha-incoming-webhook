# Incoming Webhook

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/torquemada163/ha-incoming-webhook.svg)](https://github.com/torquemada163/ha-incoming-webhook/releases)

A Home Assistant integration that lets you control switch entities via a secure webhook API. Perfect for connecting external services like Telegram bots, IFTTT, or custom scripts to your smart home.

## Features

- **JWT Authentication** - Secure access with industry-standard tokens
- **Multiple Actions** - Turn on, turn off, toggle, or check status
- **Automatic Entity Creation** - Just configure and go, no manual setup
- **Custom Attributes** - Attach metadata to track who triggered what
- **State Persistence** - Survives restarts without losing state
- **Universal Compatibility** - Works on any Home Assistant installation

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant
2. Go to **Integrations**
3. Click the three dots menu → **Custom repositories**
4. Add `https://github.com/torquemada163/ha-incoming-webhook` as an Integration
5. Search for "Incoming Webhook" and install it
6. Restart Home Assistant

### Manual

Copy the `custom_components/incoming_webhook` folder to your `config/custom_components/` directory and restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & Services → Integrations**
2. Click **Add Integration** and search for "Incoming Webhook"
3. Enter your settings:
   - **JWT Secret** - At least 32 characters, keep it safe
   - **Port** - Default is 8099
   - **Switches** - Define each switch with an ID, name, and icon
4. Your switches will appear as `switch.webhook_<id>`

## API Reference

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server info and status |
| `/health` | GET | Health check |
| `/webhook` | POST | Control switches |

### Authentication

All requests to `/webhook` require a JWT token:

```http
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

### Webhook Request

```json
{
  "switch_id": "living_room",
  "action": "toggle",
  "attributes": {
    "source": "telegram",
    "user": "john"
  }
}
```

**Actions:** `on`, `off`, `toggle`, `status`

**Attributes** are optional - use them to track context like who triggered the switch or from where.

### Response

```json
{
  "status": "success",
  "switch_id": "living_room",
  "action": "toggle",
  "state": "on",
  "attributes": {
    "source": "telegram",
    "user": "john",
    "last_triggered_at": "2026-02-05T12:30:00+00:00"
  }
}
```

### Error Responses

| Code | Meaning |
|------|---------|
| 401 | Invalid or missing JWT token |
| 404 | Switch not found |
| 422 | Invalid action or malformed request |
| 500 | Internal server error |

## Quick Start Examples

### Generate a JWT Token

```python
import jwt
from datetime import datetime, timedelta, timezone

SECRET = "your-secret-from-config"  # Same as in HA config

token = jwt.encode(
    {"iss": "my-app", "exp": datetime.now(timezone.utc) + timedelta(days=365)},
    SECRET,
    algorithm="HS256"
)
print(token)
```

Or use the helper script:
```bash
python scripts/generate_token.py
```

### curl Examples

**Check server status:**
```bash
curl http://your-ha-ip:8099/
```

**Health check:**
```bash
curl http://your-ha-ip:8099/health
```

**Turn on a switch:**
```bash
curl -X POST http://your-ha-ip:8099/webhook \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"switch_id": "doorbell", "action": "on"}'
```

**Toggle with attributes:**
```bash
curl -X POST http://your-ha-ip:8099/webhook \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"switch_id": "doorbell", "action": "toggle", "attributes": {"source": "curl"}}'
```

**Get status:**
```bash
curl -X POST http://your-ha-ip:8099/webhook \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"switch_id": "doorbell", "action": "status"}'
```

### Python Example

```python
import requests
import jwt
from datetime import datetime, timedelta, timezone

# Generate token (do this once, reuse the token)
SECRET = "your-jwt-secret"
token = jwt.encode(
    {"iss": "my-bot", "exp": datetime.now(timezone.utc) + timedelta(days=365)},
    SECRET,
    algorithm="HS256"
)

# Make a request
response = requests.post(
    "http://homeassistant.local:8099/webhook",
    headers={"Authorization": f"Bearer {token}"},
    json={"switch_id": "doorbell", "action": "on"}
)

print(response.json())
```

## Troubleshooting

**Integration not showing up?**
- Restart Home Assistant after installation
- Check **Settings → System → Logs** for errors

**Getting 401 Unauthorized?**
- Make sure your JWT secret matches exactly (case-sensitive)
- Check if your token has expired
- Verify the Authorization header format: `Bearer <token>` (note the space)

**Switch not found (404)?**
- Double-check the `switch_id` matches your configuration
- The ID is case-sensitive

**Port already in use?**
- Another service is using port 8099
- Change the port in integration settings (reconfigure)

**Server not responding?**
- Wait a few seconds after HA restart (server starts with a small delay)
- Check if the port is accessible (firewall rules)
- Look for errors in Home Assistant logs

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

Found a bug or have an idea? Open an issue or submit a pull request!
