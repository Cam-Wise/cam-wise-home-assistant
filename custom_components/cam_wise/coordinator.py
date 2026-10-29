"""Data coordinator for Cam-Wise status entities."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import CamWiseApiClient, CamWiseApiError, CamWiseAuthError
from .const import DOMAIN, RECORDING_CONTRACT, UPDATE_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class CamWiseCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll Cam-Wise once for all entities."""

    def __init__(self, hass: HomeAssistant, client: CamWiseApiClient, entry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
            always_update=False,
        )
        self.entry = entry
        self.client = client
        self._last_update_failed = False

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.client.async_status()
        except CamWiseAuthError as err:
            raise ConfigEntryAuthFailed("Approve this Home Assistant connection in Cam-Wise Desktop again") from err
        except CamWiseApiError as err:
            if not self._last_update_failed:
                _LOGGER.warning("Cam-Wise is unavailable: %s", err)
            self._last_update_failed = True
            raise UpdateFailed("Cam-Wise is unreachable. Start Desktop or use Reconfigure if its address changed") from err
        if self.entry.data.get("pairing_token"):
            from homeassistant.helpers import issue_registry as ir
            issue_id = "recording_desktop_update_" + self.entry.entry_id
            if type(data.get("recording_contract")) is not int or data["recording_contract"] != RECORDING_CONTRACT:
                ir.async_create_issue(self.hass, DOMAIN, issue_id, is_fixable=False,
                    severity=ir.IssueSeverity.WARNING, translation_key="recording_desktop_update")
            else:
                ir.async_delete_issue(self.hass, DOMAIN, issue_id)
        if self.entry.data.get("pairing_token") and data.get("recommended_route_options"):
            from . import _persist_recommended_route_options
            _persist_recommended_route_options(self.hass, self.entry, data)
        runtime = getattr(self.entry, "runtime_data", None)
        handler = getattr(runtime, "events", None)
        if self.entry.data.get("pairing_token") and handler is not None:
            handler.spawn(handler.async_report_status())
        if self._last_update_failed:
            _LOGGER.info("Cam-Wise is available again")
        self._last_update_failed = False
        return data
