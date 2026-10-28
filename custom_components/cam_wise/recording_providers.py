"""Selected-camera recording adapters. Never start recordings or access live feeds."""
from __future__ import annotations

import asyncio
import json
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

from aiohttp import web
from homeassistant.util import dt as dt_util

MAX_BYTES = 1024 * 1024 * 1024


def entity(hass, selected):
    camera = hass.data.get("camera")
    value = camera.get_entity(selected) if camera else None
    if value is None:
        raise web.HTTPConflict(reason="camera_not_loaded")
    return value


def tapo_device(hass, registered, selected):
    root = hass.data.get("tapo_control", {}).get(registered.config_entry_id)
    if not root:
        raise web.HTTPConflict(reason="tapo_control_not_loaded")
    matches = [device for device in [root, *root.get("childDevices", [])]
               if any(row.get("entity") is entity(hass, selected)
                      for row in device.get("entities", []))]
    if len(matches) != 1:
        raise web.HTTPConflict(reason="tapo_camera_mapping_unavailable")
    return matches[0]


async def list_sources(hass, registered, selected):
    """Return internal stable identities and labels; URLs never leave HA."""
    provider = registered.platform
    cam = entity(hass, selected)
    if provider == "unifiprotect":
        if getattr(cam.data.api, "is_public_only", False):
            raise web.HTTPConflict(reason="unifi_full_access_required")
        rows = await cam.data.api.get_events_raw(start=dt_util.utcnow() - timedelta(days=1),
            end=dt_util.utcnow(), limit=1000)
        rows = [r for r in rows if r.get("camera") == cam.device.id and r.get("end")
                and r.get("start") and r.get("end") < dt_util.utcnow().timestamp() * 1000 - 10000]
        return [(str(r["id"]), str(r["start"])) for r in
                sorted(rows, key=lambda r: r["start"], reverse=True)[:100]]
    if provider == "blink":
        api = cam._camera
        rows = list(api.recent_clips or [])
        if api.clip:
            rows.append({"clip": api.clip, "time": api.last_record})
        # The SDK authenticates to its own server. Refuse arbitrary remote origins.
        origin = urlsplit(api.sync.urls.base_url)
        result = {}
        for row in rows:
            url = urlsplit(str(row.get("clip") or ""))
            if url.scheme == "https" and (url.hostname, url.port) == (origin.hostname, origin.port):
                result[url.geturl()] = str(row.get("time") or "Blink recording")
        return list(result.items())[-100:]
    if provider == "tapo_control":
        from custom_components.tapo_control.utils import getRecordings
        device = tapo_device(hass, registered, selected)
        dates = await hass.async_add_executor_job(device["controller"].getRecordingsList)
        keys = sorted({str(row["date"]) for item in dates for row in item.values()}, reverse=True)[:2]
        rows = []
        now = dt_util.utcnow().timestamp() + device.get("timezoneOffset", 0)
        for day in keys:
            records = await getRecordings(hass, device, device["controller"], day)
            for item in records:
                for row in item.values():
                    start, end = int(row["startTime"]), int(row["endTime"])
                    if start < end < now - 15:
                        rows.append((json.dumps([day, start, end]), str(start)))
        return sorted(rows, key=lambda row: json.loads(row[0])[1], reverse=True)[:100]
    raise web.HTTPBadRequest(reason="recording_provider_not_supported")


async def stream_upstream(request, upstream):
    if upstream is None or upstream.status != 200:
        raise web.HTTPBadGateway(reason="recording_not_ready")
    if upstream.content_type not in {"video/mp4", "application/octet-stream"}:
        raise web.HTTPBadGateway(reason="recording_not_video")
    if upstream.content_length and upstream.content_length > MAX_BYTES:
        raise web.HTTPRequestEntityTooLarge(max_size=MAX_BYTES, actual_size=upstream.content_length)
    response = web.StreamResponse(headers={"Content-Type": "video/mp4", "Cache-Control": "no-store"})
    if upstream.content_length:
        response.content_length = upstream.content_length
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


async def download_source(hass, request, registered, selected, source):
    cam = entity(hass, selected)
    if registered.platform == "unifiprotect":
        event = await cam.data.api.get_event(source)
        if event.camera_id != cam.device.id or not event.start or not event.end:
            raise web.HTTPForbidden()
        from homeassistant.components.unifiprotect.views import VideoEventProxyView
        return await VideoEventProxyView(hass).get(request.clone(headers={}),
            cam.data.api.bootstrap.nvr.id, source)
    if registered.platform == "blink":
        # Revalidate membership and camera immediately before SDK authenticated read.
        if source not in dict(await list_sources(hass, registered, selected)):
            raise web.HTTPNotFound(reason="recording_expired")
        upstream = await cam._camera.get_video_clip(url=source)
        try:
            async with asyncio.timeout(180):
                return await stream_upstream(request, upstream)
        finally:
            if upstream is not None:
                upstream.release()
    if registered.platform == "tapo_control":
        from custom_components.tapo_control.utils import getRecording, getColdFile, getColdDirPathForEntry
        device = tapo_device(hass, registered, selected)
        day, start, end = json.loads(source)
        child = device["camData"]["basic_info"]["dev_id"] if device.get("isChild") else ""
        path = Path(getColdFile(hass, registered.config_entry_id, start, end, "videos", childID=child)).resolve()
        base = Path(getColdDirPathForEntry(hass, registered.config_entry_id)).resolve() / "videos"
        if path.parent != base or path.suffix != ".mp4":
            raise web.HTTPForbidden()
        tasks = hass.data.setdefault("cam_wise_recording_prepare", {})
        task_key = (registered.config_entry_id, selected)
        task = tasks.get(task_key)
        if task is not None and not task.done():
            raise web.HTTPConflict(reason="recording_preparing_retry")
        if task is not None:
            # Consume failures; do not leak a vendor exception or signed URL.
            if not task.cancelled():
                task.exception()
            tasks.pop(task_key, None)
        if not path.is_file():
            async def prepare():
                async with asyncio.timeout(180):
                    await getRecording(hass, device["controller"], registered.config_entry_id,
                                       device, day.replace("-", ""), start, end)
            vendor_entry = hass.config_entries.async_get_entry(registered.config_entry_id)
            tasks[task_key] = vendor_entry.async_create_background_task(hass,
                prepare(), "cam_wise_prepare_existing_recording")
            # Retries fetch the completed cached file; never start parallel downloads.
            raise web.HTTPConflict(reason="recording_preparing_retry")
        if path.parent != base or path.suffix != ".mp4" or not path.is_file():
            raise web.HTTPNotFound(reason="recording_not_ready")
        if path.stat().st_size > MAX_BYTES:
            raise web.HTTPRequestEntityTooLarge(max_size=MAX_BYTES, actual_size=path.stat().st_size)
        return web.FileResponse(path, headers={"Content-Type": "video/mp4", "Cache-Control": "no-store"})
    raise web.HTTPBadRequest(reason="recording_provider_not_supported")
