# Incoming Webhook - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/torquemada163/ha-incoming-webhook.svg)](https://github.com/torquemada163/ha-incoming-webhook/releases)

Home Assistant Integration for secure webhook API to control switch entities from external services.

## ✨ Features

- 🔐 JWT authentication for secure access
- 🔄 Four actions: on, off, toggle, status
- 🎯 Automatic entity creation (no manual setup!)
- 🏷️ Custom attributes support
- 📝 Persistent state across restarts
- 🚀 Works on all HA installations (not just HAOS/Supervised)

## 📦 Installation

### Via HACS (Recommended)

1. Open HACS
2. Go to "Integrations"
3. Click the 3 dots in the top right
4. Select "Custom repositories"
5. Add this repository: `https://github.com/torquemada163/ha-incoming-webhook`
6. Category: Integration
7. Click "Add"
8. Find "Incoming Webhook" and click "Download"
9. Restart Home Assistant

### Manual Installation

1. Copy `custom_components/incoming_webhook` to your `config/custom_components/` directory
2. Restart Home Assistant

## ⚙️ Configuration

1. Go to **Settings → Devices & Services → Integrations**
2. Click **+ Add Integration**
3. Search for "Incoming Webhook"
4. Configure:
   - **JWT Secret** (min 32 characters)
   - **Port** (default: 8099)
   - **Switches** (ID, Name, Icon for each switch)
5. Entities will be created automatically as `switch.webhook_*`

## 🔌 API Usage

### Endpoint

```
POST http://homeassistant.local:8099/webhook
```

### Authentication

```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### Request Format

```json
{
  "switch_id": "telegram_bot",
  "action": "on",
  "attributes": {
    "source": "telegram",
    "user": "john"
  }
}
```

**Actions:** `on` | `off` | `toggle` | `status`

### Response

```json
{
  "status": "success",
  "switch_id": "telegram_bot",
  "action": "on",
  "state": "on",
  "attributes": {
    "source": "telegram",
    "user": "john",
    "last_triggered_at": "2026-02-03T00:00:00+00:00"
  }
}
```

## 🔑 JWT Token Generation

```python
import jwt
from datetime import datetime, timedelta, timezone

JWT_SECRET = "your-secret-from-config"

payload = {
    "iss": "my-service",
    "exp": datetime.now(timezone.utc) + timedelta(days=365)
}

token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
print(token)
```

## 📝 Example: Telegram Bot

```python
import requests
import jwt
from datetime import datetime, timedelta, timezone

# Generate JWT token
JWT_SECRET = "your-secret"
token = jwt.encode(
    {"iss": "telegram_bot", "exp": datetime.now(timezone.utc) + timedelta(days=365)},
    JWT_SECRET,
    algorithm="HS256"
)

# Call webhook
response = requests.post(
    "http://homeassistant.local:8099/webhook",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "switch_id": "doorbell",
        "action": "on",
        "attributes": {"source": "telegram", "user": "john"}
    }
)

print(response.json())
```

## 🔄 Migration from Addon v1.x

See [MIGRATION.md](docs/MIGRATION.md) for detailed migration guide from the old addon architecture.

**Key changes:**
- Entity IDs: `input_boolean.webhook_*` → `switch.webhook_*`
- Installation: Addon → HACS Integration
- Configuration: addon config.yaml → UI config flow

## 🐛 Troubleshooting

**Integration doesn't appear in UI:**
- Make sure you restarted Home Assistant after installation
- Check logs: Settings → System → Logs

**Webhook returns 401 Unauthorized:**
- Verify JWT secret matches configuration
- Check token expiration
- Ensure `Authorization: Bearer <token>` header is present

**Switch entities not created:**
- Check integration configuration
- Restart Home Assistant
- Check logs for errors

## 📖 Documentation

- [Full Documentation](docs/)
- [API Reference](docs/api.md)
- [Migration Guide](docs/MIGRATION.md)

## 🤝 Contributing

Contributions are welcome! Please open an issue or pull request.

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🙏 Credits

Originally developed as Home Assistant Addon, rewritten as HACS Integration for better user experience.

Previous project: [home-assistant-incoming-webhook](https://github.com/torquemada163/home-assistant-incoming-webhook)
