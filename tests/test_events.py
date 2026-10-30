"""Event reliability with real HA state changes and entry lifecycle."""

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import Context
from homeassistant.util.dt import utcnow

from custom_components.cam_wise.client import (
    CamWiseConnectionError,
    CamWiseNotSentError,
)
from custom_components.cam_wise.events import MAX_PENDING

from .conftest import BASE_URL, MAPPING, STATUS

EVENT_URL = f"{BASE_URL}/integrations/home-assistant/cam-wise/event"


async def setup(hass, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry.runtime_data.events


def recording(hass, media):
    hass.states.async_set("sensor.front_recording", "ready", {"last_video_id": media})


def trigger(hass, role="motion", offset=0):
    hass.states.async_set(
        f"event.front_{role}",
        (utcnow() + timedelta(microseconds=offset)).isoformat(),
        {"event_type": role},
        context=Context(),
    )


def requests(api):
    return [request[2] for request in api.mock_calls if str(request[1]) == EVENT_URL]


async def test_simultaneous_media_are_serial_and_deduplicated(hass, api, entry):
    handler = await setup(hass, entry)
    started = asyncio.Event()
    release = asyncio.Event()
    active = 0
    peak = 0
    calls = []

    async def send(payload):
        nonlocal active, peak
        calls.append(dict(payload))
        active += 1
        peak = max(peak, active)
        started.set()
        await release.wait()
        active -= 1
        return {"ok": True, "result": "accepted", "accepted": True}

    with patch.object(handler.client, "async_send_event", side_effect=send):
        recording(hass, "one")
        await started.wait()
        recording(hass, "two")
        recording(hass, "one")
        release.set()
        await hass.async_block_till_done()
    assert peak == 1
    assert [call["media_identifier"] for call in calls] == ["one", "two"]
    assert handler.diagnostics["duplicate_count"] == 1
    assert not handler.tasks


async def test_burst_waits_fifo_for_later_media(hass, api, entry):
    handler = await setup(hass, entry)
    trigger(hass)
    trigger(hass, "ding")
    trigger(hass, offset=1)
    await hass.async_block_till_done()
    assert len(handler.pending) == 3
    assert not requests(api)
    for media in ("one", "two", "three"):
        recording(hass, media)
        await hass.async_block_till_done()
    assert [payload["trigger_type"] for payload in requests(api)] == [
        "motion",
        "ding",
        "motion",
    ]
    assert not handler.pending
    assert handler.diagnostics["accepted_count"] == 3
    assert handler.diagnostics["processed"] is None


async def test_pending_expires_without_new_event_and_cannot_claim_late_media(
    hass, api, entry
):
    handler = await setup(hass, entry)
    with patch("custom_components.cam_wise.events.PENDING_SECONDS", 0.01):
        trigger(hass)
        await hass.async_block_till_done()
        await asyncio.sleep(0.03)
        await hass.async_block_till_done()
    assert not handler.pending
    assert handler.timer is None
    assert handler.diagnostics["expired_count"] == 1
    recording(hass, "late")
    await hass.async_block_till_done()
    assert requests(api)[0]["trigger_type"] == "recording_ready"


async def test_duplicate_media_and_attributes_do_not_resend(hass, api, entry):
    handler = await setup(hass, entry)
    recording(hass, "one")
    await hass.async_block_till_done()
    hass.states.async_set(
        "sensor.front_recording",
        "ready",
        {"last_video_id": "one", "friendly_name": "New name"},
    )
    recording(hass, "two")
    recording(hass, "one")
    await hass.async_block_till_done()
    assert [payload["media_identifier"] for payload in requests(api)] == ["one", "two"]
    assert handler.recent["one"] == "accepted"


@pytest.mark.parametrize(
    "error,safe",
    [
        (CamWiseNotSentError("not connected"), True),
        (CamWiseConnectionError("response lost"), False),
    ],
)
async def test_network_loss_reconnect_only_retries_proven_not_sent(
    hass, api, entry, error, safe
):
    handler = await setup(hass, entry)
    with patch.object(handler.client, "async_send_event", side_effect=error) as send:
        recording(hass, "one")
        await hass.async_block_till_done()
        assert send.await_count == 1
    assert bool(handler.retries) is safe
    api.clear_requests()
    api.get(f"{BASE_URL}/integrations/home-assistant/status", status=503)
    await handler.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert handler.diagnostics["connected"] is False
    api.clear_requests()
    api.get(f"{BASE_URL}/integrations/home-assistant/status", json=STATUS)
    api.post(EVENT_URL, json={"ok": True, "accepted": True, "result": "accepted"})
    api.post(
        f"{BASE_URL}/integrations/home-assistant/cam-wise/status", json={"ok": True}
    )
    await handler.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert handler.diagnostics["connected"] is True
    assert len(requests(api)) == int(safe)
    assert not handler.retries


async def test_accepted_background_failure_is_not_completion_or_replayed(
    hass, api, entry
):
    handler = await setup(hass, entry)
    recording(hass, "one")
    await hass.async_block_till_done()
    # Aggregate desktop status cannot associate a failure with this accepted event.
    handler.coordinator.async_set_updated_data(
        {**STATUS, "status": "error", "attention_required": True}
    )
    recording(hass, "two")
    recording(hass, "one")
    await hass.async_block_till_done()
    assert [payload["media_identifier"] for payload in requests(api)] == ["one", "two"]
    assert handler.recent["one"] == "accepted"
    assert handler.diagnostics["processed"] is None


@pytest.mark.parametrize(
    "response,retry",
    [
        ({"ok": False, "accepted": False, "result": "error", "retryable": True}, True),
        (
            {"ok": False, "accepted": False, "result": "ignored", "retryable": False},
            False,
        ),
        ({"ok": True, "result": "duplicate", "accepted": False}, False),
        ({"ok": True}, False),
    ],
)
async def test_response_semantics(hass, api, entry, response, retry):
    handler = await setup(hass, entry)
    with patch.object(
        handler.client, "async_send_event", new=AsyncMock(return_value=response)
    ):
        recording(hass, "one")
        await hass.async_block_till_done()
    assert bool(handler.retries) is retry
    assert handler.diagnostics["accepted_count"] == 0
    assert handler.diagnostics["processed"] is None


async def test_retries_expire_and_are_attempt_bounded(hass, api, entry):
    handler = await setup(hass, entry)
    with patch.object(
        handler.client, "async_send_event", side_effect=CamWiseNotSentError()
    ) as send:
        recording(hass, "one")
        await hass.async_block_till_done()
        for _ in range(5):
            await handler.retry()
        assert send.await_count == 3
        assert not handler.retries
        recording(hass, "two")
        await hass.async_block_till_done()
        handler.retries["two"].expires = hass.loop.time() - 1
        await handler.retry()
        assert send.await_count == 4
    assert not handler.retries
    assert handler.diagnostics["expired_count"] == 1


async def test_unload_cancels_active_send_waiters_timer_and_listeners(hass, api, entry):
    handler = await setup(hass, entry)
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def send(payload):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    trigger(hass)
    await hass.async_block_till_done()
    assert handler.timer is not None
    with patch.object(handler.client, "async_send_event", side_effect=send):
        recording(hass, "one")
        await started.wait()
        recording(hass, "two")
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
    assert cancelled.is_set()
    assert not handler.tasks
    assert not handler.pending
    assert not handler.unsubs
    assert handler.timer is None
    assert handler.closed
    api.mock_calls.clear()
    recording(hass, "three")
    await hass.async_block_till_done()
    assert not api.mock_calls


@pytest.mark.parametrize(
    "changes",
    [
        {"camera_entity_id": ""},
        {"ding_entity_id": MAPPING["motion_entity_id"]},
        {"motion_entity_id": "sensor.front_recording"},
    ],
)
async def test_invalid_saved_mapping_does_not_forward_or_rewrite(
    hass, api, entry, changes
):
    options = {**entry.options, **changes}
    hass.config_entries.async_update_entry(entry, options=options)
    handler = await setup(hass, entry)
    trigger(hass)
    recording(hass, "one")
    await hass.async_block_till_done()
    assert handler.diagnostics["mapping_errors"]
    assert not requests(api)
    assert entry.options == options


async def test_missing_camera_does_not_forward(hass, api, entry):
    await setup(hass, entry)
    hass.states.async_remove("camera.front")
    recording(hass, "one")
    await hass.async_block_till_done()
    assert not requests(api)


@pytest.mark.parametrize(
    "state", ["unknown", "unavailable", "off", "garbage", "2020-01-01T00:00:00+00:00"]
)
async def test_invalid_event_states_are_ignored(hass, api, entry, state):
    handler = await setup(hass, entry)
    hass.states.async_set("event.front_motion", state)
    hass.states.async_remove("event.front_ding")
    await hass.async_block_till_done()
    assert not handler.pending
    assert not requests(api)


async def test_binary_sensor_only_off_to_on_and_event_attribute_changes_ignored(
    hass, api, entry
):
    hass.states.async_set("binary_sensor.motion", "off")
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, "motion_entity_id": "binary_sensor.motion"}
    )
    handler = await setup(hass, entry)
    hass.states.async_set("binary_sensor.motion", "on")
    hass.states.async_set("binary_sensor.motion", "on", {"friendly_name": "Changed"})
    hass.states.async_set("binary_sensor.motion", "off")
    trigger(hass, "ding")
    state = hass.states.get("event.front_ding")
    hass.states.async_set(
        "event.front_ding",
        state.state,
        {"event_type": "ding", "friendly_name": "Changed"},
    )
    await hass.async_block_till_done()
    assert [item.payload["trigger_type"] for item in handler.pending] == [
        "motion",
        "ding",
    ]


