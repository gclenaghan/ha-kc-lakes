"""Sensor platform for King County Lakes Buoy Data."""

from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import DEGREE, EntityCategory, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import KCLakesConfigEntry
from .const import (
    ATTRIBUTION,
    BUOY_MAP_URL,
    DOMAIN,
    KEY_AIR_TEMPERATURE,
    KEY_BUOY_LATITUDE,
    KEY_BUOY_LONGITUDE,
    KEY_WATER_LAST_UPDATE,
    KEY_WATER_TEMPERATURE,
    KEY_WEATHER_LAST_UPDATE,
    KEY_WIND_DIRECTION,
    KEY_WIND_SPEED,
)
from .coordinator import KCLakeBuoyDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

LAKE_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=KEY_WATER_TEMPERATURE,
        translation_key="water_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:water-thermometer",
    ),
    SensorEntityDescription(
        key=KEY_AIR_TEMPERATURE,
        translation_key="air_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:thermometer",
    ),
    SensorEntityDescription(
        key=KEY_WIND_SPEED,
        translation_key="wind_speed",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:weather-windy",
    ),
    SensorEntityDescription(
        key=KEY_WIND_DIRECTION,
        translation_key="wind_direction",
        icon="mdi:compass-outline",
    ),
    SensorEntityDescription(
        key=KEY_WEATHER_LAST_UPDATE,
        translation_key="weather_last_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:clock-outline",
    ),
    SensorEntityDescription(
        key=KEY_WATER_LAST_UPDATE,
        translation_key="water_last_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:clock-outline",
    ),
    SensorEntityDescription(
        key=KEY_BUOY_LATITUDE,
        translation_key="buoy_latitude",
        native_unit_of_measurement=DEGREE,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=5,
        icon="mdi:latitude",
    ),
    SensorEntityDescription(
        key=KEY_BUOY_LONGITUDE,
        translation_key="buoy_longitude",
        native_unit_of_measurement=DEGREE,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=5,
        icon="mdi:longitude",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KCLakesConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up King County Lakes buoy sensor entities."""
    coordinator = entry.runtime_data
    known_lakes: set[str] = set()

    @callback
    def _async_add_new_lakes() -> None:
        """Create entities for any newly discovered active lake buoys."""
        if not coordinator.data:
            return

        new_entities: list[KCLakeSensor] = []
        for lake_name in coordinator.data:
            if lake_name in known_lakes:
                continue
            known_lakes.add(lake_name)
            _LOGGER.debug("Adding buoy sensors for %s", lake_name)
            new_entities.extend(
                KCLakeSensor(coordinator, entry.entry_id, lake_name, description)
                for description in LAKE_SENSORS
            )

        if new_entities:
            async_add_entities(new_entities)

    _async_add_new_lakes()
    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_lakes))


class KCLakeSensor(CoordinatorEntity[KCLakeBuoyDataUpdateCoordinator], SensorEntity):
    """Representation of a King County Lake Buoy sensor."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KCLakeBuoyDataUpdateCoordinator,
        config_entry_id: str,
        lake_name: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._lake_name = lake_name
        self._attr_unique_id = f"{config_entry_id}_{lake_name}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, lake_name)},
            name=lake_name,
            manufacturer="King County",
            model="Lake Profiling Buoy",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=BUOY_MAP_URL,
        )

    @property
    def available(self) -> bool:
        """Return True if the coordinator succeeded and this lake is active."""
        return (
            super().available
            and self.coordinator.data is not None
            and self._lake_name in self.coordinator.data
        )

    @property
    def native_value(self) -> StateType | datetime:
        """Return the latest sensor reading from coordinator data."""
        if not self.coordinator.data:
            return None
        lake_data = self.coordinator.data.get(self._lake_name)
        if lake_data is None:
            return None
        return lake_data.get(self.entity_description.key)
