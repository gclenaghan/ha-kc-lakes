"""Constants for the King County Lakes Buoy Data integration."""

from datetime import timedelta

DOMAIN = "kc_lakes"
DEFAULT_NAME = "King County Lakes Buoy Data"

# API Details
BUOY_MAP_URL = "https://green2.kingcounty.gov/lake-buoy/"
API_URL = "https://green2.kingcounty.gov/lake-buoy/GenerateMapData.aspx"
API_TIMEOUT = 20  # Seconds
SCAN_INTERVAL = timedelta(minutes=10)
PACIFIC_TIMEZONE = "America/Los_Angeles"

# Data Keys
KEY_WEATHER_LAST_UPDATE = "weather_last_update"
KEY_AIR_TEMPERATURE = "air_temperature"
KEY_WIND_SPEED = "wind_speed"
KEY_WIND_DIRECTION = "wind_direction"
KEY_WATER_TEMPERATURE = "water_temperature"
KEY_WATER_LAST_UPDATE = "water_last_update"
KEY_BUOY_LATITUDE = "buoy_latitude"
KEY_BUOY_LONGITUDE = "buoy_longitude"

# Attribution
ATTRIBUTION = f"Data provided by King County ({BUOY_MAP_URL})"
