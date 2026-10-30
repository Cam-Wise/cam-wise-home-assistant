"""Strict conversion of Reolink device wall times using explicit device DST rules.

Never use the SDK tzinfo's fold handling or today's offset for a past recording.
"""

from __future__ import annotations

import calendar
import asyncio
import hashlib
import json
from datetime import datetime, timedelta, timezone

from homeassistant.util import dt as dt_util

CLOCK_MARGIN = 5.0


def _integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError("invalid_device_time_settings")
    return value


def _rule(data, prefix, year):
    month = _integer(data[prefix + "Mon"], 1, 12)
    week = _integer(data[prefix + "Week"], 1, 5)
    weekday = (_integer(data[prefix + "Weekday"], 0, 6) - 1) % 7
    days = [
        d
        for d in calendar.Calendar().itermonthdates(year, month)
        if d.month == month and d.weekday() == weekday
    ]
    day = days[-1] if week == 5 else days[week - 1]
    return datetime(
        year,
        month,
        day.day,
        _integer(data[prefix + "Hour"], 0, 23),
        _integer(data[prefix + "Min"], 0, 59),
        _integer(data[prefix + "Sec"], 0, 59),
    )


def offsets(settings):
    """Reolink timeZone is seconds west of UTC; DST rules use device wall time."""
    base = -_integer(settings["Time"]["timeZone"], -50400, 50400)
    dst = settings["Dst"]
    enabled = _integer(dst["enable"], 0, 1)
    shift = _integer(dst["offset"], 1, 2) * 3600 if enabled else 0
    if abs(base + shift) > 50400:
        raise ValueError("invalid_device_time_settings")
    return base, shift


def utc_candidates(wall, settings):
    """Zero candidates for a spring gap, two for an autumn fold, one otherwise."""
    if wall.tzinfo is not None:
        raise ValueError("device_wall_time_required")
    base, shift = offsets(settings)
    if not shift:
        return [(wall - timedelta(seconds=base)).replace(tzinfo=timezone.utc)]
    windows = []
    for year in (wall.year - 1, wall.year, wall.year + 1):
        start_wall = _rule(settings["Dst"], "start", year)
        end_wall = _rule(settings["Dst"], "end", year)
        start = start_wall - timedelta(seconds=base)
        end = end_wall - timedelta(seconds=base + shift)
        if start_wall == end_wall or start == end:
            raise ValueError("invalid_device_dst_rules")
        if end < start:  # Southern hemisphere: the season ends next year.
            end = _rule(settings["Dst"], "end", year + 1) - timedelta(
                seconds=base + shift
            )
        windows.append((start, end))
    result = []
    for offset in (base, base + shift):
        utc = wall - timedelta(seconds=offset)
        daylight = any(start <= utc < end for start, end in windows)
        if offset == base + (shift if daylight else 0):
            result.append(utc.replace(tzinfo=timezone.utc))
    return result


def clock_context(settings, wall, before, after):
    """Validate a fresh device clock read; network/detection times aren't capture times."""
    candidates = utc_candidates(wall.replace(tzinfo=None), settings)
    if not 0 <= after - before <= CLOCK_MARGIN:
        raise ValueError("recording_clock_unreliable")
    if not any(
        before - CLOCK_MARGIN <= t.timestamp() <= after + CLOCK_MARGIN
        for t in candidates
    ):
        raise ValueError("recording_clock_unreliable")
    basis = {"timeZone": settings["Time"]["timeZone"], "Dst": settings["Dst"]}
    return {
        "settings": settings,
        "capture_margin": 2 * CLOCK_MARGIN,
        "time_basis": hashlib.sha256(
            json.dumps(basis, sort_keys=True).encode()
        ).hexdigest()[:32],
    }


async def read_clock(hass, entry_id):
    from homeassistant.components.reolink.util import get_host

    api = get_host(hass, entry_id).api
    before = dt_util.utcnow().timestamp()
    # Existing SDK read-only GetTime operation. Its returned tzinfo is not trusted.
    async with asyncio.timeout(10):
        wall = await api.async_get_time()
    after = dt_util.utcnow().timestamp()
    # Both supported SDKs retain the raw GetTime response here. Missing/changed
    # SDK layout disables only this source, instead of guessing a timezone.
    settings = json.loads(json.dumps(api._time_settings))
    return clock_context(settings, wall, before, after)


def metadata(source, context):
    empty = {"captured_at": None, "ended_at": None, "completed": False}
    try:
        parts = source.removeprefix("media-source://reolink/").split("|")
        if len(parts) != 7 or parts[0] != "FILE":
            return {**empty, "timing_error": "recording_time_metadata_unavailable"}
        values = []
        for part in parts[-2:]:
            if len(part) != 14 or not part.isascii() or not part.isdigit():
                raise ValueError()
            options = utc_candidates(
                datetime.strptime(part, "%Y%m%d%H%M%S"), context["settings"]
            )
            if len(options) != 1:
                return {
                    **empty,
                    "timing_error": "recording_time_ambiguous"
                    if options
                    else "recording_time_nonexistent",
                }
            values.append(options[0].timestamp())
        start, end = values
        if not 0 < start < end <= dt_util.utcnow().timestamp():
            return {**empty, "timing_error": "recording_time_invalid"}
        return {
            "captured_at": start,
            "ended_at": end,
            "completed": True,
            "capture_margin": context.get("capture_margin", CLOCK_MARGIN),
        }
    except (KeyError, ValueError, TypeError, OverflowError):
        return {**empty, "timing_error": "recording_time_invalid"}
