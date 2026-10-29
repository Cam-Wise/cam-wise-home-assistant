"""Actual time rules and mixed-version boundaries; synthetic cameras only."""

from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

import pytest
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from custom_components.cam_wise import reolink_time as rt
from custom_components.cam_wise.const import DOMAIN


@pytest.fixture
def settings():
    return {
        "Time": {"timeZone": -3600},
        "Dst": {
            "enable": 1,
            "offset": 1,
            "startMon": 3,
            "startWeek": 5,
            "startWeekday": 0,
            "startHour": 2,
            "startMin": 0,
            "startSec": 0,
            "endMon": 10,
            "endWeek": 5,
            "endWeekday": 0,
            "endHour": 3,
            "endMin": 0,
            "endSec": 0,
        },
    }


@pytest.mark.parametrize(
    "wall,expected",
    [
        ("2026-10-25T01:30:00", ["2026-10-24T23:30:00+00:00"]),
        (
            "2026-10-25T02:30:00",
            ["2026-10-25T01:30:00+00:00", "2026-10-25T00:30:00+00:00"],
        ),
        ("2026-10-25T03:30:00", ["2026-10-25T02:30:00+00:00"]),
        ("2026-03-29T01:30:00", ["2026-03-29T00:30:00+00:00"]),
        ("2026-03-29T02:30:00", []),
        ("2026-03-29T03:30:00", ["2026-03-29T01:30:00+00:00"]),
        (
            "2025-10-26T02:30:00",
            ["2025-10-26T01:30:00+00:00", "2025-10-26T00:30:00+00:00"],
        ),
    ],
)
def test_real_calendar_transition_rules(settings, wall, expected):
    assert [
        v.isoformat() for v in rt.utc_candidates(datetime.fromisoformat(wall), settings)
    ] == expected


@pytest.mark.parametrize(
    "start,end,error",
    [
        ("20261025023000", "20261025023100", "recording_time_ambiguous"),
        ("20260329023000", "20260329023100", "recording_time_nonexistent"),
        ("20261025015959", "20261025023000", "recording_time_ambiguous"),
        ("20260230023000", "20260230023100", "recording_time_invalid"),
    ],
)
def test_individual_ambiguous_or_invalid_recording_is_marked(
    settings, start, end, error
):
    row = rt.metadata(
        f"media-source://reolink/FILE|entry|0|sub|file|{start}|{end}",
        {"settings": settings},
    )
    assert row["timing_error"] == error and row["captured_at"] is None


def test_recording_offset_is_historical_not_current(settings):
    summer = rt.utc_candidates(datetime(2026, 7, 1, 10), settings)[0]
    winter = rt.utc_candidates(datetime(2026, 1, 1, 10), settings)[0]
    assert summer.hour == 8 and winter.hour == 9


def test_southern_hemisphere_crosses_year(settings):
    settings["Time"]["timeZone"] = -36000
    settings["Dst"].update(startMon=10, startWeek=1, endMon=4, endWeek=1)
    assert rt.utc_candidates(datetime(2026, 1, 1, 12), settings)[0].hour == 1
    assert rt.utc_candidates(datetime(2026, 7, 1, 12), settings)[0].hour == 2


@pytest.mark.parametrize(
    "change",
    [
        lambda s: s["Time"].pop("timeZone"),
        lambda s: s["Time"].update(timeZone=999999),
        lambda s: s["Dst"].update(startWeek=0),
        lambda s: s["Dst"].update(endMon=13),
        lambda s: s["Dst"].update(enable=True),
    ],
)
def test_missing_or_invalid_zone_is_structural(settings, change):
    change(settings)
    with pytest.raises((ValueError, KeyError)):
        rt.clock_context(settings, datetime(2026, 10, 28, 10), 1793178000, 1793178001)


@pytest.mark.parametrize("skew", [-3600, -60, 60, 3600])
def test_device_clock_skew_is_rejected(settings, skew):
    wall = datetime(2026, 10, 28, 10)
    actual = datetime(2026, 10, 28, 9, tzinfo=timezone.utc).timestamp()
    with pytest.raises(ValueError, match="clock_unreliable"):
        rt.clock_context(settings, wall, actual + skew, actual + skew + 1)


