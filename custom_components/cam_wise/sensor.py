"""Cam-Wise sensors."""

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CamWiseConfigEntry
from .entity import CamWiseEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CamWiseConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            CamWiseStatusSensor(coordinator, entry),
            CamWiseReviewQueueSensor(coordinator, entry),
        ]
    )


class CamWiseStatusSensor(CamWiseEntity, SensorEntity):
    _attr_translation_key = "status"
    _attr_icon = "mdi:cctv"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "status")

    @property
    def native_value(self):
        return self.coordinator.data.get("status", "online")

    @property
    def extra_state_attributes(self):
        return {
            "version": self.coordinator.data.get("version"),
            "environment": self.coordinator.data.get("environment"),
            "api_version": self.coordinator.data.get("api_version"),
        }


class CamWiseReviewQueueSensor(CamWiseEntity, SensorEntity):
    _attr_translation_key = "review_queue"
    _attr_icon = "mdi:clipboard-text-clock"
    _attr_native_unit_of_measurement = "items"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "review_queue")

    @property
    def native_value(self):
        return int(self.coordinator.data.get("review_queue", 0))
