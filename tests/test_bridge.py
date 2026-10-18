"""The paired credential is not a general Home Assistant user credential."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

from homeassistant.setup import async_setup_component


async def test_bridge_limits_state_snapshot_and_services(hass, hass_client, entry, api, monkeypatch):
    await async_setup_component(hass, "http", {})
    hass.config_entries.async_update_entry(entry, data={**entry.data, "pairing_token": "synthetic-bridge-token"})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    hass.states.async_set("camera.other", "idle", {"friendly_name": "Other", "access_token": "must-not-leak"})
    hass.states.async_set("sensor.private", "private-value")
    image = AsyncMock(return_value=SimpleNamespace(content=b"synthetic-image", content_type="image/jpeg"))
    monkeypatch.setattr("custom_components.cam_wise.bridge.async_get_image", image)
    client = await hass_client()
    base = "/api/cam_wise_bridge/api/"
    headers = {"Authorization": "Bearer synthetic-bridge-token"}
    assert (await client.get(base + "states")).status == 401
    response = await client.get(base + "states", headers=headers)
    assert response.status == 200
    values = await response.json()
    assert not any(s["entity_id"] == "sensor.private" for s in values)
    other = next(s for s in values if s["entity_id"] == "camera.other")
    assert "access_token" not in other["attributes"]
    assert (await client.get(base + "states/sensor.private", headers=headers)).status == 403
    assert (await client.get(base + "camera_proxy/camera.other", headers=headers)).status == 403
    assert (await client.get(base + "camera_proxy/camera.front", headers=headers)).status == 200
    assert (await client.get(base + "services", headers=headers)).status == 404
    assert (await client.post(base + "services", headers=headers)).status == 405
    assert (await client.get(base + "states", headers={**headers, "Origin": "https://example.com"})).status == 403
