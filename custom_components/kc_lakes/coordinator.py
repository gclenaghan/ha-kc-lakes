"""DataUpdateCoordinator for King County Lakes."""
import logging
import async_timeout
from dateutil.parser import parse
from typing import Dict, Any

from aiohttp import ClientSession, ClientError, ClientResponseError

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.core import HomeAssistant

from .const import DOMAIN, API_URL, API_TIMEOUT, SCAN_INTERVAL, LAKES

_LOGGER = logging.getLogger(__name__)


class KCLakesDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
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
                response.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)
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
             _LOGGER.exception("Unexpected error fetching data") # Logs the full traceback
             raise UpdateFailed(f"Unexpected error: {err}") from err
        
    def parse_buoy_data(self, raw_data):
        processed_data = {}
        for lake_raw_data in raw_data.split('^|'):
            lake_str_columns = lake_raw_data.split('|\t')
            if len(lake_str_columns) < 10 or lake_str_columns[9] != 'Y':
                continue
            lake_raw_data[lake_str_columns[0]] = {
                'weather_last_update': parse(lake_str_columns[1]),
                'air_temperature_c': float(lake_str_columns[2]),
                'wind_speed_m/s': float(lake_str_columns[3]),
                'wind_direction': lake_str_columns[4][5:], #[5:] removes the "from " prefix
                'water_temperature': float(lake_str_columns[5]),
                'water_last_update': parse(lake_str_columns[6]),
                'buoy_latitude': float(lake_str_columns[7]),
                'buoy_longitude': float(lake_str_columns[8]),
            }
        return processed_data