async def test_restart_uses_existing_media_as_baseline(hass, api, entry):
    await setup(hass, entry)
    recording(hass, "one")
    await hass.async_block_till_done()
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    api.mock_calls.clear()
    recording(hass, "two")
    recording(hass, "one")
    await hass.async_block_till_done()
    assert [payload["media_identifier"] for payload in requests(api)] == ["two"]


async def test_burst_bound_is_explicit_not_silent_overwrite(hass, api, entry):
    handler = await setup(hass, entry)
    for offset in range(MAX_PENDING + 2):
        trigger(hass, offset=offset)
        await hass.async_block_till_done()
    assert len(handler.pending) == MAX_PENDING
    assert handler.diagnostics["overflow_count"] == 2
    assert handler.diagnostics["received_count"] == MAX_PENDING + 2


async def test_safe_retry_timer_operates_without_another_state_event(hass, api, entry):
    handler = await setup(hass, entry)
    with patch.object(
        handler.client, "async_send_event", side_effect=CamWiseNotSentError()
    ):
        recording(hass, "one")
        await hass.async_block_till_done()
    handler.retries["one"].retry_at = hass.loop.time()
    handler.schedule_expiry()
    await asyncio.sleep(0)
    await hass.async_block_till_done()
    assert len(requests(api)) == 1
    assert not handler.retries
    assert handler.timer is None


