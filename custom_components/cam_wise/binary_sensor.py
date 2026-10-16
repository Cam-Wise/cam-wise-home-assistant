"""Cam-Wise binary sensors."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
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
    async_add_entities([CamWiseAttentionRequiredSensor(coordinator, entry)])


class CamWiseAttentionRequiredSensor(CamWiseEntity, BinarySensorEntity):
    _attr_translation_key = "attention_required"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "attention_required")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("attention_required", False))
