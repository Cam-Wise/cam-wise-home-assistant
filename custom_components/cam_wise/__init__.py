"""Cam-Wise Home Assistant custom integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import CamWiseApiClient
from .const import (
    CONF_CAMERA_ENTITY,
    CONF_DING_ENTITY,
    CONF_HOST,
    CONF_MOTION_ENTITY,
    CONF_PORT,
    CONF_RECORDING_ENTITY,
    PLATFORMS,
)
from .coordinator import CamWiseCoordinator
from .events import CamWiseEventHandler, mapping_errors


@dataclass
class CamWiseRuntimeData:
    """Runtime-only state for a Cam-Wise config entry."""

    client: CamWiseApiClient
    coordinator: CamWiseCoordinator
    events: CamWiseEventHandler | None = None
    route_unsub: Callable[[], None] | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)


type CamWiseConfigEntry = ConfigEntry[CamWiseRuntimeData]


def _route_options(entry: ConfigEntry) -> dict[str, str]:
    values = {**entry.data, **entry.options}
    return {
        "camera": str(values.get(CONF_CAMERA_ENTITY) or "").strip(),
        "motion": str(values.get(CONF_MOTION_ENTITY) or "").strip(),
        "ding": str(values.get(CONF_DING_ENTITY) or "").strip(),
        "recording_ready": str(values.get(CONF_RECORDING_ENTITY) or "").strip(),
    }


def _persist_recommended_route_options(
    hass: HomeAssistant, entry: ConfigEntry, status: dict[str, Any]
) -> tuple[dict[str, str], str]:
    """Repair an older entry only when every event mapping is still blank."""
    current = _route_options(entry)
    if any(current.values()):
        return current, "entry_options"

    recommended = status.get("recommended_route_options") or {}
    route_options = {
        "camera": str(recommended.get(CONF_CAMERA_ENTITY) or "").strip(),
        "motion": str(recommended.get(CONF_MOTION_ENTITY) or "").strip(),
        "ding": str(recommended.get(CONF_DING_ENTITY) or "").strip(),
        "recording_ready": str(recommended.get(CONF_RECORDING_ENTITY) or "").strip(),
    }
    if mapping_errors(route_options) or not route_options["camera"] or not any(
        route_options[kind] for kind in ("motion", "ding", "recording_ready")
    ):
        return current, "empty"

    options = dict(entry.options)
    options.update(
        {
            CONF_CAMERA_ENTITY: route_options["camera"],
            CONF_MOTION_ENTITY: route_options["motion"],
            CONF_DING_ENTITY: route_options["ding"],
            CONF_RECORDING_ENTITY: route_options["recording_ready"],
        }
    )
    hass.config_entries.async_update_entry(entry, options=options)
    return route_options, "cam_wise_recommendation"


async def async_setup_entry(hass: HomeAssistant, entry: CamWiseConfigEntry) -> bool:
    """Set up Cam-Wise from a config entry."""
    client = CamWiseApiClient(
        async_get_clientsession(hass), entry.data[CONF_HOST], entry.data[CONF_PORT]
    )
    coordinator = CamWiseCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()

    runtime_data = CamWiseRuntimeData(client=client, coordinator=coordinator)
    entry.runtime_data = runtime_data
    route_options, mapping_origin = _persist_recommended_route_options(
        hass, entry, coordinator.data or {}
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    handler = CamWiseEventHandler(hass, entry, route_options, mapping_origin)
    runtime_data.events = handler
    runtime_data.route_unsub = handler.start()
    entry.async_on_unload(handler.stop_listeners)
    await handler.async_report_status()
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CamWiseConfigEntry) -> bool:
    """Unload a Cam-Wise config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        runtime_data = entry.runtime_data
        if runtime_data.events is not None:
            await runtime_data.events.async_close()
        runtime_data.route_unsub = None
    return unloaded


async def _async_reload_entry(hass: HomeAssistant, entry: CamWiseConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
