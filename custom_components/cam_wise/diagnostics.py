"""Diagnostics support for Cam-Wise."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import CamWiseConfigEntry
from .const import (
    CONF_CAMERA_ENTITY,
    CONF_DING_ENTITY,
    CONF_HOST,
    CONF_MOTION_ENTITY,
    CONF_PORT,
    CONF_RECORDING_ENTITY,
)

TO_REDACT = {
    CONF_HOST,
    CONF_CAMERA_ENTITY,
    CONF_MOTION_ENTITY,
    CONF_PORT,
    CONF_DING_ENTITY,
    CONF_RECORDING_ENTITY,
}

STATUS_KEYS = (
    "api_version",
    "version",
    "environment",
    "status",
    "review_queue",
    "attention_required",
)

RUNTIME_DIAGNOSTIC_KEYS = (
    "received_count",
    "forwarded_count",
    "accepted_count",
    "processed",
    "pending_count",
    "retry_count",
    "expired_count",
    "overflow_count",
    "duplicate_count",
    "uncertain_count",
    "mapping_errors",
    "version",
    "connected",
    "mapping_origin",
    "integration_loaded",
    "listeners_registered",
    "listener_type",
    "motion_listener_registered",
    "ding_listener_registered",
    "recording_listener_registered",
    "media_listener_registered",
    "unsubscribe_handle_present",
    "registered_after_restart",
    "last_trace_step",
    "context_id_present",
    "media_wait_started",
    "media_ready_detected",
    "new_media_detected",
    "forward_started",
    "forward_response",
    "error_code",
    "error_stage",
    "exception_type",
    "retryable",
)


def _configured_route_flags(entry: CamWiseConfigEntry) -> dict[str, bool]:
    values = {**entry.data, **entry.options}
    return {
        "camera": bool(values.get(CONF_CAMERA_ENTITY)),
        "motion": bool(values.get(CONF_MOTION_ENTITY)),
        "ding": bool(values.get(CONF_DING_ENTITY)),
        "recording_ready": bool(values.get(CONF_RECORDING_ENTITY)),
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: CamWiseConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime_data = getattr(entry, "runtime_data", None)
    coordinator = getattr(runtime_data, "coordinator", None)
    coordinator_data = getattr(coordinator, "data", None) or {}
    runtime_diagnostics = getattr(runtime_data, "diagnostics", {}) or {}

    return {
        "entry": {
            "data": async_redact_data(
                {
                    key: value
                    for key, value in entry.data.items()
                    if key in TO_REDACT | {CONF_PORT}
                },
                TO_REDACT,
            ),
            "options": async_redact_data(
                {
                    key: value
                    for key, value in entry.options.items()
                    if key in TO_REDACT
                },
                TO_REDACT,
            ),
            "route_configured": _configured_route_flags(entry),
        },
        "runtime": {
            key: runtime_diagnostics.get(key)
            for key in RUNTIME_DIAGNOSTIC_KEYS
            if key in runtime_diagnostics
        },
        "status": {
            key: coordinator_data.get(key)
            for key in STATUS_KEYS
            if key in coordinator_data
        },
    }
