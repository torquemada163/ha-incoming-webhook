"""Config flow for Incoming Webhook integration."""

import json
import logging
import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_JWT_SECRET,
    CONF_PORT,
    CONF_SWITCHES,
    CONF_SWITCH_ID,
    CONF_SWITCH_NAME,
    CONF_SWITCH_ICON,
    DEFAULT_PORT,
    DEFAULT_ICON,
    MIN_JWT_SECRET_LENGTH,
    MIN_PORT,
    MAX_PORT,
)

_LOGGER = logging.getLogger(__name__)

# Regex pattern for switch ID validation (letters, numbers, underscores only)
SWITCH_ID_REGEX = re.compile(r"^[a-zA-Z0-9_]+$")


class IncomingWebhookConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Incoming Webhook."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._reauth_entry: config_entries.ConfigEntry | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow handler."""
        return IncomingWebhookOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate input
            validation_errors = self._validate_input(user_input)
            if validation_errors:
                errors = validation_errors
            else:
                # Create the config entry
                return self.async_create_entry(
                    title="Incoming Webhook",
                    data=user_input,
                )

        # Show the form
        return self.async_show_form(
            step_id="user",
            data_schema=self._get_user_schema(),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration."""
        errors: dict[str, str] = {}
        entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )

        if user_input is not None:
            # Validate input
            validation_errors = self._validate_input(user_input)
            if validation_errors:
                errors = validation_errors
            else:
                # Update config entry
                self.hass.config_entries.async_update_entry(
                    entry,
                    data=user_input,
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")

        # Show form with current values
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._get_user_schema(entry.data if entry else None),
            errors=errors,
        )

    def _get_user_schema(
        self, current_config: dict[str, Any] | None = None
    ) -> vol.Schema:
        """
        Get the schema for user input.
        
        Args:
            current_config: Current configuration for default values
        """
        if current_config:
            # For reconfigure - prefill with current values
            switches_str = json.dumps(current_config.get(CONF_SWITCHES, []))
            return vol.Schema(
                {
                    vol.Required(
                        CONF_JWT_SECRET,
                        default=current_config.get(CONF_JWT_SECRET, ""),
                    ): str,
                    vol.Required(
                        CONF_PORT,
                        default=current_config.get(CONF_PORT, DEFAULT_PORT),
                    ): int,
                    vol.Required(CONF_SWITCHES, default=switches_str): str,
                }
            )
        else:
            # For initial setup - empty values with defaults
            return vol.Schema(
                {
                    vol.Required(CONF_JWT_SECRET): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(
                        CONF_SWITCHES,
                        default='[{"id": "example", "name": "Example Switch"}]',
                    ): str,
                }
            )

    def _validate_input(self, user_input: dict[str, Any]) -> dict[str, str]:
        """
        Validate user input.
        
        Args:
            user_input: Data from the user
            
        Returns:
            Dict of errors (empty if validation passed)
        """
        errors: dict[str, str] = {}

        # Validate JWT secret
        jwt_secret = user_input.get(CONF_JWT_SECRET, "")
        if len(jwt_secret) < MIN_JWT_SECRET_LENGTH:
            errors["base"] = "invalid_jwt_secret"
            return errors

        # Validate port
        port = user_input.get(CONF_PORT)
        if not isinstance(port, int) or port < MIN_PORT or port > MAX_PORT:
            errors["base"] = "invalid_port"
            return errors

        # Validate switches
        switches_str = user_input.get(CONF_SWITCHES, "")
        try:
            switches = json.loads(switches_str)
        except json.JSONDecodeError:
            errors["base"] = "invalid_switches_format"
            return errors

        if not isinstance(switches, list) or len(switches) == 0:
            errors["base"] = "empty_switches"
            return errors

        # Validate each switch
        switch_ids = set()
        validated_switches = []

        for switch in switches:
            if not isinstance(switch, dict):
                errors["base"] = "invalid_switches_format"
                return errors

            switch_id = switch.get(CONF_SWITCH_ID)
            switch_name = switch.get(CONF_SWITCH_NAME)

            # Check required fields
            if not switch_id or not switch_name:
                errors["base"] = "invalid_switches_format"
                return errors

            # Validate switch ID format
            if not SWITCH_ID_REGEX.match(switch_id):
                errors["base"] = "invalid_switch_id"
                return errors

            # Check uniqueness
            if switch_id in switch_ids:
                errors["base"] = "duplicate_switch_id"
                return errors

            switch_ids.add(switch_id)

            # Build validated switch with default icon if needed
            validated_switches.append(
                {
                    CONF_SWITCH_ID: switch_id,
                    CONF_SWITCH_NAME: switch_name,
                    CONF_SWITCH_ICON: switch.get(CONF_SWITCH_ICON, DEFAULT_ICON),
                }
            )

        # Update user_input with validated switches
        user_input[CONF_SWITCHES] = validated_switches

        return errors


class IncomingWebhookOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Incoming Webhook."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        # No additional options for now
        # This can be extended later for logging settings, etc.
        return self.async_create_entry(title="", data={})
