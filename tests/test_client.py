"""Validate the public HTTP boundary without private desktop imports."""

from aiohttp import ClientConnectorError, ServerDisconnectedError
from aiohttp.client_reqrep import ConnectionKey

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.cam_wise.client import (
    CamWiseApiClient,
    CamWiseConnectionError,
    CamWiseNotSentError,
    CamWiseUnsupportedApiError,
    base_url,
    normalize_host,
)

from .conftest import BASE_URL, DISCOVERY, STATUS


async def test_api_contract(hass, api):
    client = CamWiseApiClient(async_get_clientsession(hass), "cam-wise.test", 8000)
    assert await client.async_validate() == DISCOVERY
    assert await client.async_status() == STATUS
    payload = {
        "trigger_type": "recording_ready",
        "trigger_entity_id": "sensor.front_recording",
        "camera_entity_id": "camera.front",
        "occurred_at": "2026-10-14T12:00:00+00:00",
        "event_id": "synthetic-context",
        "context_id": "synthetic-context",
        "media_identifier": "synthetic-media",
    }
    assert await client.async_send_event(payload) == {"ok": True, "result": "accepted"}
    assert api.mock_calls[-1][2] == payload
    await client.async_report_integration_status({"integration_loaded": True})
    assert (
        str(api.mock_calls[-1][1])
        == f"{BASE_URL}/integrations/home-assistant/cam-wise/status"
    )


@pytest.mark.parametrize(
    ("payload", "exception"),
    [
        ([], CamWiseConnectionError),
        ({}, CamWiseUnsupportedApiError),
        ({**STATUS, "api_version": "2"}, CamWiseUnsupportedApiError),
        ({"api_version": "1"}, CamWiseConnectionError),
    ],
)
async def test_status_validation(hass, aioclient_mock, payload, exception):
    aioclient_mock.get(f"{BASE_URL}/integrations/home-assistant/status", json=payload)
    client = CamWiseApiClient(async_get_clientsession(hass), "cam-wise.test", 8000)
    with pytest.raises(exception):
        await client.async_status()


@pytest.mark.parametrize("post", [True, False])
async def test_http_failure(hass, aioclient_mock, post):
    client = CamWiseApiClient(async_get_clientsession(hass), "cam-wise.test", 8000)
    if post:
        aioclient_mock.post(
            f"{BASE_URL}/integrations/home-assistant/cam-wise/event", status=503
        )
        call = client.async_send_event({"trigger_type": "motion"})
    else:
        aioclient_mock.get(f"{BASE_URL}/health", status=503)
        call = client.async_validate()
    with pytest.raises(CamWiseConnectionError):
        await call


def test_ipv6_address():
    assert base_url("2001:db8::1", 8000) == "http://[2001:db8::1]:8000"


@pytest.mark.parametrize("before_request", [True, False])
async def test_post_distinguishes_connection_failure_from_lost_response(
    hass, aioclient_mock, before_request
):
    client = CamWiseApiClient(async_get_clientsession(hass), "cam-wise.test", 8000)
    key = ConnectionKey("cam-wise.test", 8000, False, False, None, None, None)
    error = (
        ClientConnectorError(key, OSError("refused"))
        if before_request
        else ServerDisconnectedError()
    )
    aioclient_mock.post(
        f"{BASE_URL}/integrations/home-assistant/cam-wise/event", exc=error
    )
    with pytest.raises(CamWiseConnectionError) as caught:
        await client.async_send_event({"trigger_type": "motion"})
    assert isinstance(caught.value, CamWiseNotSentError) is before_request


@pytest.mark.parametrize(
    "host",
    [
        "https://cam-wise.test",
        "user:password@host",
        "host:8000",
        "host/path",
        "host?token=x",
        "host name",
        "[bad::address]",
    ],
)
def test_reject_unsafe_or_ambiguous_host(host):
    with pytest.raises(ValueError):
        normalize_host(host)


@pytest.mark.parametrize(
    "field,value",
    [
        ("review_queue", "3"),
        ("review_queue", True),
        ("review_queue", -1),
        ("attention_required", "false"),
        ("status", []),
        ("recommended_route_options", []),
        ("recommended_route_options", {"camera_entity_id": []}),
    ],
)
async def test_reject_malformed_status_types(hass, aioclient_mock, field, value):
    aioclient_mock.get(
        f"{BASE_URL}/integrations/home-assistant/status", json={**STATUS, field: value}
    )
    client = CamWiseApiClient(async_get_clientsession(hass), "cam-wise.test", 8000)
    with pytest.raises(CamWiseConnectionError):
        await client.async_status()


async def test_optional_recommended_mapping_null_values(hass, aioclient_mock):
    status = {**STATUS, "recommended_route_options": {"camera_entity_id": None}}
    aioclient_mock.get(f"{BASE_URL}/integrations/home-assistant/status", json=status)
    client = CamWiseApiClient(async_get_clientsession(hass), "cam-wise.test", 8000)
    assert await client.async_status() == status


@pytest.mark.parametrize("status", [307, 308])
@pytest.mark.parametrize("reachable_target", [False, True])
async def test_post_redirect_is_unknown_without_followup(
    hass, aiohttp_server, socket_enabled, status, reachable_target
):
    from aiohttp import web

    calls = []
    target_calls = []

    async def target(request):
        target_calls.append(await request.json())
        return web.json_response({"ok": True, "result": "accepted"})

    target_app = web.Application()
    target_app.router.add_post("/target", target)
    target_server = await aiohttp_server(target_app)
    location = (
        str(target_server.make_url("/target"))
        if reachable_target
        else "http://127.0.0.1:1/unreachable"
    )

    async def redirect(request):
        calls.append(await request.json())
        return web.Response(status=status, headers={"Location": location})

    app = web.Application()
    app.router.add_post("/integrations/home-assistant/cam-wise/event", redirect)
    server = await aiohttp_server(app)
    client = CamWiseApiClient(async_get_clientsession(hass), "127.0.0.1", server.port)
    with pytest.raises(CamWiseConnectionError) as caught:
        await client.async_send_event({"media_identifier": "synthetic-private-media"})
    assert not isinstance(caught.value, CamWiseNotSentError)
    assert str(caught.value) == "Cam-Wise returned an unexpected HTTP status"
    assert len(calls) == 1
    assert not target_calls
