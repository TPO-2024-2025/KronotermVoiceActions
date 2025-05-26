# __init__.py

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry

#
from homeassistant.const import Platform, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.typing import ConfigType

from .config_flow import (
    CONF_TYPE,
    ENTRY_TYPE_CUSTOM,
    ENTRY_TYPE_REMOTE,
)

from .const import ATTR_SPEAKER, DOMAIN
from .data import WyomingService
from .devices import SatelliteDevice
from .models import DomainDataItem
from .websocket_api import async_register_websocket_api

_LOGGER = logging.getLogger(__name__)


CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

SATELLITE_PLATFORMS = [
    Platform.ASSIST_SATELLITE,
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.NUMBER,
]

__all__ = [
    "ATTR_SPEAKER",
    "DOMAIN",
    "async_setup",
    "async_setup_entry",
    "async_unload_entry",
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Wyoming integration."""
    async_register_websocket_api(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Load Wyoming based on entry type."""
    hass.data.setdefault(DOMAIN, {})
    entry_type = entry.data.get(CONF_TYPE)

    if entry_type == ENTRY_TYPE_CUSTOM:

        _LOGGER.info(
            "Setting up Kronoterm Custom Conversation Agent (Entry ID: %s)",
            entry.entry_id,
        )

        item = DomainDataItem(entry_data=entry.data)
        hass.data[DOMAIN][entry.entry_id] = item

        await hass.config_entries.async_forward_entry_setups(
            entry, [Platform.CONVERSATION]
        )

        return True

    elif entry_type == ENTRY_TYPE_REMOTE:

        host = entry.data[CONF_HOST]
        port = entry.data[CONF_PORT]
        _LOGGER.info(
            "Setting up remote Wyoming service at %s:%s (Entry ID: %s)",
            host,
            port,
            entry.entry_id,
        )

        service = await WyomingService.create(host, port)

        if service is None:
            raise ConfigEntryNotReady(
                f"Unable to connect to Wyoming service at {host}:{port}"
            )

        item = DomainDataItem(entry_data=entry.data, service=service)
        hass.data[DOMAIN][entry.entry_id] = item

        platforms_to_load = set(service.platforms)

        _LOGGER.debug("Platforms to load for %s:%s: %s", host, port, platforms_to_load)

        if platforms_to_load:
            await hass.config_entries.async_forward_entry_setups(
                entry, platforms_to_load
            )

        entry.async_on_unload(entry.add_update_listener(update_listener))

        if (
            satellite_info := service.info.satellite
        ) is not None and satellite_info.installed:
            _LOGGER.debug("Setting up satellite device for %s:%s", host, port)
            dev_reg = dr.async_get(hass)
            satellite_id = entry.entry_id
            device = dev_reg.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, satellite_id)},
                name=satellite_info.name,
                suggested_area=satellite_info.area,
            )
            item.device = SatelliteDevice(
                satellite_id=satellite_id,
                device_id=device.id,
            )

            await hass.config_entries.async_forward_entry_setups(
                entry, SATELLITE_PLATFORMS
            )

        return True

    else:
        _LOGGER.error(
            "Unknown configuration entry type '%s' for entry %s",
            entry_type,
            entry.entry_id,
        )
        return False


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update (currently only relevant for remote services)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Wyoming entry based on type."""
    if entry.entry_id not in hass.data.get(DOMAIN, {}):
        return True

    item: DomainDataItem = hass.data[DOMAIN][entry.entry_id]
    entry_type = item.entry_data.get(CONF_TYPE)

    platforms_to_unload: set[Platform] = set()

    if entry_type == ENTRY_TYPE_CUSTOM:

        _LOGGER.info(
            "Unloading Kronoterm Custom Conversation Agent (Entry ID: %s)",
            entry.entry_id,
        )

        platforms_to_unload = {Platform.CONVERSATION}

    elif entry_type == ENTRY_TYPE_REMOTE:

        host = item.entry_data.get(CONF_HOST, "unknown host")
        port = item.entry_data.get(CONF_PORT, "unknown port")
        _LOGGER.info(
            "Unloading remote Wyoming service for %s:%s (Entry ID: %s)",
            host,
            port,
            entry.entry_id,
        )

        if item.service:
            platforms_to_unload.update(item.service.platforms)

        if item.device is not None:
            platforms_to_unload.update(SATELLITE_PLATFORMS)

    else:
        _LOGGER.error(
            "Cannot unload entry %s: Unknown configuration entry type '%s'",
            entry.entry_id,
            entry_type,
        )
        if entry.entry_id in hass.data.get(DOMAIN, {}):
            del hass.data[DOMAIN][entry.entry_id]
            if not hass.data[DOMAIN]:
                del hass.data[DOMAIN]
        return False

    _LOGGER.debug("Platforms to unload for %s: %s", entry.entry_id, platforms_to_unload)

    unload_ok = False
    if platforms_to_unload:
        unload_ok = await hass.config_entries.async_unload_platforms(
            entry, platforms_to_unload
        )
    else:

        unload_ok = True

    if unload_ok:
        del hass.data[DOMAIN][entry.entry_id]
        if not hass.data[DOMAIN]:
            del hass.data[DOMAIN]

    return unload_ok
