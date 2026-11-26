"""The King County Lakes Buoy Data integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .coordinator import KCLakeBuoyDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

type KCLakesConfigEntry = ConfigEntry[KCLakeBuoyDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: KCLakesConfigEntry) -> bool:
    """Set up King County Lakes Buoy Data from a config entry."""
    _LOGGER.debug(
        "Setting up King County Lakes Buoy Data integration (entry_id=%s)",
        entry.entry_id,
    )

    session = async_get_clientsession(hass)
    coordinator = KCLakeBuoyDataUpdateCoordinator(hass, entry, session)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KCLakesConfigEntry) -> bool:
    """Unload a King County Lakes Buoy Data config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
