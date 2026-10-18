"""HTTP pairing remains an explicit Desktop approval, never a pasted token."""
import hashlib

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.cam_wise.client import CamWiseApiClient, CamWiseAuthError
from custom_components.cam_wise.const import DOMAIN
from .conftest import BASE_URL, DATA, DISCOVERY, STATUS


async def test_pairing_requires_approval_then_preserves_token(hass, aioclient_mock, monkeypatch):
    token = "synthetic-test-token-never-a-real-credential"
    monkeypatch.setattr("custom_components.cam_wise.config_flow.secrets.token_urlsafe", lambda n: token)
    code = hashlib.sha256(token.encode()).hexdigest()[:6].upper()
    aioclient_mock.get(f"{BASE_URL}/health", json={"status": "ok"})
    aioclient_mock.get(f"{BASE_URL}/integrations/home-assistant/discovery-info",
                      json={**DISCOVERY, "pairing_required": True})
    aioclient_mock.post(f"{BASE_URL}/integrations/home-assistant/pair", json={"request_id": "synthetic", "code": code})
    aioclient_mock.get(f"{BASE_URL}/integrations/home-assistant/status", status=401)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER}, data=DATA)
    assert result["step_id"] == "pair"
    assert result["description_placeholders"]["code"] == code
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE_URL}/integrations/home-assistant/status", json={**STATUS, "device_id": DISCOVERY["device_id"]})
    aioclient_mock.post(f"{BASE_URL}/integrations/home-assistant/cam-wise/status", json={"ok": True})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {**DATA, "pairing_token": token}
    await hass.async_block_till_done()


async def test_revoked_token_is_auth_error_without_secret(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/integrations/home-assistant/status", status=401)
    client = CamWiseApiClient(async_get_clientsession(hass), DATA["host"], DATA["port"], "synthetic-token")
    with pytest.raises(CamWiseAuthError) as exc:
        await client.async_status()
    assert "synthetic-token" not in str(exc.value)