async def test_old_trigger_uses_remaining_lifetime_not_fresh_two_minutes(
    hass, api, entry
):
    handler = await setup(hass, entry)
    hass.states.async_set(
        "event.front_motion", (utcnow() - timedelta(seconds=119)).isoformat()
    )
    await hass.async_block_till_done()
    assert len(handler.pending) == 1
    assert handler.pending[0].expires - hass.loop.time() < 2


async def test_unchanged_trigger_media_does_not_claim_old_recording(hass, api, entry):
    hass.states.async_set("event.front_motion", "unknown", {"last_video_id": "old"})
    handler = await setup(hass, entry)
    hass.states.async_set(
        "event.front_motion", utcnow().isoformat(), {"last_video_id": "old"}
    )
    await hass.async_block_till_done()
    assert len(handler.pending) == 1
    assert not requests(api)


async def test_expiry_of_older_event_behind_fresh_event_preserves_fifo(
    hass, api, entry
):
    handler = await setup(hass, entry)
    trigger(hass)
    trigger(hass, "ding")
    await hass.async_block_till_done()
    handler.pending[1].expires = hass.loop.time() - 1
    await handler.retry(send=False)
    assert [item.payload["trigger_type"] for item in handler.pending] == ["motion"]
    assert handler.diagnostics["expired_count"] == 1


async def test_server_accepts_but_response_is_lost_no_blind_retry(hass, api, entry):
    handler = await setup(hass, entry)
    server_accepted = []

    async def accept_then_disconnect(payload):
        server_accepted.append(dict(payload))
        raise CamWiseConnectionError("accepted remotely, response lost")

    with patch.object(
        handler.client, "async_send_event", side_effect=accept_then_disconnect
    ) as send:
        recording(hass, "one")
        await hass.async_block_till_done()
        await handler.retry()
        handler.connection_changed()
        recording(hass, "two")
        recording(hass, "one")
        await hass.async_block_till_done()
        assert send.await_count == 2
    assert [item["media_identifier"] for item in server_accepted] == ["one", "two"]
    assert handler.recent["one"] == "delivery_unknown"
    assert handler.diagnostics["accepted_count"] == 0
    assert handler.diagnostics["processed"] is None


@pytest.mark.parametrize("result", [{"token": "synthetic-secret", "media_identifier": "synthetic-private-media"}, "synthetic-secret"])
async def test_untrusted_result_values_are_not_exported(hass, api, entry, result):
    from custom_components.cam_wise.diagnostics import async_get_config_entry_diagnostics
    handler = await setup(hass, entry)
    with patch.object(handler.client, "async_send_event", return_value={"ok": False, "result": result}):
        recording(hass, "one")
        await hass.async_block_till_done()
    exported = await async_get_config_entry_diagnostics(hass, entry)
    assert handler.diagnostics["forward_response"] == "unknown_response"
    assert "synthetic-secret" not in str(exported)
    assert "synthetic-private-media" not in str(exported)
    assert not handler.retries


async def test_snapshot_only_motion_forwards_without_recording_wait(hass, api, entry):
    hass.config_entries.async_update_entry(entry, options={**MAPPING, "recording_entity_id": ""})
    handler = await setup(hass, entry)
    trigger(hass)
    await hass.async_block_till_done()
    assert not handler.pending
    assert len(requests(api)) == 1
    assert requests(api)[0]["media_identifier"].startswith("snapshot:")
    trigger(hass, offset=1)
    await hass.async_block_till_done()
    assert len(requests(api)) == 2
