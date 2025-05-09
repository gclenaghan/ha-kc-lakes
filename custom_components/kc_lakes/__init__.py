import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, PLATFORMS
from .coordinator import KCLakeBuoyDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    _LOGGER.info(
        "Setting up King County Lake Buoy integration (Entry ID: %s)", entry.entry_id
    )

    session = async_get_clientsession(hass)
    coordinator = KCLakeBuoyDataUpdateCoordinator(hass, session)

    # Fetch initial data so we have it when platforms are set up
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms (sensor, etc.)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("King County Lake Buoy integration setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info(
        "Unloading King County Lake Buoy integration (Entry ID: %s)", entry.entry_id
    )

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Clean up data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:  # Remove domain data if it's the last entry
            hass.data.pop(DOMAIN)
        _LOGGER.info("King County Lake Buoy integration unload complete")

    return unload_ok
