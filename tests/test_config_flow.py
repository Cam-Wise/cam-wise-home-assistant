"""Exercise config and options flows through Home Assistant's flow managers."""

from ipaddress import ip_address

import pytest
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    SOURCE_USER,
    SOURCE_ZEROCONF,
)
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from custom_components.cam_wise.const import DOMAIN

from .conftest import BASE_URL, DATA, DISCOVERY, MAPPING, STATUS


async def test_user_setup(hass, api):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": "http://cam-wise.test/", "port": 8000}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == DATA
    assert result["result"].unique_id == DISCOVERY["device_id"]
    await hass.async_block_till_done()


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ({"api_version": "2"}, "unsupported_api_version"),
        ({"product": "Other"}, "cannot_connect"),
    ],
)
async def test_invalid_discovery(hass, aioclient_mock, payload, error):
    aioclient_mock.get(f"{BASE_URL}/health", json={"status": "ok"})
    aioclient_mock.get(
        f"{BASE_URL}/integrations/home-assistant/discovery-info",
        json={**DISCOVERY, **payload},
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=DATA
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}


async def test_connection_failure(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/health", status=503)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=DATA
    )
    assert result["errors"] == {"base": "cannot_connect"}
    hass.config_entries.flow.async_abort(result["flow_id"])


async def test_duplicate_user(hass, api, entry):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=DATA
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_zeroconf_confirm(hass, aioclient_mock):
    url = "http://192.0.2.10:8000"
    aioclient_mock.get(f"{url}/health", json={"status": "ok"})
    aioclient_mock.get(
        f"{url}/integrations/home-assistant/discovery-info", json=DISCOVERY
    )
    info = ZeroconfServiceInfo(
        ip_address=ip_address("192.0.2.10"),
        ip_addresses=[ip_address("192.0.2.10")],
        hostname="cam-wise.test.",
        name="Cam-Wise._camwise._tcp.local.",
        type="_camwise._tcp.local.",
        port=8000,
        properties={},
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=info
    )
    assert result["step_id"] == "confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"host": "192.0.2.10", "port": 8000}
    await hass.async_block_till_done()


@pytest.mark.parametrize("same_device", [True, False])
async def test_reconfigure(hass, api, entry, same_device):
    url = "http://moved.test:8010"
    api.get(f"{url}/health", json={"status": "ok"})
    api.get(
        f"{url}/integrations/home-assistant/discovery-info",
        json={
            **DISCOVERY,
            "device_id": entry.unique_id if same_device else "another-device",
        },
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
        data={"host": "moved.test", "port": 8010},
    )
    if same_device:
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        assert entry.data == {"host": "moved.test", "port": 8010}
    else:
        assert result["errors"] == {"base": "different_device"}
        assert entry.data == DATA
    assert entry.options == {**MAPPING, "user_setting": "preserved"}
    assert entry.unique_id == DISCOVERY["device_id"]
    await hass.async_block_till_done()


async def test_options_recommended(hass, api, entry):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"use_recommended": True, "choose_entities": False}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {**MAPPING, "user_setting": "preserved"}
    assert entry.data == DATA
    assert entry.unique_id == DISCOVERY["device_id"]


async def test_options_advanced(hass, api, entry):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"choose_entities": True}
    )
    assert result["step_id"] == "advanced"
    assert result["data_schema"]({}) == MAPPING
    hass.states.async_set("event.other_motion", "unknown")
    changed = {**MAPPING, "motion_entity_id": " event.other_motion "}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], changed
    )
    assert result["data"]["motion_entity_id"] == "event.other_motion"
    assert entry.data == DATA


@pytest.mark.parametrize("recommendation", [True, False])
async def test_options_without_saved_mapping(
    hass, aioclient_mock, entry, recommendation
):
    hass.config_entries.async_update_entry(entry, options={})
    aioclient_mock.get(
        f"{BASE_URL}/integrations/home-assistant/status",
        json={**STATUS, "recommended_route_options": MAPPING if recommendation else {}},
    )
    if not recommendation:
        hass.states.async_set("camera.front", "idle", {"friendly_name": "Front camera"})
        hass.states.async_set(
            "event.front_motion", "unknown", {"device_class": "motion"}
        )
        hass.states.async_set("event.front_ding", "unknown", {"event_type": "doorbell"})
        hass.states.async_set(
            "sensor.front_recording", "ready", {"last_video_id": "synthetic"}
        )
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["step_id"] == "init"
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["data"] == MAPPING


@pytest.mark.parametrize("change", [
    {"motion_entity_id": "event.does_not_exist"},
    {"motion_entity_id": "sensor.front_recording"},
    {"ding_entity_id": MAPPING["motion_entity_id"]},
    {"camera_entity_id": ""},
])
async def test_options_reject_invalid_mapping_without_losing_settings(hass, api, entry, change):
    before = dict(entry.options)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"choose_entities": True})
    result = await hass.config_entries.options.async_configure(result["flow_id"], {**MAPPING, **change})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "advanced"
    assert result["errors"]
    assert entry.options == before
    hass.config_entries.options.async_abort(result["flow_id"])


async def test_suggestion_does_not_map_unrelated_entity_to_event_roles(hass, api, entry):
    hass.config_entries.async_update_entry(entry, options={})
    hass.states.async_remove("event.front_motion")
    hass.states.async_remove("event.front_ding")
    hass.states.async_remove("sensor.front_recording")
    hass.states.async_set("binary_sensor.front_battery", "on", {"device_id": "front"})
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["step_id"] == "advanced"
    hass.config_entries.options.async_abort(result["flow_id"])
