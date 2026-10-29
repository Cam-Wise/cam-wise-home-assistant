"""Bounded recording reads for the camera explicitly selected in this HA entry.

Vendor credentials and resolved URLs stay in Home Assistant. This is not a
general media browser, URL proxy, live stream or background recording poller.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
import math
from datetime import datetime
from homeassistant.util import dt as dt_util
from urllib.parse import urljoin, urlsplit

from aiohttp import ClientTimeout, web
from homeassistant.components import media_source
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

MAX_BYTES = 1024 * 1024 * 1024
CACHE_KEY = "cam_wise_recording_reads"
ID_RE = re.compile(r"^[a-f0-9]{32}$")


def _camera(hass, selected):
    registered = er.async_get(hass).async_get(selected)
    if registered is None or registered.platform not in {"reolink", "ring", "unifiprotect", "tapo_control", "blink"}:
        raise web.HTTPBadRequest(reason="recording_provider_not_supported")
    return registered


def _remember(hass, entry, selected, provider, identity, source, title, revision=None, timing=None):
    cache = hass.data.setdefault(CACHE_KEY, {})
    now = hass.loop.time()
    for key, value in list(cache.items()):
        if value["expires"] <= now:
            del cache[key]
    while len(cache) >= 256:
        del cache[next(iter(cache))]
    identifier = hashlib.sha256((repr(identity) + source).encode()).hexdigest()[:32]
    cache[(entry.entry_id, selected, identifier)] = {
        "provider": provider, "identity": identity, "source": source,
        "expires": now + 900,
    }
    logical = source
    if provider == "reolink":
        parts = source.removeprefix("media-source://reolink/").split("|")
        # Channel/stream/start identify a recording, independent of its growing end.
        if len(parts) != 7 or parts[0] != "FILE":
            raise web.HTTPBadRequest(reason="recording_identity_unavailable")
        logical = "|".join(parts[1:4] + [parts[-2]])
    elif provider == "tapo_control":
        day, start, _end = json.loads(source)
        logical = json.dumps([day, start])
    elif provider == "blink":
        logical = urlsplit(source).path + "|" + str(title)
        if revision is None:
            revision = logical  # Signed access-token renewal is not new footage.
    stable_key = hashlib.sha256((repr(identity) + provider + logical).encode()).hexdigest()[:32]
    version = hashlib.sha256(str(revision if revision is not None else source).encode()).hexdigest()[:32]
    return {"id": identifier, "key": stable_key, "revision": version, "title": str(title)[:160],
            **(timing or {"captured_at": None, "ended_at": None, "completed": False})}


def _epoch(value):
    """Accept UTC epoch seconds or timezone-aware vendor datetimes; never local labels."""
    try:
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return None
            value = value.timestamp()
        if type(value) not in (float, int) or not math.isfinite(value):
            return None
        return float(value) if 0 < value <= dt_util.utcnow().timestamp() else None
    except (ValueError, OverflowError, TypeError):
        return None


def timing(start, end=None, *, completed=False):
    start, end = _epoch(start), _epoch(end)
    return {"captured_at": start, "ended_at": end,
            "completed": bool(start and (completed or end and start < end))}


def _reolink_timing(hass, entry_id, source, context=None):
    from .reolink_time import metadata
    return metadata(source, context or {})


def _ring_timing(hass, selected, video_id):
    from .recording_providers import entity
    try:
        event = entity(hass, selected)._last_event or {}
        if str(event.get("id")) != str(video_id):
            return timing(None)
        return timing(event.get("created_at"),
                      completed=(event.get("recording") or {}).get("status") == "ready")
    except (AttributeError, web.HTTPException):
        return timing(None)


async def async_list_recordings(hass, entry, selected, day=""):
    registered = _camera(hass, selected)
    if day and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise web.HTTPBadRequest(reason="invalid_recording_date")
    identity = (registered.config_entry_id, registered.device_id, registered.unique_id)
    if registered.platform in {"unifiprotect", "tapo_control", "blink"}:
        from .recording_providers import list_sources
        sources = await list_sources(hass, registered, selected)
        return {"provider": registered.platform, "days": [], "day": "",
                "availability": "available" if sources else "no_recordings",
                "recordings": [_remember(hass, entry, selected, registered.platform,
                               identity, row[0], row[1], row[2] if len(row) > 2 else None,
                               row[3] if len(row) > 3 else None) for row in sources]}
    if registered.platform == "ring":
        state = hass.states.get(selected)
        attrs = state.attributes if state else {}
        video_id = attrs.get("last_video_id")
        records = []
        if video_id is not None and attrs.get("video_url"):
            records.append(_remember(hass, entry, selected, "ring", identity,
                           "ring:" + str(video_id), "Latest Ring recording",
                           timing=_ring_timing(hass, selected, video_id)))
        return {"provider": "ring", "recordings": records, "days": [], "day": "",
                "availability": "latest_only" if records else "enable_last_recording_and_subscription"}

    root = await media_source.async_browse_media(hass, "media-source://reolink")
    registry = er.async_get(hass)
    choices = []
    for node in root.children or []:
        parts = str(node.identifier or "").split("|")
        if len(parts) != 3 or parts[:2] != ["CAM", registered.config_entry_id]:
            continue
        thumbnail = str(node.thumbnail or "").split("?", 1)[0]
        other = registry.async_get(thumbnail.removeprefix("/api/camera_proxy/"))
        if thumbnail == "/api/camera_proxy/" + selected:
            choices = [node]
            break
        if other and registered.device_id and other.device_id == registered.device_id:
            # Different resolution entities may represent the same camera channel.
            own_channel = registered.unique_id.split("_")[1:2]
            if own_channel == [parts[2]]:
                choices.append(node)
    if len(choices) != 1:
        return {"provider": "reolink", "recordings": [], "days": [], "day": "",
                "availability": "no_recording_storage_or_camera_mapping"}
    resolutions = await media_source.async_browse_media(hass, choices[0].media_content_id)
    expected_prefix = "RES|" + choices[0].identifier.removeprefix("CAM|") + "|"
    resolution = next((n for n in resolutions.children or []
                       if n.identifier == expected_prefix + "sub"), None)
    if resolution is None:
        raise web.HTTPBadRequest(reason="download_resolution_unavailable")
    dates = await media_source.async_browse_media(hass, resolution.media_content_id)
    valid_days = {}
    for node in dates.children or []:
        parts = str(node.identifier or "").split("|")
        if len(parts) == 7 and parts[:4] == ["DAY", registered.config_entry_id,
                                            choices[0].identifier.split("|")[2], "sub"]:
            try:
                from datetime import date
                date_key = date(*map(int, parts[4:])).isoformat()
            except ValueError:
                continue
            valid_days[date_key] = node
    ordered_days = sorted(valid_days, reverse=True)[:32]
    chosen = day or (ordered_days[0] if ordered_days else "")
    records = []
    clock = {}
    if chosen in valid_days:
        files = await media_source.async_browse_media(hass, valid_days[chosen].media_content_id)
        prefix = "FILE|" + choices[0].identifier.removeprefix("CAM|") + "|sub|"
        playable = [n for n in files.children or [] if n.can_play and
                    str(n.identifier or "").startswith(prefix) and
                    str(n.media_content_id).startswith("media-source://reolink/")]
        if any(len(str(n.identifier).split("|")) != 7 for n in playable):
            return {"provider": "reolink", "recordings": [], "days": ordered_days,
                    "day": chosen, "availability": "reolink_time_metadata_unavailable"}
        if playable:
            from .reolink_time import read_clock
            try:
                clock = await read_clock(hass, registered.config_entry_id)
            except Exception:
                return {"provider": "reolink", "recordings": [], "days": ordered_days,
                        "day": chosen, "availability": "recording_clock_unreliable"}
        for node in sorted(playable, key=lambda n: n.identifier.split("|")[-2], reverse=True)[:100]:
            records.append(_remember(hass, entry, selected, "reolink", identity,
                                     node.media_content_id, chosen + " · " + node.title,
                                     timing=_reolink_timing(hass, registered.config_entry_id, node.media_content_id, clock)))
    return {"provider": "reolink", "recordings": records, "days": ordered_days,
            "day": chosen, "availability": "available" if records else "no_recordings",
            "time_basis": clock.get("time_basis", "")}


def _ring_recording_url(value):
    """Validate vendor recording origins, including regional Amazon Phoenix delivery."""
    try:
        url = urlsplit(str(value or ""))
        host = (url.hostname or "").lower()
        vendor = any(host == domain or host.endswith("." + domain)
                     for domain in ("ring.com", "amazonaws.com", "cloudfront.net"))
        phoenix = re.fullmatch(
            r"(?:(?:[0-9]{1,3}-){3}[0-9]{1,3}\.)?download-[a-z]{2}(?:-[a-z]+)+-[0-9]+"
            r"\.prod\.phoenix\.devices\.amazon\.dev", host)
        if (url.scheme != "https" or url.username or url.password or
                url.port not in (None, 443) or url.fragment or not (vendor or phoenix)):
            raise ValueError()
        return url
    except ValueError:
        raise web.HTTPBadRequest(reason="recording_vendor_url_not_supported") from None


async def async_download_recording(hass, request, entry, selected, identifier):
    if not ID_RE.fullmatch(identifier):
        raise web.HTTPNotFound()
    record = hass.data.get(CACHE_KEY, {}).get((entry.entry_id, selected, identifier))
    registered = _camera(hass, selected)
    identity = (registered.config_entry_id, registered.device_id, registered.unique_id)
    if not record or record["expires"] <= hass.loop.time() or record["identity"] != identity:
        raise web.HTTPNotFound(reason="recording_expired_refresh_list")
    if record["provider"] in {"unifiprotect", "tapo_control", "blink"}:
        from .recording_providers import download_source
        return await download_source(hass, request, registered, selected, record["source"])
    if record["provider"] == "reolink":
        resolved = await media_source.async_resolve_media(hass, record["source"], None)
        url = urlsplit(resolved.url)
        match = re.fullmatch(r"/api/reolink/video/([^/]+)/(\d+)/(sub)/([^/]+)/([A-Za-z0-9_=-]+)", url.path)
        source_parts = record["source"].removeprefix("media-source://reolink/").split("|")
        if url.scheme or url.netloc or url.query or url.fragment or not match or list(match.groups()[:2]) != source_parts[1:3]:
            raise web.HTTPBadRequest(reason="recording_download_format_unavailable")
        from homeassistant.components.reolink.views import PlaybackProxyView
        # Never forward the pairing capability or HA/browser headers to a camera.
        clean_request = request.clone(headers={})
        return await PlaybackProxyView(hass).get(clean_request, *match.groups())

    state = hass.states.get(selected)
    attrs = state.attributes if state else {}
    if "ring:" + str(attrs.get("last_video_id")) != record["source"]:
        raise web.HTTPNotFound(reason="recording_changed_refresh_list")
    url = _ring_recording_url(attrs.get("video_url"))
    session = async_get_clientsession(hass)
    async with asyncio.timeout(180):
        for redirects in range(4):
            async with session.get(url.geturl(), allow_redirects=False,
                                   timeout=ClientTimeout(total=180, connect=15)) as upstream:
                if upstream.status in {301, 302, 303, 307, 308}:
                    location = upstream.headers.get("Location")
                    if redirects == 3 or not location:
                        raise web.HTTPBadGateway(reason="recording_redirect_limit")
                    # Ring Phoenix routes regional links to a numbered delivery host.
                    # Check every hop before connecting; never forward incoming headers.
                    url = _ring_recording_url(urljoin(url.geturl(), location))
                    continue
                if upstream.status != 200 or upstream.content_type not in {"video/mp4", "application/octet-stream"}:
                    raise web.HTTPBadGateway(reason="recording_download_failed")
                if upstream.content_length and upstream.content_length > MAX_BYTES:
                    raise web.HTTPRequestEntityTooLarge(max_size=MAX_BYTES, actual_size=upstream.content_length)
                response = web.StreamResponse(headers={"Content-Type": "video/mp4", "Cache-Control": "no-store"})
                await response.prepare(request)
                size = 0
                async for chunk in upstream.content.iter_chunked(65536):
                    size += len(chunk)
                    if size > MAX_BYTES:
                        request.transport.close()
                        return response
                    await response.write(chunk)
                await response.write_eof()
                return response
