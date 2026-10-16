"""Shared Cam-Wise entity model."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import base_url
from .const import CONF_HOST, CONF_PORT, DOMAIN


class CamWiseEntity(CoordinatorEntity):
    """Base entity belonging to one Cam-Wise installation."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key: str) -> None:
        super().__init__(coordinator)
        device_id = str(entry.unique_id)
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name="Cam-Wise",
            manufacturer="Cam-Wise",
            model="Cam-Wise local runtime",
            sw_version=str(coordinator.data.get("version") or "unknown"),
            configuration_url=(
                f"{base_url(entry.data[CONF_HOST], entry.data[CONF_PORT])}/ui"
            ),
        )
