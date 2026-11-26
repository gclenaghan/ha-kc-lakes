"""DataUpdateCoordinator for King County Lakes Buoy Data."""

from __future__ import annotations

import asyncio
from datetime import UTC
import logging
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import API_TIMEOUT, API_URL, DOMAIN, PACIFIC_TIMEZONE, SCAN_INTERVAL
from .parser import parse_buoy_data

_LOGGER = logging.getLogger(__name__)


class KCLakeBuoyDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Coordinator to manage fetching King County Lakes buoy data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        session: ClientSession,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.session = session

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch and parse data from the King County Lake Buoy endpoint."""
        try:
            async with (
                asyncio.timeout(API_TIMEOUT),
                self.session.get(API_URL) as response,
            ):
                response.raise_for_status()
                raw_data = await response.text()
        except TimeoutError as err:
            raise UpdateFailed(
                "Timeout communicating with King County Lake Buoy API"
            ) from err
        except ClientResponseError as err:
            raise UpdateFailed(
                f"HTTP error {err.status} from King County Lake Buoy API: {err.message}"
            ) from err
        except ClientError as err:
            raise UpdateFailed(
                f"Error communicating with King County Lake Buoy API: {err}"
            ) from err

        pacific_tz = dt_util.get_time_zone(PACIFIC_TIMEZONE) or UTC
        return parse_buoy_data(raw_data, pacific_tz)
