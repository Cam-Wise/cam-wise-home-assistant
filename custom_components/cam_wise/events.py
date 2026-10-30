"""Entry-owned, bounded event intake; HTTP acceptance is not processing proof."""

from __future__ import annotations

import asyncio
from collections import OrderedDict, deque
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.util.dt import parse_datetime, utcnow

from .client import CamWiseApiError, CamWiseNotSentError
from .const import CONF_PORT, INTEGRATION_VERSION

if TYPE_CHECKING:
    from . import CamWiseConfigEntry

_LOGGER = logging.getLogger(__name__)
PENDING_SECONDS = 120
MAX_PENDING = 64
MAX_RECENT_MEDIA = 256
ROLE_DOMAINS = {
    "camera": {"camera"},
    "motion": {"event", "binary_sensor"},
    "ding": {"event", "binary_sensor"},
    "recording_ready": {"sensor", "event", "camera"},
}


def mapping_errors(
    routes: dict[str, str], hass: HomeAssistant | None = None
) -> set[str]:
    """Validate domains and role conflicts; camera may also supply recordings."""
    errors = {
        role
        for role, entity in routes.items()
        if entity
        and (
            entity.split(".", 1)[0] not in ROLE_DOMAINS[role]
            or (hass is not None and hass.states.get(entity) is None)
        )
    }
    roles = ("motion", "ding", "recording_ready")
    for role in roles:
        if routes[role] and any(
            routes[role] == routes[other] for other in roles if other != role
        ):
            errors.add(role)
    if any(routes[role] for role in roles) and not routes["camera"]:
        errors.add("camera")
    return errors


def media_identifier(state: State | None) -> str | None:
    if state is None:
        return None
    value = next(
        (
            state.attributes.get(key)
            for key in ("last_video_id", "media_id", "video_id")
            if state.attributes.get(key)
        ),
        None,
    )
    return (
        str(value)
        if isinstance(value, (str, int)) and not isinstance(value, bool)
        else None
    )


def state_payload(routes: dict[str, str], event: Event) -> dict[str, Any] | None:
    """Only rising binary edges, new EventEntity timestamps, or changed media IDs."""
    entity = event.data.get("entity_id")
    role = next(
        (
            role
            for role in ("motion", "ding", "recording_ready")
            if routes[role] and routes[role] == entity
        ),
        None,
    )
    new: State | None = event.data.get("new_state")
    old: State | None = event.data.get("old_state")
    if role is None or new is None or new.state in {"unknown", "unavailable", ""}:
        return None
    media = media_identifier(new)
    if role == "recording_ready":
        if media is None or media == media_identifier(old):
            return None
        occurred = new.last_updated
    elif new.domain == "binary_sensor":
        if new.state != "on" or old is None or old.state != "off":
            return None
        occurred = new.last_changed
    else:
        occurred = parse_datetime(new.state)
        if (
            occurred is None
            or occurred.tzinfo is None
            or (old and old.state == new.state)
        ):
            return None
        age = (utcnow() - occurred).total_seconds()
        if age < -5 or age > PENDING_SECONDS:
            return None
    if role != "recording_ready" and media == media_identifier(old):
        media = None
    return {
        "trigger_type": role,
        "trigger_entity_id": entity,
        "camera_entity_id": routes["camera"],
        "occurred_at": occurred.isoformat(),
        "event_id": new.context.id,
        "context_id": new.context.id,
        "media_identifier": media,
    }


@dataclass
class PendingEvent:
    payload: dict[str, Any]
    expires: float
    attempts: int = 0
    retry_at: float = 0


