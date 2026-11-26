"""Unit tests for the King County Lake Buoy payload parser."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import types
import unittest
from zoneinfo import ZoneInfo

# Allow importing custom_components.kc_lakes.parser without requiring the full
# Home Assistant runtime installed in lightweight test environments.
PACKAGE_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "kc_lakes"
if "homeassistant" not in sys.modules:
    cc_pkg = sys.modules.setdefault(
        "custom_components", types.ModuleType("custom_components")
    )
    cc_pkg.__path__ = [str(PACKAGE_DIR.parent)]
    kc_pkg = sys.modules.setdefault(
        "custom_components.kc_lakes", types.ModuleType("custom_components.kc_lakes")
    )
    kc_pkg.__path__ = [str(PACKAGE_DIR)]

from custom_components.kc_lakes.const import (  # noqa: E402
    KEY_AIR_TEMPERATURE,
    KEY_BUOY_LATITUDE,
    KEY_BUOY_LONGITUDE,
    KEY_WATER_LAST_UPDATE,
    KEY_WATER_TEMPERATURE,
    KEY_WEATHER_LAST_UPDATE,
    KEY_WIND_DIRECTION,
    KEY_WIND_SPEED,
)
from custom_components.kc_lakes.parser import parse_buoy_data  # noqa: E402

PACIFIC = ZoneInfo("America/Los_Angeles")

SAMPLE_LIVE_PAYLOAD = (
    "RUSS Edmondson|\t|\t|\t|\tNA|\t|\t|\t47.63538|\t-122.27069|\tN^|"
    "RUSS N. SAMM|\t|\t|\t|\tNA|\t|\t|\t47.62338|\t-122.07998|\tN^|"
    "RUSS N. WA|\t|\t|\t|\tNA|\t|\t|\t47.68707|\t-122.23319|\tN^|"
    "RUSS S. WA|\t|\t|\t|\tNA|\t|\t|\t47.59263|\t-122.27336|\tN^|"
    "Sammamish|\t11/26/2026 9:02:00 AM|\t12.5|\t8.8|\tfrom NW|\t11.35|\t"
    "11/26/2026 12:03:00 AM|\t47.58167|\t-122.09000|\tY^|"
    "Washington|\t11/26/2026 8:02:00 AM|\t12.3|\t7.9|\tfrom S|\t11.92|\t"
    "11/26/2026 8:03:00 AM|\t47.61222|\t-122.25428|\tY^|"
)


class TestParseBuoyData(unittest.TestCase):
    """Tests for parse_buoy_data."""

    def test_live_payload_parses_active_lakes_and_skips_inactive(self) -> None:
        """Only active ('Y') buoys are returned with properly typed values."""
        result = parse_buoy_data(SAMPLE_LIVE_PAYLOAD, PACIFIC)

        self.assertEqual(set(result.keys()), {"Lake Sammamish", "Lake Washington"})

        samm = result["Lake Sammamish"]
        self.assertEqual(samm[KEY_AIR_TEMPERATURE], 12.5)
        self.assertEqual(samm[KEY_WIND_SPEED], 8.8)
        self.assertEqual(samm[KEY_WIND_DIRECTION], "NW")
        self.assertEqual(samm[KEY_WATER_TEMPERATURE], 11.35)
        self.assertEqual(samm[KEY_BUOY_LATITUDE], 47.58167)
        self.assertEqual(samm[KEY_BUOY_LONGITUDE], -122.09)
        self.assertEqual(
            samm[KEY_WEATHER_LAST_UPDATE],
            datetime(2026, 11, 26, 9, 2, 0, tzinfo=PACIFIC),
        )
        # November is PST (UTC-8)
        self.assertEqual(
            samm[KEY_WEATHER_LAST_UPDATE].utcoffset(), timedelta(hours=-8)
        )

    def test_summer_dst_offset_applied_automatically(self) -> None:
        """Summer timestamps resolve to PDT (UTC-7) with ZoneInfo."""
        payload = (
            "Washington|\t7/15/2026 2:30:00 PM|\t24.1|\t3.2|\tfrom NNW|\t21.8|\t"
            "7/15/2026 2:00:00 PM|\t47.61222|\t-122.25428|\tY^|"
        )
        result = parse_buoy_data(payload, PACIFIC)
        ts = result["Lake Washington"][KEY_WEATHER_LAST_UPDATE]
        self.assertEqual(ts, datetime(2026, 7, 15, 14, 30, 0, tzinfo=PACIFIC))
        self.assertEqual(ts.utcoffset(), timedelta(hours=-7))

    def test_partial_or_missing_fields_on_active_buoy_do_not_crash(self) -> None:
        """Empty or 'NA' fields on one buoy return None without breaking other lakes."""
        payload = (
            "Sammamish|\t|\t|\t|\tNA|\t14.2|\t5/10/2026 6:00:00 AM|\t47.58|\t-122.09|\tY^|"
            "Washington|\t5/10/2026 9:00:00 AM|\t15.0|\t4.5|\tCalm|\t|\t|\t47.61|\t-122.25|\tY^|"
        )
        result = parse_buoy_data(payload, timezone.utc)

        self.assertEqual(set(result.keys()), {"Lake Sammamish", "Lake Washington"})

        samm = result["Lake Sammamish"]
        self.assertIsNone(samm[KEY_WEATHER_LAST_UPDATE])
        self.assertIsNone(samm[KEY_AIR_TEMPERATURE])
        self.assertIsNone(samm[KEY_WIND_SPEED])
        self.assertIsNone(samm[KEY_WIND_DIRECTION])
        self.assertEqual(samm[KEY_WATER_TEMPERATURE], 14.2)

        wash = result["Lake Washington"]
        self.assertEqual(wash[KEY_AIR_TEMPERATURE], 15.0)
        self.assertEqual(wash[KEY_WIND_DIRECTION], "Calm")
        self.assertIsNone(wash[KEY_WATER_TEMPERATURE])
        self.assertIsNone(wash[KEY_WATER_LAST_UPDATE])

    def test_corrupt_values_log_and_return_none(self) -> None:
        """Malformed numeric or timestamp strings degrade to None safely."""
        payload = (
            "Lake Union|\tnot-a-date|\tbad-float|\t2.1|\tFrom SE|\t18.0|\t"
            "2026-08-01 13:15:00|\t47.63|\t-122.33|\tY^|"
        )
        with self.assertLogs("custom_components.kc_lakes.parser", level="WARNING"):
            result = parse_buoy_data(payload, PACIFIC)

        # Already prefixed with "Lake ", so shouldn't become "Lake Lake Union"
        self.assertIn("Lake Union", result)
        union = result["Lake Union"]
        self.assertIsNone(union[KEY_WEATHER_LAST_UPDATE])
        self.assertIsNone(union[KEY_AIR_TEMPERATURE])
        self.assertEqual(union[KEY_WIND_SPEED], 2.1)
        self.assertEqual(union[KEY_WIND_DIRECTION], "SE")
        self.assertEqual(
            union[KEY_WATER_LAST_UPDATE],
            datetime(2026, 8, 1, 13, 15, 0, tzinfo=PACIFIC),
        )

    def test_empty_and_malformed_payload(self) -> None:
        """Empty or truncated payloads return an empty dictionary."""
        self.assertEqual(parse_buoy_data("", PACIFIC), {})
        self.assertEqual(parse_buoy_data("short|\trow^|", PACIFIC), {})


if __name__ == "__main__":
    unittest.main()
