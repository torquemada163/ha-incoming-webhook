"""The Incoming Webhook integration."""

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up Incoming Webhook from a config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry for this integration
        
    Returns:
        True if setup was successful
    """
    _LOGGER.info("Setting up Incoming Webhook integration")
    
    # Store config entry data for access from other modules
    # Note: entry.data is a mappingproxy (immutable), so we create a new dict
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
    }
    
    # Set up platforms (switch)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # TODO: Phase 4 - Start webhook server
    # The FastAPI server will be started here as a background task
    
    _LOGGER.info("Incoming Webhook integration setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unload a config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry to unload
        
    Returns:
        True if unload was successful
    """
    _LOGGER.info("Unloading Incoming Webhook integration")
    
    # TODO: Phase 4 - Stop webhook server
    # Gracefully shut down the FastAPI server here
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Remove data from hass.data
        hass.data[DOMAIN].pop(entry.entry_id)
    
    _LOGGER.info("Incoming Webhook integration unloaded")
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """
    Reload config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry to reload
    """
    _LOGGER.info("Reloading Incoming Webhook integration")
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