class CamWiseEventHandler:
    """One entry owns listeners, tasks, FIFO waits and a bounded media ledger.

    The lock covers the HTTP await: concurrent callbacks cannot send the same
    media. An ambiguous delivery is terminal locally to avoid unsafe replay.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: CamWiseConfigEntry,
        routes: dict[str, str],
        origin: str,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.client = entry.runtime_data.client
        self.coordinator = entry.runtime_data.coordinator
        self.routes = routes
        self.diagnostics = entry.runtime_data.diagnostics
        self.lock = asyncio.Lock()
        self.pending: deque[PendingEvent] = deque()
        self.retries: OrderedDict[str, PendingEvent] = OrderedDict()
        self.recent: OrderedDict[str, str] = OrderedDict()
        self.tasks: set[asyncio.Task[None]] = set()
        self.unsubs: list[Callable[[], None]] = []
        self.timer: asyncio.TimerHandle | None = None
        self.closed = False
        self.diagnostics.update(
            {
                "entry_id": entry.entry_id,
                "callback_function": "receive",
                "camera_entity_id": routes["camera"] or None,
                "motion_entity_id": routes["motion"] or None,
                "ding_entity_id": routes["ding"] or None,
                "recording_entity_id": routes["recording_ready"] or None,
                "last_forward_target_port": entry.data[CONF_PORT],
                "listeners_registered": False,
                "unsubscribe_handle_present": False,
                "version": INTEGRATION_VERSION,
                "mapping_origin": origin,
                "integration_loaded": True,
                "connected": True,
                "listener_type": "state_changed",
                "registered_after_restart": True,
                "received_count": 0,
                "forwarded_count": 0,
                "accepted_count": 0,
                "expired_count": 0,
                "overflow_count": 0,
                "duplicate_count": 0,
                "uncertain_count": 0,
                "processed": None,
                "mapping_errors": sorted(mapping_errors(routes)),
            }
        )
        # Existing media at startup is a baseline, never a replay request.
        baseline = media_identifier(hass.states.get(routes["recording_ready"]))
        if baseline:
            self.recent[baseline] = "startup_baseline"

    @callback
    def start(self) -> Callable[[], None] | None:
        self.unsubs.append(self.coordinator.async_add_listener(self.connection_changed))
        errors = mapping_errors(self.routes)
        if errors:
            self.diagnostics["last_trace_step"] = "invalid_mapping"
            return None
        watched = any(
            self.routes[role] for role in ("motion", "ding", "recording_ready")
        )
        if watched:
            self.unsubs.append(
                self.hass.bus.async_listen("state_changed", self.receive)
            )
        self.diagnostics.update(
            {
                "listeners_registered": watched,
                "unsubscribe_handle_present": watched,
                "last_trace_step": "listeners_registered",
                **{
                    f"{role}_listener_registered": bool(watched and self.routes[role])
                    for role in ("motion", "ding")
                },
                "recording_listener_registered": bool(
                    watched and self.routes["recording_ready"]
                ),
                "media_listener_registered": bool(
                    watched and self.routes["recording_ready"]
                ),
            }
        )
        return self.stop_listeners if watched else None

    @callback
    def spawn(self, work: Coroutine[Any, Any, None]) -> None:
        task = self.hass.async_create_task(work, "Cam-Wise event")
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    @callback
    def receive(self, event: Event) -> None:
        if self.closed:
            return
        if self.hass.states.get(self.routes["camera"]) is None:
            self.diagnostics["last_trace_step"] = "camera_missing"
            return
        payload = state_payload(self.routes, event)
        if payload is None:
            return
        self.diagnostics.update(
            {
                "last_event_received_at": utcnow().isoformat(),
                "last_entity_id": payload["trigger_entity_id"],
                "last_event_kind": payload["trigger_type"],
                "context_id_present": bool(payload["context_id"]),
            }
        )
        self.diagnostics["received_count"] += 1
        if len(self.tasks) >= MAX_PENDING:
            self.diagnostics["overflow_count"] += 1
            _LOGGER.warning("Cam-Wise event intake limit reached")
            return
        occurred = parse_datetime(payload["occurred_at"])
        age = max(0, (utcnow() - occurred).total_seconds())
        self.spawn(
            self.handle(
                PendingEvent(payload, self.hass.loop.time() + PENDING_SECONDS - age)
            )
        )

    @callback
    def connection_changed(self) -> None:
        if self.closed:
            return
        self.diagnostics["connected"] = self.coordinator.last_update_success
        if self.coordinator.last_update_success and self.retries:
            self.spawn(self.retry())

    def expire(self) -> None:
        now = self.hass.loop.time()
        retained = deque(item for item in self.pending if item.expires > now)
        self.diagnostics["expired_count"] += len(self.pending) - len(retained)
        self.pending = retained
        for media, item in list(self.retries.items()):
            if item.expires <= now:
                del self.retries[media]
                self.diagnostics["expired_count"] += 1
        self.diagnostics["media_wait_started"] = bool(self.pending)
        self.diagnostics["pending_count"] = len(self.pending)
        self.diagnostics["retry_count"] = len(self.retries)

    def schedule_expiry(self) -> None:
        if self.timer:
            self.timer.cancel()
            self.timer = None
        waits = [item.expires for item in (*self.pending, *self.retries.values())]
        if self.coordinator.last_update_success:
            waits.extend(item.retry_at for item in self.retries.values())
        if waits and not self.closed:
            self.timer = self.hass.loop.call_at(min(waits), self.expiry_due)

    @callback
    def expiry_due(self) -> None:
        self.timer = None
        if not self.closed:
            self.spawn(
                self.retry(send=self.coordinator.last_update_success, force=False)
            )

    async def handle(self, item: PendingEvent) -> None:
        async with self.lock:
            if self.closed:
                return
            self.expire()
            if item.expires <= self.hass.loop.time():
                self.diagnostics["expired_count"] += 1
                return
            media = item.payload["media_identifier"]
            if not media and not self.routes["recording_ready"]:
                # Snapshot-only cameras have no future recording-ready transition.
                media = "snapshot:" + str(item.payload.get("context_id") or item.payload.get("event_id") or
                    (str(item.payload.get("trigger_entity_id")) + str(item.payload.get("occurred_at"))))
                item.payload["media_identifier"] = media
            if not media:
                if len(self.pending) >= MAX_PENDING:
                    self.diagnostics["overflow_count"] += 1
                else:
                    self.pending.append(item)
                    self.diagnostics["last_trace_step"] = "media_wait_started"
            elif media in self.recent or media in self.retries:
                self.diagnostics["duplicate_count"] += 1
            else:
                if item.payload["trigger_type"] == "recording_ready" and self.pending:
                    trigger = self.pending.popleft()
                    trigger.payload["media_identifier"] = media
                    item = trigger
                await self.forward(item)
            self.expire()
            self.schedule_expiry()
            await self.async_report_status()

    async def retry(self, send: bool = True, force: bool = True) -> None:
        async with self.lock:
            if self.closed:
                return
            self.expire()
            if send:
                for media, item in list(self.retries.items()):
                    if item.expires <= self.hass.loop.time() or (
                        not force and item.retry_at > self.hass.loop.time()
                    ):
                        continue
                    del self.retries[media]
                    await self.forward(item)
            self.expire()
            self.schedule_expiry()
            await self.async_report_status()

    async def forward(self, item: PendingEvent) -> None:
        media = item.payload["media_identifier"]
        self.diagnostics.update(
            {
                "last_trace_step": "forward_started",
                "forward_started": True,
                "last_forward_started_at": utcnow().isoformat(),
                "media_ready_detected": True,
                "new_media_detected": True,
                "last_media_id": media,
                "last_error": None,
                "error_code": None,
                "error_stage": None,
                "exception_type": None,
            }
        )
        self.diagnostics["forwarded_count"] += 1
        item.attempts += 1
        # Reserve before awaiting; cancellation/response loss must not allow replay.
        self.recent[media] = "delivery_unknown"
        while len(self.recent) > MAX_RECENT_MEDIA:
            self.recent.popitem(last=False)
        try:
            result = await self.client.async_send_event(item.payload)
        except CamWiseNotSentError:
            del self.recent[media]
            self.keep_retry(media, item)
            self.diagnostics.update(
                {
                    "forward_response": "not_sent",
                    "retryable": bool(media in self.retries),
                    "error_code": "cam_wise_not_sent",
                    "error_stage": "connect",
                }
            )
        except CamWiseApiError:
            self.diagnostics["uncertain_count"] += 1
            self.diagnostics.update(
                {
                    "forward_response": "delivery_unknown",
                    "retryable": False,
                    "error_code": "cam_wise_delivery_unknown",
                    "error_stage": "forward_request",
                }
            )
        else:
            raw_response = result.get("result") or result.get("processing_status")
            response = (
                raw_response if isinstance(raw_response, str) and raw_response in {
                    "accepted", "duplicate", "ignored", "error", "paused",
                    "failed_retryable", "failed_permanent", "waiting_for_recording",
                } else "unknown_response"
            )
            self.diagnostics.update({"forward_response": response, "retryable": False})
            if (
                response == "accepted"
                and result.get("ok") is True
                and result.get("accepted") is not False
            ):
                self.recent[media] = "accepted"
                self.diagnostics["accepted_count"] += 1
            elif response == "duplicate" and result.get("ok") is True:
                self.recent[media] = "duplicate"
            elif result.get("accepted") is False and result.get("retryable") is True:
                del self.recent[media]
                self.keep_retry(media, item)
                self.diagnostics["retryable"] = media in self.retries
            elif result.get("accepted") is False:
                self.recent[media] = "rejected"
            else:
                self.diagnostics["uncertain_count"] += 1
        self.diagnostics["last_trace_step"] = self.diagnostics["forward_response"]

    def keep_retry(self, media: str, item: PendingEvent) -> None:
        if item.attempts < 3 and len(self.retries) < MAX_PENDING:
            item.retry_at = self.hass.loop.time() + 15
            self.retries[media] = item
        else:
            self.recent[media] = "retry_limit_reached"
            self.diagnostics["last_trace_step"] = "retry_limit_reached"

    async def async_report_status(self) -> None:
        if self.closed:
            return
        try:
            payload = dict(self.diagnostics)
            if self.entry.data.get("pairing_token"):
                from homeassistant.helpers import entity_registry as er
                registry = er.async_get(self.hass)
                catalog = []
                for state in self.hass.states.async_all("camera"):
                    registered = registry.async_get(state.entity_id)
                    device = registered.device_id if registered else None
                    related = [s for s in self.hass.states.async_all() if device and
                        (row := registry.async_get(s.entity_id)) and row.device_id == device]
                    motion = next((s.entity_id for s in related if s.domain in {"event", "binary_sensor"} and
                        (s.attributes.get("device_class") == "motion" or "motion" in s.entity_id)), "")
                    ding = next((s.entity_id for s in related if s.domain in {"event", "binary_sensor"} and
                        any(word in s.entity_id for word in ("ding", "doorbell"))), "")
                    catalog.append({"entity_id": state.entity_id,
                        "name": str(state.attributes.get("friendly_name") or state.entity_id)[:120],
                        "motion": motion, "ding": ding,
                        "recording": bool(state.attributes.get("video_url") and state.attributes.get("last_video_id"))})
                http = getattr(self.hass, "http", None)
                payload["bridge_port"] = getattr(http, "server_port", None)
                payload["camera_catalog"] = catalog[:64]
            await self.client.async_report_integration_status(payload)
        except CamWiseApiError:
            _LOGGER.debug("Cam-Wise integration status report unavailable")

    @callback
    def stop_listeners(self) -> None:
        for unsubscribe in self.unsubs:
            unsubscribe()
        self.unsubs.clear()

    async def async_close(self) -> None:
        self.closed = True
        self.stop_listeners()
        if self.timer:
            self.timer.cancel()
            self.timer = None
        tasks = list(self.tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self.tasks.clear()
        self.pending.clear()
        self.retries.clear()
        self.diagnostics.update(
            {
                "integration_loaded": False,
                "listeners_registered": False,
                "unsubscribe_handle_present": False,
                "last_trace_step": "integration_unloaded",
                "pending_count": 0,
                "retry_count": 0,
            }
        )
