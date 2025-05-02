from datetime import timedelta

DOMAIN = "kc_lakes"
PLATFORMS = ["sensor"]

# API Details
API_URL = "https://green2.kingcounty.gov/lake-buoy/GenerateMapData.aspx"
API_TIMEOUT = 20  # Seconds
SCAN_INTERVAL = timedelta(minutes=10)

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
ATTRIBUTION = "Data provided by King County https://green2.kingcounty.gov/lake-buoy/"
