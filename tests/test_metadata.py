"""Guard independently stored manifest and actual runtime version identity."""
import json
from pathlib import Path

from custom_components.cam_wise.const import INTEGRATION_VERSION

async def test_manifest_runtime_and_protocol_version_identity(hass, api, entry):
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "custom_components/cam_wise/manifest.json").read_text(encoding="utf-8"))
    report = json.loads((root / "tests/fixtures/integration-status.json").read_text(encoding="utf-8"))
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.diagnostics["version"] == manifest["version"] == report["version"] == INTEGRATION_VERSION
