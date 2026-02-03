"""Switch platform for Incoming Webhook integration."""

import logging
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    CONF_SWITCHES,
    CONF_SWITCH_ID,
    CONF_SWITCH_NAME,
    CONF_SWITCH_ICON,
    ATTR_LAST_TRIGGERED_AT,
    ATTR_CUSTOM_ATTRIBUTES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    Set up switch entities from a config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry for this integration
        async_add_entities: Callback to add new entities
    """
    # Get switch configuration from entry data
    config_data = hass.data[DOMAIN][entry.entry_id]["config"]
    switches_config = config_data.get(CONF_SWITCHES, [])
    
    if not switches_config:
        _LOGGER.warning("No switches configured in config entry")
        return
    
    # Create an entity for each configured switch
    entities = [
        WebhookSwitch(hass, entry, switch_config)
        for switch_config in switches_config
    ]
    
    # Store references to entities for webhook server access
    hass.data[DOMAIN][entry.entry_id]["entities"] = {
        entity.switch_id: entity for entity in entities
    }
    
    # Add entities to Home Assistant
    async_add_entities(entities, True)
    
    _LOGGER.info(
        "Successfully set up %d webhook switch entities", len(entities)
    )


class WebhookSwitch(SwitchEntity, RestoreEntity):
    """Represents a virtual switch controlled via webhook."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        switch_config: dict[str, Any],
    ) -> None:
        """
        Initialize the webhook switch.
        
        Args:
            hass: Home Assistant instance
            entry: Config entry
            switch_config: Configuration for this specific switch
        """
        self.hass = hass
        self._entry = entry
        self._switch_id = switch_config[CONF_SWITCH_ID]
        self._attr_name = switch_config[CONF_SWITCH_NAME]
        self._attr_icon = switch_config.get(CONF_SWITCH_ICON)
        
        # Internal state
        self._attr_is_on = False
        self._custom_attrs: dict[str, Any] = {}
        
        _LOGGER.debug(
            "Initialized webhook switch: %s (id: %s)",
            self._attr_name,
            self._switch_id,
        )

    @property
    def unique_id(self) -> str:
        """
        Return a unique ID for this entity.
        
        Format: {entry_id}_{switch_id}
        This ensures persistence across restarts and reconfiguration.
        """
        return f"{self._entry.entry_id}_{self._switch_id}"

    @property
    def switch_id(self) -> str:
        """Return the switch ID used in webhook API calls."""
        return self._switch_id

    @property
    def device_info(self) -> DeviceInfo:
        """
        Return device information for grouping entities.
        
        All webhook switches are grouped under a single virtual device.
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Incoming Webhook",
            manufacturer="Custom Integration",
            model="Virtual Switch",
            sw_version="2.0.0",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """
        Return additional state attributes.
        
        Includes:
        - switch_id: The ID used in webhook API calls
        - last_triggered_at: Timestamp of last state change
        - custom_attributes: Any custom data sent via webhook
        """
        attributes = {
            "switch_id": self._switch_id,
        }
        
        if self._custom_attrs.get(ATTR_LAST_TRIGGERED_AT):
            attributes[ATTR_LAST_TRIGGERED_AT] = self._custom_attrs[
                ATTR_LAST_TRIGGERED_AT
            ]
        
        # Include custom attributes from webhook calls
        if custom := self._custom_attrs.get(ATTR_CUSTOM_ATTRIBUTES):
            attributes[ATTR_CUSTOM_ATTRIBUTES] = custom
        
        return attributes

    async def async_turn_on(self, **kwargs: Any) -> None:
        """
        Turn the switch on.
        
        Args:
            **kwargs: Additional service call parameters (unused)
        """
        _LOGGER.debug("Turning on switch: %s", self._switch_id)
        self._attr_is_on = True
        self._update_last_triggered()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """
        Turn the switch off.
        
        Args:
            **kwargs: Additional service call parameters (unused)
        """
        _LOGGER.debug("Turning off switch: %s", self._switch_id)
        self._attr_is_on = False
        self._update_last_triggered()
        self.async_write_ha_state()

    async def async_toggle(self, **kwargs: Any) -> None:
        """
        Toggle the switch state.
        
        Args:
            **kwargs: Additional service call parameters (unused)
        """
        _LOGGER.debug("Toggling switch: %s", self._switch_id)
        self._attr_is_on = not self._attr_is_on
        self._update_last_triggered()
        self.async_write_ha_state()

    async def async_set_custom_attributes(
        self, attributes: dict[str, Any]
    ) -> None:
        """
        Set custom attributes from webhook calls.
        
        This method will be called by the webhook server (Phase 4)
        to store additional data from external services.
        
        Args:
            attributes: Dictionary of custom attributes to store
        """
        _LOGGER.debug(
            "Setting custom attributes for switch %s: %s",
            self._switch_id,
            attributes,
        )
        self._custom_attrs[ATTR_CUSTOM_ATTRIBUTES] = attributes
        self.async_write_ha_state()

    def _update_last_triggered(self) -> None:
        """Update the timestamp of the last state change."""
        self._custom_attrs[ATTR_LAST_TRIGGERED_AT] = datetime.now(
            timezone.utc
        ).isoformat()

    async def async_added_to_hass(self) -> None:
        """
        Called when the entity is added to Home Assistant.
        
        Restores the previous state after HA restart or integration reload.
        """
        await super().async_added_to_hass()
        
        # Try to restore previous state
        if (old_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = old_state.state == STATE_ON
            
            # Restore attributes
            if old_state.attributes:
                if last_triggered := old_state.attributes.get(
                    ATTR_LAST_TRIGGERED_AT
                ):
                    self._custom_attrs[ATTR_LAST_TRIGGERED_AT] = last_triggered
                
                if custom_attrs := old_state.attributes.get(
                    ATTR_CUSTOM_ATTRIBUTES
                ):
                    self._custom_attrs[ATTR_CUSTOM_ATTRIBUTES] = custom_attrs
            
            _LOGGER.debug(
                "Restored state for switch %s: %s",
                self._switch_id,
                "on" if self._attr_is_on else "off",
            )
        else:
            _LOGGER.debug(
                "No previous state found for switch %s, starting as off",
                self._switch_id,
            )

    async def async_will_remove_from_hass(self) -> None:
        """Called when the entity is being removed from Home Assistant."""
        await super().async_will_remove_from_hass()
        
        # Clean up entity reference from hass.data
        if (
            DOMAIN in self.hass.data
            and self._entry.entry_id in self.hass.data[DOMAIN]
            and "entities" in self.hass.data[DOMAIN][self._entry.entry_id]
        ):
            self.hass.data[DOMAIN][self._entry.entry_id]["entities"].pop(
                self._switch_id, None
            )
        
        _LOGGER.debug("Removed webhook switch: %s", self._switch_id)
