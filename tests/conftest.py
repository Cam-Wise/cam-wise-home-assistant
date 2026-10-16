"""Real Home Assistant fixtures with synthetic Cam-Wise HTTP responses."""

import json
from pathlib import Path

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cam_wise.const import DOMAIN

BASE_URL = "http://cam-wise.test:8000"
DATA = {"host": "cam-wise.test", "port": 8000}
MAPPING = {
    "camera_entity_id": "camera.front",
    "motion_entity_id": "event.front_motion",
    "ding_entity_id": "event.front_ding",
    "recording_entity_id": "sensor.front_recording",
}


def fixture_payload(name):
    """Load reviewed synthetic public API examples."""
    return json.loads((Path(__file__).parent / "fixtures" / f"{name}.json").read_text())


STATUS = fixture_payload("status")
DISCOVERY = fixture_payload("discovery")


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Load the actual custom component through HA's loader."""


@pytest.fixture
def api(aioclient_mock):
    """Mock only the remote HTTP boundary, never HA classes."""
    aioclient_mock.get(f"{BASE_URL}/health", json={"status": "ok"})
    aioclient_mock.get(
        f"{BASE_URL}/integrations/home-assistant/discovery-info", json=DISCOVERY
    )
    aioclient_mock.get(f"{BASE_URL}/integrations/home-assistant/status", json=STATUS)
    aioclient_mock.post(
        f"{BASE_URL}/integrations/home-assistant/cam-wise/status", json={"ok": True}
    )
    aioclient_mock.post(
        f"{BASE_URL}/integrations/home-assistant/cam-wise/event",
        json={"ok": True, "result": "accepted"},
    )
    return aioclient_mock


@pytest.fixture
def entry(hass):
    """Create a real config entry with existing user settings."""
    hass.states.async_set("camera.front", "idle")
    hass.states.async_set("event.front_motion", "unknown", {"device_class": "motion"})
    hass.states.async_set("event.front_ding", "unknown", {"device_class": "doorbell"})
    hass.states.async_set("sensor.front_recording", "ready")
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Cam-Wise (test)",
        unique_id=DISCOVERY["device_id"],
        data=DATA,
        options={**MAPPING, "user_setting": "preserved"},
    )
    entry.add_to_hass(hass)
    return entry
