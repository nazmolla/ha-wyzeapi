"""The Wyze Home Assistant Integration integration."""
from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.check_config import HomeAssistantConfig
from wyzeapy import Wyzeapy

from .const import DOMAIN, CONF_CLIENT, CONF_COORDINATOR, DISCOVERY_SCAN_INTERVAL

PLATFORMS = ["light", "switch", "binary_sensor", "lock", "climate",
             "alarm_control_panel"]  # Fixme: Re add scene
_LOGGER = logging.getLogger(__name__)


# noinspection PyUnusedLocal
async def async_setup(hass: HomeAssistant, config: HomeAssistantConfig,
                      discovery_info=None):
    # pylint: disable=unused-argument
    """Set up the Alexa domain."""
    if DOMAIN not in config:
        _LOGGER.debug(
            "Nothing to import from configuration.yaml, loading from "
            "Integrations",
        )
        return True

    domainconfig = config.get(DOMAIN)
    entry_found = False
    # pylint: disable=logging-not-lazy
    _LOGGER.debug("Importing config information for %s from configuration.yml" %
                  domainconfig[CONF_USERNAME])
    if hass.config_entries.async_entries(DOMAIN):
        _LOGGER.debug("Found existing config entries")
        for entry in hass.config_entries.async_entries(DOMAIN):
            if (entry.data.get(CONF_USERNAME) == domainconfig[CONF_USERNAME] and entry.data.get(CONF_PASSWORD) ==
                    domainconfig[CONF_PASSWORD]):
                _LOGGER.debug("Updating existing entry")
                hass.config_entries.async_update_entry(
                    entry,
                    data={
                        CONF_USERNAME: domainconfig[CONF_USERNAME],
                        CONF_PASSWORD: domainconfig[CONF_PASSWORD],
                    },
                )
                entry_found = True
                break
    if not entry_found:
        _LOGGER.debug("Creating new config entry")
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data={
                    CONF_USERNAME: domainconfig[CONF_USERNAME],
                    CONF_PASSWORD: domainconfig[CONF_PASSWORD],
                },
            )
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Wyze Home Assistant Integration from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    client = await Wyzeapy.create()
    await client.login(entry.data.get(CONF_USERNAME), entry.data.get(CONF_PASSWORD))

    hass.data[DOMAIN][entry.entry_id] = {
        CONF_CLIENT: client
    }

    for platform in PLATFORMS:
        hass.create_task(hass.config_entries.async_forward_entry_setup(entry, platform))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    client: Wyzeapy = hass.data[DOMAIN][entry.entry_id]
    await client.async_close()

    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
