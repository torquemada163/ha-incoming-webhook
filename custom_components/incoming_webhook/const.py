"""Constants for the Incoming Webhook integration."""

from typing import Final

# Domain identifier
DOMAIN: Final = "incoming_webhook"

# Supported platforms
PLATFORMS: Final[list[str]] = ["switch"]

# Config entry data keys
CONF_JWT_SECRET: Final = "jwt_secret"
CONF_PORT: Final = "port"
CONF_SWITCHES: Final = "switches"

# Switch configuration keys
CONF_SWITCH_ID: Final = "id"
CONF_SWITCH_NAME: Final = "name"
CONF_SWITCH_ICON: Final = "icon"

# Default values
DEFAULT_PORT: Final = 8099
DEFAULT_ICON: Final = "mdi:light-switch"

# Validation constraints
MIN_JWT_SECRET_LENGTH: Final = 32
MIN_PORT: Final = 1024
MAX_PORT: Final = 65535

# Entity attributes
ATTR_LAST_TRIGGERED_AT: Final = "last_triggered_at"
ATTR_CUSTOM_ATTRIBUTES: Final = "custom_attributes"
