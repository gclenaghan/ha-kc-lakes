"""DataUpdateCoordinator for King County Lakes."""

import logging
import async_timeout
from dateutil.parser import parse
from datetime import tzinfo
from typing import Dict, Any
from zoneinfo import ZoneInfo

from aiohttp import ClientSession, ClientError, ClientResponseError

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    API_URL,
    API_TIMEOUT,
    SCAN_INTERVAL,
    KEY_WEATHER_LAST_UPDATE,
    KEY_AIR_TEMPERATURE,
    KEY_WIND_SPEED,
    KEY_WIND_DIRECTION,
    KEY_WATER_TEMPERATURE,
    KEY_WATER_LAST_UPDATE,
    KEY_BUOY_LATITUDE,
    KEY_BUOY_LONGITUDE,
)

_LOGGER = logging.getLogger(__name__)


class KCLakeBuoyDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching King County Lakes data."""

    def __init__(self, hass: HomeAssistant, session: ClientSession):
        self.session = session
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            async with async_timeout.timeout(API_TIMEOUT):
                response = await self.session.get(API_URL)
                response.raise_for_status()  # Raise exception for bad status codes (4xx or 5xx)
                # Assuming the API returns a list of dictionaries, one for each lake/buoy
                raw_data = await response.text()

                return self.parse_buoy_data(raw_data)

        except ClientResponseError as err:
            _LOGGER.error("HTTP error fetching data: %s - %s", err.status, err.message)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except ClientError as err:
            _LOGGER.error("Client error fetching data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except TimeoutError:
            _LOGGER.error("Timeout fetching data")
            raise UpdateFailed("Timeout communicating with API") from TimeoutError
        except Exception as err:
            _LOGGER.exception(
                "Unexpected error fetching data"
            )  # Logs the full traceback
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def parse_buoy_data(self, raw_data):
        processed_data = {}
        for lake_raw_data in raw_data.split("^|"):
            lake_str_columns = lake_raw_data.split("|\t")
            if len(lake_str_columns) < 10 or lake_str_columns[9] != "Y":
                continue
            pacific_zone = ZoneInfo("America/Los_Angeles")
            lake_name = "Lake " + lake_str_columns[0]
            processed_data[lake_name] = {
                KEY_WEATHER_LAST_UPDATE: parse(lake_str_columns[1]).replace(
                    tzinfo=pacific_zone
                ),
                KEY_AIR_TEMPERATURE: float(lake_str_columns[2]),
                KEY_WIND_SPEED: float(lake_str_columns[3]),
                KEY_WIND_DIRECTION: lake_str_columns[4][
                    5:
                ],  # [5:] removes the "from " prefix
                KEY_WATER_TEMPERATURE: float(lake_str_columns[5]),
                KEY_WATER_LAST_UPDATE: parse(lake_str_columns[6]).replace(
                    tzinfo=pacific_zone
                ),
                KEY_BUOY_LATITUDE: float(lake_str_columns[7]),
                KEY_BUOY_LONGITUDE: float(lake_str_columns[8]),
            }
        return processed_data
