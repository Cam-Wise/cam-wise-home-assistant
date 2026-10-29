"""Read-only camera bridge authorized by the approved installation credential.

This is not a Home Assistant user token and exposes no services or arbitrary proxy.
"""
from __future__ import annotations

import hmac
from aiohttp import web
from homeassistant.components.http import HomeAssistantView, KEY_HASS

from .const import DOMAIN, RECORDING_CONTRACT


async def async_get_image(hass, entity_id, timeout=10):
    # Camera dependencies belong to the installed camera integration. Status-only
    # use must not import its optional image stack during Cam-Wise setup.
    from homeassistant.components.camera import async_get_image as get_image
    return await get_image(hass, entity_id, timeout=timeout)


class CamWiseBridge(HomeAssistantView):
    url = "/api/cam_wise_bridge/api/{resource:.*}"
    name = "api:cam_wise_bridge"
    requires_auth = False

    async def get(self, request, resource):
        hass = request.app[KEY_HASS]
        if request.headers.get("Origin") or request.query:
            return web.Response(status=403)
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        entry = next((e for e in hass.config_entries.async_entries(DOMAIN)
            if e.state.value == "loaded" and e.data.get("pairing_token") and
            hmac.compare_digest(str(e.data["pairing_token"]), token)), None)
        if entry is None:
            return web.Response(status=401)
        # A Desktop revocation also invalidates this reverse read capability.
        from .client import CamWiseApiError
        try:
            desktop_status = await entry.runtime_data.client.async_status()
        except CamWiseApiError:
            return web.Response(status=401)
        options = {**entry.data, **entry.options}
        selected = str(options.get("camera_entity_id") or "")
        allowed = {str(options.get(k) or "") for k in
            ("camera_entity_id", "motion_entity_id", "ding_entity_id", "recording_entity_id")}
        if resource.startswith("recordings/"):
            if (type(desktop_status.get("recording_contract")) is not int or
                    desktop_status["recording_contract"] != RECORDING_CONTRACT or
                    request.headers.get("X-Cam-Wise-Recording-Contract") != str(RECORDING_CONTRACT)):
                return self.json({"error": "desktop_recording_update_required",
                    "message_en": "Update Cam-Wise Desktop before enabling automatic recorded videos.",
                    "message_nl": "Werk Cam-Wise Desktop bij voordat u automatische video-invoer inschakelt."},
                    status_code=409)
            from .recordings import async_list_recordings, async_download_recording
            parts = resource.split("/")
            approved = {selected} if selected else set()
            extra = options.get("recording_camera_entities", [])
            if isinstance(extra, list):
                approved.update(e for e in extra if isinstance(e, str) and e.startswith("camera."))
            if len(parts) < 2 or parts[1] not in approved:
                return web.Response(status=403)
            selected = parts[1]
            try:
                if len(parts) == 4 and parts[2] == "file":
                    return await async_download_recording(hass, request, entry, selected, parts[3])
                if len(parts) in (2, 3):
                    return self.json({**await async_list_recordings(hass, entry, selected, parts[2] if len(parts) == 3 else ""),
                                      "recording_contract": RECORDING_CONTRACT})
                return web.Response(status=404)
            except web.HTTPException:
                raise
            except Exception:
                # Never return vendor URLs/credentials from underlying exceptions.
                return self.json({"error": "ha_recording_read_failed"}, status_code=502)
        def serialized(state):
            value = dict(state.as_dict())
            if state.domain == "camera" and state.entity_id != selected:
                value["attributes"] = {"friendly_name": state.attributes.get("friendly_name", state.entity_id)}
            else:
                value["attributes"] = {k: v for k, v in state.attributes.items()
                    if k not in {"access_token", "entity_picture", "password", "token"}}
            return value
        if resource == "":
            return self.json({"message": "API running."})
        if resource == "states":
            # All camera identities may be offered for selection; no unrelated sensors.
            states = [s for s in hass.states.async_all() if s.domain == "camera" or s.entity_id in allowed]
            return self.json([serialized(s) for s in states])
        if resource.startswith("states/"):
            entity_id = resource.removeprefix("states/")
            if entity_id not in allowed and not entity_id.startswith("camera."):
                return web.Response(status=403)
            state = hass.states.get(entity_id)
            return self.json(serialized(state)) if state else web.Response(status=404)
        if resource.startswith("camera_proxy/"):
            entity_id = resource.removeprefix("camera_proxy/")
            if not selected or entity_id != selected:
                return web.Response(status=403)
            try:
                image = await async_get_image(hass, entity_id, timeout=10)
                return web.Response(body=image.content, content_type=image.content_type)
            except Exception:
                return web.Response(status=502)
        return web.Response(status=404)
