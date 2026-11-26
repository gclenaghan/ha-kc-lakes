# King County Lakes Buoy Data

Home Assistant custom integration that polls real-time meteorological and surface water (1m depth) measurements from King County's lake profiling buoys (currently **Lake Washington** and **Lake Sammamish**). Useful for checking whether it's a good day for paddleboarding or swimming around the start and end of summer.

Data source: <https://green2.kingcounty.gov/lake-buoy/>

## Sensors

For each active King County buoy, a device (`Lake Washington`, `Lake Sammamish`, etc.) is created and updated every 10 minutes with the following entities:

| Sensor | Unit / Format | Category |
| :--- | :--- | :--- |
| **Water Temperature** *(1m depth)* | °C *(auto-converted by HA to °F if configured)* | Primary |
| **Air Temperature** | °C *(auto-converted by HA to °F if configured)* | Primary |
| **Wind Speed** | m/s *(auto-converted by HA to mph/kn if configured)* | Primary |
| **Wind Direction** | Compass cardinal (`NW`, `S`, etc.) | Primary |
| **Weather Last Update** | Timestamp | Diagnostic |
| **Water Last Update** | Timestamp | Diagnostic |
| **Buoy Latitude** | ° | Diagnostic |
| **Buoy Longitude** | ° | Diagnostic |

> **Note:** King County buoy measurements are provisional data subject to revision.

## Installation (HACS)

1. Open **HACS** in Home Assistant.
2. Add `https://github.com/gclenaghan/ha-kc-lakes` as a **Custom Repository** (Category: **Integration**).
3. Install **King County Lakes Buoy Data** and restart Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration** and search for **King County Lakes Buoy Data**.
