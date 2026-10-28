"""Ring URL-origin and stream regressions with synthetic recordings only."""
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock
import pytest
from aiohttp import web
from homeassistant.helpers import entity_registry as er
from custom_components.cam_wise import recordings as rec


@pytest.mark.parametrize("host", [
    "download-eu-south-2.prod.phoenix.devices.amazon.dev",
    "download-us-east-1.prod.phoenix.devices.amazon.dev",
    "download-ap-southeast-2.prod.phoenix.devices.amazon.dev",
    "recordings.ring.com", "example.s3.amazonaws.com", "example.cloudfront.net",
])
def test_ring_vendor_origins_and_signed_query(host):
    value = "https://" + host + "/recording.mp4?signature=synthetic"
    assert rec._ring_recording_url(value).geturl() == value


@pytest.mark.parametrize("value", [
    "http://download-eu-south-2.prod.phoenix.devices.amazon.dev/a",
    "https://download-eu-south-2.prod.phoenix.devices.amazon.dev.evil.test/a",
    "https://evil-download-eu-south-2.prod.phoenix.devices.amazon.dev/a",
    "https://anything.devices.amazon.dev/a",
    "https://download-eu-south-2.staging.phoenix.devices.amazon.dev/a",
    "https://download-eu-south-2.prod.phoenix.devices.amazon.dev:8000/a",
    "https://user:password@download-eu-south-2.prod.phoenix.devices.amazon.dev/a",
    "https://download-eu-south-2.prod.phoenix.devices.amazon.dev/a#fragment",
    "https://127.0.0.1/a", "https://[::1]/a", "https://evil.test/a",
    "https://recordings.ring.com:invalid/a", "https://[broken", "",
])
def test_ring_rejects_untrusted_or_malformed_origins(value):
    with pytest.raises(web.HTTPBadRequest, match="recording_vendor_url_not_supported"):
        rec._ring_recording_url(value)


async def test_phoenix_recording_stream_does_not_forward_pairing_credentials(hass, monkeypatch):
    row = er.async_get(hass).async_get_or_create("camera", "ring", "synthetic-phoenix")
    entry = NS(entry_id="cw")
    url = "https://download-eu-south-2.prod.phoenix.devices.amazon.dev/a.mp4?signature=synthetic"
    hass.states.async_set(row.entity_id, "idle", {"last_video_id": 123, "video_url": url})
    listed = await rec.async_list_recordings(hass, entry, row.entity_id)

    async def chunks(size):
        yield b"synthetic-recorded-video"

    upstream = NS(status=200, content_type="video/mp4", content_length=24,
                  content=NS(iter_chunked=chunks))

    class Context:
        async def __aenter__(self):
            return upstream
        async def __aexit__(self, *args):
            return None

    session = NS(get=Mock(return_value=Context()))
    monkeypatch.setattr(rec, "async_get_clientsession", lambda hass: session)
    output = NS(prepare=AsyncMock(), write=AsyncMock(), write_eof=AsyncMock())
    monkeypatch.setattr(rec.web, "StreamResponse", Mock(return_value=output))
    request = NS(headers={"Authorization": "Bearer synthetic-pairing"})
    result = await rec.async_download_recording(hass, request, entry, row.entity_id,
                                              listed["recordings"][0]["id"])
    assert result is output
    args, kwargs = session.get.call_args
    assert args == (url,)
    assert kwargs["allow_redirects"] is False and "headers" not in kwargs
    output.write.assert_awaited_once_with(b"synthetic-recorded-video")
    output.write_eof.assert_awaited_once()
