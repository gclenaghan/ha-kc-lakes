import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfSpeed,
    FORMAT_TIME,
    DEGREE,
)

from .const import (
    DOMAIN,
    ATTRIBUTION,
    KEY_WEATHER_LAST_UPDATE,
    KEY_AIR_TEMPERATURE,
    KEY_WIND_SPEED,
    KEY_WIND_DIRECTION,
    KEY_WATER_TEMPERATURE,
    KEY_WATER_LAST_UPDATE,
    KEY_BUOY_LATITUDE,
    KEY_BUOY_LONGITUDE,
)
from .coordinator import KCLakesDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Define sensors for each lake. Adjust keys based on API and const.py
# Format: (key_in_api_data, name_suffix, unit, device_class, state_class, icon)
LAKE_SENSORS = [
    (
        KEY_WEATHER_LAST_UPDATE,
        "Weather Last Update",
        None,
        SensorDeviceClass.TIMESTAMP,
        SensorStateClass.MEASUREMENT,
        "mdi:clock-outline",
    ),
    (
        KEY_AIR_TEMPERATURE,
        "Air Temperature",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
        "mdi:thermometer",
    ),
    (
        KEY_WIND_SPEED,
        "Wind Speed",
        UnitOfSpeed.METERS_PER_SECOND,
        SensorDeviceClass.WIND_SPEED,
        SensorStateClass.MEASUREMENT,
        "mdi:weather-windy",
    ),
    (
        KEY_WIND_DIRECTION,
        "Wind Direction",
        None,
        None,
        None,
        "mdi:compass-outline",
    ),
    (
        KEY_WATER_TEMPERATURE,
        "Water Temperature",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
        "mdi:water-thermometer",
    ),
    (
        KEY_WATER_LAST_UPDATE,
        "Water Last Update",
        None,
        SensorDeviceClass.TIMESTAMP,
        SensorStateClass.MEASUREMENT,
        "mdi:clock-outline",
    ),
    (
        KEY_BUOY_LATITUDE,
        "Buoy Latitude",
        DEGREE,
        None,
        SensorStateClass.MEASUREMENT_ANGLE,
        "mdi:latitude",
    ),
    (
        KEY_BUOY_LONGITUDE,
        "Buoy Longitude",
        DEGREE,
        None,
        SensorStateClass.MEASUREMENT_ANGLE,
        "mdi:longitude",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator: KCLakesDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create sensors only after the first successful coordinator update
    @callback
    def _async_create_entities():
        """Create entities once coordinator data is available."""
        if not coordinator.last_update_success or not coordinator.data:
            _LOGGER.warning("Coordinator has no data, skipping sensor setup")
            return  # Don't create entities if the initial fetch failed

        new_entities = []
        # coordinator.data is expected to be a dict: {lake_name: lake_data_dict}
        for lake_name, lake_data in coordinator.data.items():
            _LOGGER.debug("Setting up sensors for lake: %s", lake_name)
            for (
                data_key,
                name_suffix,
                unit,
                dev_class,
                state_class,
                icon,
            ) in LAKE_SENSORS:
                if data_key in lake_data:  # Only create sensor if data exists
                    new_entities.append(
                        KCLakeSensor(
                            coordinator,
                            entry.entry_id,
                            lake_name,
                            data_key,
                            name_suffix,
                            unit,
                            dev_class,
                            state_class,
                            icon,
                        )
                    )
                else:
                    _LOGGER.debug(
                        "Data key '%s' not found for lake '%s'", data_key, lake_name
                    )

        if new_entities:
            _LOGGER.info("Adding %d King County Lake sensors", len(new_entities))
            async_add_entities(new_entities)
        else:
            _LOGGER.warning(
                "No sensors could be created. Check API response and LAKE_SENSORS definition."
            )

    # Check if data is already available (e.g., after HA restart)
    if coordinator.data:
        _async_create_entities()
    else:
        # Listen for the first successful update to create entities
        coordinator.async_add_listener(_async_create_entities)


class KCLakeSensor(CoordinatorEntity[KCLakesDataUpdateCoordinator], SensorEntity):
    """Representation of a King County Lake Buoy Sensor."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True  # Use "Platform Name Sensor Name" format

    def __init__(
        self,
        coordinator: KCLakesDataUpdateCoordinator,
        config_entry_id: str,
        lake_name: str,
        data_key: str,
        name_suffix: str,
        unit: Optional[str],
        device_class: Optional[SensorDeviceClass],
        state_class: Optional[SensorStateClass],
        icon: Optional[str],
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._lake_name = lake_name
        self._data_key = data_key

        # Entity Properties
        self._attr_unique_id = f"{config_entry_id}_{lake_name}_{data_key}"
        self._attr_name = name_suffix  # Will be combined with device name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon

        # Device Info: Groups sensors by lake
        self._attr_device_info = {
            "identifiers": {(DOMAIN, lake_name)},
            "name": lake_name,
            "manufacturer": "King County",
            "model": "Lake Buoy",
            "via_device": (
                DOMAIN,
                config_entry_id,
            ),  # Links device to the integration config entry
        }
        self._update_state()  # Set initial state

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Available if coordinator has data AND this specific lake's data is present
        return (
            super().available  # Checks coordinator status
            and self.coordinator.data is not None
            and self._lake_name in self.coordinator.data
            and self._data_key in self.coordinator.data[self._lake_name]
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data and self._lake_name in self.coordinator.data:
            self._update_state()
            self.async_write_ha_state()
        else:
            # Mark as unavailable if lake data disappears
            self._attr_native_value = None
            self.async_write_ha_state()

    def _update_state(self) -> None:
        """Update the sensor state from coordinator data."""
        lake_data = self.coordinator.data.get(self._lake_name, {})
        self._attr_native_value = lake_data.get(self._data_key)
