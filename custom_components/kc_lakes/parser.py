"""Parser for King County Lake Buoy map data payloads."""

from __future__ import annotations

from datetime import datetime, tzinfo
import logging
from typing import Any

from .const import (
    KEY_AIR_TEMPERATURE,
    KEY_BUOY_LATITUDE,
    KEY_BUOY_LONGITUDE,
    KEY_WATER_LAST_UPDATE,
    KEY_WATER_TEMPERATURE,
    KEY_WEATHER_LAST_UPDATE,
    KEY_WIND_DIRECTION,
    KEY_WIND_SPEED,
)

_LOGGER = logging.getLogger(__name__)

_TIMESTAMP_FORMATS: tuple[str, ...] = (
    "%m/%d/%Y %I:%M:%S %p",
    "%m/%d/%Y %I:%M %p",
    "%m/%d/%Y %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
)


def _is_missing(raw_value: str) -> bool:
    """Return True if a raw column value represents missing data."""
    stripped = raw_value.strip()
    return not stripped or stripped.upper() == "NA"


def _parse_float(raw_value: str, field_name: str, lake_name: str) -> float | None:
    """Parse an optional float field, returning None if empty or invalid."""
    if _is_missing(raw_value):
        return None
    try:
        return float(raw_value.strip())
    except ValueError:
        _LOGGER.warning(
            "Invalid float value %r for %s on %s", raw_value, field_name, lake_name
        )
        return None


def _parse_timestamp(
    raw_value: str, tz: tzinfo, field_name: str, lake_name: str
) -> datetime | None:
    """Parse an optional King County local timestamp with timezone attached."""
    if _is_missing(raw_value):
        return None
    cleaned = " ".join(raw_value.strip().split())
    for fmt in _TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).replace(tzinfo=tz)
        except ValueError:
            continue
    _LOGGER.warning(
        "Unrecognized timestamp format %r for %s on %s",
        raw_value,
        field_name,
        lake_name,
    )
    return None


def _parse_wind_direction(raw_value: str) -> str | None:
    """Normalize King County wind direction strings such as 'from NW'."""
    if _is_missing(raw_value):
        return None
    cleaned = raw_value.strip()
    if cleaned.lower().startswith("from "):
        cleaned = cleaned[5:].strip()
    return cleaned or None


def parse_buoy_data(raw_data: str, tz: tzinfo) -> dict[str, dict[str, Any]]:
    """Parse delimited payload from GenerateMapData.aspx into per-lake dictionaries."""
    processed_data: dict[str, dict[str, Any]] = {}
    if not raw_data:
        return processed_data

    for record in raw_data.split("^|"):
        if not record.strip():
            continue

        columns = record.split("|\t")
        if len(columns) < 10:
            continue

        active_flag = columns[9].strip().upper()
        if active_flag != "Y":
            continue

        buoy_name = columns[0].strip()
        if not buoy_name:
            continue

        lake_name = (
            buoy_name if buoy_name.startswith("Lake ") else f"Lake {buoy_name}"
        )

        processed_data[lake_name] = {
            KEY_WEATHER_LAST_UPDATE: _parse_timestamp(
                columns[1], tz, KEY_WEATHER_LAST_UPDATE, lake_name
            ),
            KEY_AIR_TEMPERATURE: _parse_float(
                columns[2], KEY_AIR_TEMPERATURE, lake_name
            ),
            KEY_WIND_SPEED: _parse_float(columns[3], KEY_WIND_SPEED, lake_name),
            KEY_WIND_DIRECTION: _parse_wind_direction(columns[4]),
            KEY_WATER_TEMPERATURE: _parse_float(
                columns[5], KEY_WATER_TEMPERATURE, lake_name
            ),
            KEY_WATER_LAST_UPDATE: _parse_timestamp(
                columns[6], tz, KEY_WATER_LAST_UPDATE, lake_name
            ),
            KEY_BUOY_LATITUDE: _parse_float(
                columns[7], KEY_BUOY_LATITUDE, lake_name
            ),
            KEY_BUOY_LONGITUDE: _parse_float(
                columns[8], KEY_BUOY_LONGITUDE, lake_name
            ),
        }

    return processed_data
