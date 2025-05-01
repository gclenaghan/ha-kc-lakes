from datetime import timedelta

DOMAIN = "kc_lakes"
PLATFORMS = ["sensor"]

# API Details
API_URL = "https://green2.kingcounty.gov/lake-buoy/GenerateMapData.aspx"
API_TIMEOUT = 20 # Seconds
SCAN_INTERVAL = timedelta(minutes=10)

LAKES = {"Washington", "Sammamish"}


# Attribution
ATTRIBUTION = "Data provided by King County https://green2.kingcounty.gov/lake-buoy/"