def test_equal_dst_rules_are_not_a_timezone(settings):
    settings["Dst"].update(endMon=3, endWeek=5, endHour=2)
    with pytest.raises(ValueError, match="dst_rules"):
        rt.utc_candidates(datetime(2026, 10, 28, 10), settings)


def test_future_or_reversed_file_time_is_skipped(settings):
    for start, end in (
        ("20990101100000", "20990101100100"),
        ("20261028100100", "20261028100000"),
    ):
        row = rt.metadata(
            f"media-source://reolink/FILE|entry|0|sub|file|{start}|{end}",
            {"settings": settings},
        )
        assert row["timing_error"] == "recording_time_invalid"


def test_camera_zone_mismatch_is_not_fixed_with_server_timezone(settings):
    settings["Time"]["timeZone"] = -7200
    actual = datetime(2026, 10, 28, 9, tzinfo=timezone.utc).timestamp()
    with pytest.raises(ValueError, match="clock_unreliable"):
        rt.clock_context(settings, datetime(2026, 10, 28, 10), actual, actual + 1)


async def test_clock_read_uses_raw_rules_not_sdk_offset(hass, monkeypatch, settings):
    from homeassistant.components.reolink import util

    wall = datetime(
        2026, 10, 28, 10, tzinfo=timezone.utc
    )  # Deliberately wrong SDK tzinfo.
    api = NS(
        _time_settings=deepcopy(settings), async_get_time=AsyncMock(return_value=wall)
    )
    monkeypatch.setattr(util, "get_host", lambda *a: NS(api=api))
    monkeypatch.setattr(
        rt.dt_util, "utcnow", lambda: datetime(2026, 10, 28, 9, tzinfo=timezone.utc)
    )
    context = await rt.read_clock(hass, "entry")
    assert context["capture_margin"] == 10
    assert len(context["time_basis"]) == 32
    api.async_get_time.assert_awaited_once()


@pytest.mark.parametrize(
    "contract,header,allowed",
    [
        (2, "2", True),
        (None, "2", False),
        (1, "2", False),
        (2, None, False),
        (2, "1", False),
        (True, "2", False),
    ],
)
async def test_recording_bridge_checks_both_sides(
    hass, hass_client, entry, api, monkeypatch, contract, header, allowed
):
    from custom_components.cam_wise import recordings

    await async_setup_component(hass, "http", {})
    hass.config_entries.async_update_entry(
        entry, data={**entry.data, "pairing_token": "synthetic-contract"}
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    entry.runtime_data.client.async_status = AsyncMock(
        return_value={"recording_contract": contract}
    )
    reader = AsyncMock(return_value={"recordings": [], "provider": "ring"})
    monkeypatch.setattr(recordings, "async_list_recordings", reader)
    headers = {"Authorization": "Bearer synthetic-contract"}
    if header is not None:
        headers["X-Cam-Wise-Recording-Contract"] = header
    response = await (await hass_client()).get(
        "/api/cam_wise_bridge/api/recordings/camera.front", headers=headers
    )
    assert response.status == (200 if allowed else 409)
    payload = await response.json()
    if allowed:
        assert payload["recording_contract"] == 2
    else:
        assert payload["error"] == "desktop_recording_update_required"
        assert "Update" in payload["message_en"] and "Werk" in payload["message_nl"]
        assert not reader.called


async def test_old_desktop_gets_actionable_repair_without_losing_pairing(
    hass, entry, api
):
    hass.config_entries.async_update_entry(
        entry, data={**entry.data, "pairing_token": "synthetic-contract"}
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    entry.runtime_data.client.async_status = AsyncMock(
        return_value={"api_version": "1", "status": "online"}
    )
    await entry.runtime_data.coordinator.async_refresh()
    assert ir.async_get(hass).async_get_issue(
        DOMAIN, "recording_desktop_update_" + entry.entry_id
    )
    assert entry.data["pairing_token"] == "synthetic-contract"
    assert entry.options["camera_entity_id"] == "camera.front"
