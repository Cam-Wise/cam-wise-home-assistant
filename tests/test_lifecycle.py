"""Prove platform, entry and listener behavior using the real HA lifecycle."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.helpers import entity_registry as er

from custom_components.cam_wise.diagnostics import async_get_config_entry_diagnostics

from .conftest import BASE_URL, DATA, MAPPING, STATUS


async def test_setup_reload_unload(hass, api, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    registry = er.async_get(hass)
    expected = {"status": "online", "review_queue": "3", "attention_required": "on"}
    ids = {}
    for key, value in expected.items():
        domain = "binary_sensor" if key == "attention_required" else "sensor"
        entity_id = registry.async_get_entity_id(
            domain, "cam_wise", f"{entry.unique_id}_{key}"
        )
        assert entity_id is not None
        ids[key] = entity_id
        assert hass.states.get(entity_id).state == value
    registry.async_update_entity(ids["status"], name="My existing status name")
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    for key, entity_id in ids.items():
        assert hass.states.get(entity_id).state == expected[key]
    assert registry.async_get(ids["status"]).name == "My existing status name"
    assert entry.data == DATA
    assert entry.options == {**MAPPING, "user_setting": "preserved"}
    # A state event after reload must be forwarded by exactly one listener.
    api.mock_calls.clear()
    hass.states.async_set(
        "sensor.front_recording", "ready", {"last_video_id": "new-media"}
    )
    await hass.async_block_till_done()
    event_url = f"{BASE_URL}/integrations/home-assistant/cam-wise/event"
    events = [request for request in api.mock_calls if str(request[1]) == event_url]
    assert len(events) == 1
    assert events[0][2]["media_identifier"] == "new-media"
    runtime = entry.runtime_data
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    api.mock_calls.clear()
    hass.states.async_set(
        "sensor.front_recording", "ready", {"last_video_id": "after-unload"}
    )
    await hass.async_block_till_done()
    assert api.call_count == 0
    assert runtime.route_unsub is None


async def test_options_trigger_reload(hass, api, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    old_runtime = entry.runtime_data
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"choose_entities": True}
    )
    hass.states.async_set("sensor.changed_recording", "unknown")
    await hass.config_entries.options.async_configure(
        result["flow_id"],
        {**MAPPING, "recording_entity_id": "sensor.changed_recording"},
    )
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data is not old_runtime
    assert old_runtime.route_unsub is None
    assert entry.options["user_setting"] == "preserved"
    assert entry.data == DATA
    api.mock_calls.clear()
    hass.states.async_set(
        "sensor.front_recording", "ready", {"last_video_id": "old-mapping"}
    )
    await hass.async_block_till_done()
    assert api.call_count == 0
    hass.states.async_set(
        "sensor.changed_recording", "ready", {"last_video_id": "new-mapping"}
    )
    await hass.async_block_till_done()
    assert any("cam-wise/event" in str(request[1]) for request in api.mock_calls)


@pytest.mark.parametrize("invalid", [False, True])
async def test_first_refresh_failure(hass, aioclient_mock, entry, invalid):
    if invalid:
        aioclient_mock.get(f"{BASE_URL}/integrations/home-assistant/status", json=[])
    else:
        aioclient_mock.get(f"{BASE_URL}/integrations/home-assistant/status", status=503)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert not er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)


async def test_offline_recovery(hass, api, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", "cam_wise", f"{entry.unique_id}_status"
    )
    api.clear_requests()
    api.get(f"{BASE_URL}/integrations/home-assistant/status", status=503)
    await entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    api.clear_requests()
    api.get(f"{BASE_URL}/integrations/home-assistant/status", json=STATUS)
    await entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "online"


async def test_failed_platform_setup_cleans_listener(hass, api, entry):
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        side_effect=RuntimeError("synthetic platform setup failure"),
    ):
        assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR
    api.mock_calls.clear()
    hass.states.async_set(
        "sensor.front_recording", "ready", {"last_video_id": "after-failed-setup"}
    )
    await hass.async_block_till_done()
    assert api.call_count == 0


async def test_failed_unload_keeps_listener(hass, api, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        new=AsyncMock(return_value=False),
    ):
        assert not await hass.config_entries.async_unload(entry.entry_id)
    api.mock_calls.clear()
    hass.states.async_set(
        "sensor.front_recording", "ready", {"last_video_id": "still-loaded"}
    )
    await hass.async_block_till_done()
    assert any("cam-wise/event" in str(request[1]) for request in api.mock_calls)
    assert entry.runtime_data.route_unsub is not None


async def test_diagnostics_redaction(hass, api, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["entry"]["data"]["host"] == "**REDACTED**"
    for key in MAPPING:
        assert result["entry"]["options"][key] == "**REDACTED**"
    assert result["status"] == STATUS
    assert "last_media_id" not in result["runtime"]


async def test_setup_persists_recommendation_for_unmapped_entry(
    hass, aioclient_mock, entry
):
    hass.config_entries.async_update_entry(entry, options={"user_setting": "preserved"})
    aioclient_mock.get(
        f"{BASE_URL}/integrations/home-assistant/status",
        json={**STATUS, "recommended_route_options": MAPPING},
    )
    aioclient_mock.post(
        f"{BASE_URL}/integrations/home-assistant/cam-wise/status", json={"ok": True}
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert entry.data == DATA
    assert entry.options == {**MAPPING, "user_setting": "preserved"}
    assert entry.runtime_data.diagnostics["mapping_origin"] == "cam_wise_recommendation"


async def test_diagnostics_omit_unknown_saved_options(hass, api, entry):
    hass.config_entries.async_update_entry(entry, options={**entry.options, "private_token": "synthetic-secret"})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert "private_token" not in result["entry"]["options"]
    assert "synthetic-secret" not in str(result)
    assert entry.options["private_token"] == "synthetic-secret"
