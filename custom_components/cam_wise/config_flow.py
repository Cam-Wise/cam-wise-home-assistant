"""Config flow for Cam-Wise Zeroconf and manual discovery."""

from __future__ import annotations

from typing import Any
import hashlib
import secrets

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult
from homeassistant.core import State, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .client import (
    CamWiseApiClient,
    CamWiseConnectionError,
    CamWiseUnsupportedApiError,
    normalize_host,
)
from .const import (
    CONF_CAMERA_ENTITY,
    CONF_DING_ENTITY,
    CONF_HOST,
    CONF_MOTION_ENTITY,
    CONF_PORT,
    CONF_RECORDING_ENTITY,
    DEFAULT_PORT,
    DOMAIN,
)

from .events import ROLE_DOMAINS, mapping_errors

CONF_USE_RECOMMENDED = "use_recommended"
CONF_CHOOSE_ENTITIES = "choose_entities"

_ROLE_LABELS = {
    CONF_CAMERA_ENTITY: "Camera",
    CONF_MOTION_ENTITY: "Motion event",
    CONF_DING_ENTITY: "Doorbell event",
    CONF_RECORDING_ENTITY: "Recording source",
}

_MOTION_WORDS = ("motion", "beweging")
_DING_WORDS = ("ding", "doorbell", "deurbel")
_RECORDING_WORDS = ("recording", "last_video", "video_url", "opname")


def _schema(default_host: str | None = None, default_port: int = DEFAULT_PORT) -> vol.Schema:
    host_key = vol.Required(CONF_HOST, default=default_host) if default_host else vol.Required(CONF_HOST)
    return vol.Schema(
        {
            host_key: str,
            vol.Required(CONF_PORT, default=default_port): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
            ),
        }
    )


class CamWiseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up Cam-Wise from Zeroconf or user input."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered: dict[str, Any] | None = None
        self._info: dict[str, Any] | None = None
        self._pair_token: str | None = None
        self._pair_code = ""
        self._reauth_entry: ConfigEntry | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> CamWiseOptionsFlow:
        return CamWiseOptionsFlow()

    async def _async_validate(self, host: str, port: int) -> dict[str, Any]:
        client = CamWiseApiClient(async_get_clientsession(self.hass), host, port)
        return await client.async_validate()

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle a Cam-Wise mDNS service."""
        host = normalize_host(discovery_info.host)
        port = int(discovery_info.port)
        try:
            info = await self._async_validate(host, port)
        except CamWiseUnsupportedApiError:
            return self.async_abort(reason="unsupported_api_version")
        except (CamWiseConnectionError, ValueError):
            return self.async_abort(reason="cannot_connect")

        for entry in self._async_current_entries():
            if entry.unique_id == str(info["device_id"]) and info.get("pairing_required") and not entry.data.get("pairing_token"):
                # Do not silently move a working legacy entry to a token-only port.
                return self.async_abort(reason="already_configured")
            if entry.unique_id == str(info["device_id"]) and entry.data.get("pairing_token"):
                client = CamWiseApiClient(async_get_clientsession(self.hass), host, port, entry.data["pairing_token"])
                try:
                    status = await client.async_status()
                    if status.get("device_id") != entry.unique_id:
                        return self.async_abort(reason="cannot_connect")
                except CamWiseConnectionError:
                    return self.async_abort(reason="cannot_connect")
        await self.async_set_unique_id(str(info["device_id"]))
        self._abort_if_unique_id_configured(
            updates={CONF_HOST: host, CONF_PORT: port}
        )
        self.context["title_placeholders"] = {"name": "Cam-Wise"}
        self._discovered = {CONF_HOST: host, CONF_PORT: port}
        self._info = info
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask the user to confirm a discovered Cam-Wise instance."""
        if self._discovered is None or self._info is None:
            return self.async_abort(reason="discovery_expired")
        if user_input is not None:
            if self._info.get("pairing_required"):
                return await self.async_step_pair()
            environment = str(self._info.get("environment") or "unknown")
            return self.async_create_entry(
                title=f"Cam-Wise ({environment})", data=self._discovered
            )
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "host": self._discovered[CONF_HOST],
                "port": str(self._discovered[CONF_PORT]),
                "version": str(self._info.get("version") or "unknown"),
                "environment": str(self._info.get("environment") or "unknown"),
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual host/IP setup."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                host = normalize_host(user_input[CONF_HOST])
                port = int(user_input[CONF_PORT])
                info = await self._async_validate(host, port)
            except ValueError:
                errors["base"] = "invalid_host"
            except CamWiseUnsupportedApiError:
                errors["base"] = "unsupported_api_version"
            except CamWiseConnectionError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(str(info["device_id"]))
                self._abort_if_unique_id_configured()
                if info.get("pairing_required"):
                    self._discovered = {CONF_HOST: host, CONF_PORT: port}
                    self._info = info
                    return await self.async_step_pair()
                return self.async_create_entry(
                    title=f"Cam-Wise ({info.get('environment', 'unknown')})",
                    data={CONF_HOST: host, CONF_PORT: port},
                )
        return self.async_show_form(
            step_id="user", data_schema=_schema(), errors=errors
        )

    async def async_step_pair(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._discovered is None or self._info is None:
            return self.async_abort(reason="discovery_expired")
        if user_input and user_input.get("new_request"):
            self._pair_token = None
            self._pair_code = ""
        client = CamWiseApiClient(async_get_clientsession(self.hass),
            self._discovered[CONF_HOST], self._discovered[CONF_PORT], self._pair_token)
        errors = {}
        try:
            if self._pair_token is None:
                self._pair_token = secrets.token_urlsafe(32)
                verifier = hashlib.sha256(self._pair_token.encode()).hexdigest()
                response = await client.async_request_pairing(verifier)
                if response.get("code") != verifier[:6].upper():
                    raise CamWiseConnectionError("Invalid pairing response")
                self._pair_code = verifier[:6].upper()
            elif user_input is not None:
                status = await client.async_status()
                if status.get("device_id") != self._info["device_id"]:
                    return self.async_abort(reason="cannot_connect")
                if self._reauth_entry is not None:
                    return self.async_update_reload_and_abort(self._reauth_entry,
                        data_updates={"pairing_token": self._pair_token}, reason="reauth_successful")
                return self.async_create_entry(title=f"Cam-Wise ({self._info.get('environment', 'unknown')})",
                    data={**self._discovered, "pairing_token": self._pair_token})
        except CamWiseConnectionError:
            if not self._pair_code:
                self._pair_token = None
            errors["base"] = "cannot_connect"
        return self.async_show_form(step_id="pair", data_schema=vol.Schema({vol.Optional("new_request", default=False): bool}),
            errors=errors, description_placeholders={"code": self._pair_code})

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        self._reauth_entry = self._get_reauth_entry()
        self._discovered = {CONF_HOST: entry_data[CONF_HOST], CONF_PORT: entry_data[CONF_PORT]}
        try:
            self._info = await self._async_validate(entry_data[CONF_HOST], entry_data[CONF_PORT])
        except (CamWiseConnectionError, CamWiseUnsupportedApiError):
            return self.async_abort(reason="cannot_connect")
        if self._info["device_id"] != self._reauth_entry.unique_id or not self._info.get("pairing_required"):
            return self.async_abort(reason="cannot_connect")
        return await self.async_step_pair()

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update the address while ensuring it is still the same Cam-Wise."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                host = normalize_host(user_input[CONF_HOST])
                port = int(user_input[CONF_PORT])
                info = await self._async_validate(host, port)
                if entry.data.get("pairing_token"):
                    client = CamWiseApiClient(async_get_clientsession(self.hass), host, port, entry.data["pairing_token"])
                    await client.async_status()
            except ValueError:
                errors["base"] = "invalid_host"
            except CamWiseUnsupportedApiError:
                errors["base"] = "unsupported_api_version"
            except CamWiseConnectionError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(str(info["device_id"]))
                if str(info["device_id"]) != str(entry.unique_id):
                    errors["base"] = "different_device"
                else:
                    self._abort_if_unique_id_mismatch()
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={CONF_HOST: host, CONF_PORT: port},
                    )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_schema(
                str(entry.data[CONF_HOST]), int(entry.data[CONF_PORT])
            ),
            errors=errors,
        )


class CamWiseOptionsFlow(config_entries.OptionsFlow):
    """Choose the HA entities whose changes Cam-Wise should receive."""

    def __init__(self) -> None:
        self._suggestion: dict[str, Any] | None = None

    async def _async_status(self) -> dict[str, Any]:
        host = self.config_entry.data[CONF_HOST]
        port = int(self.config_entry.data[CONF_PORT])
        client = CamWiseApiClient(async_get_clientsession(self.hass), host, port)
        try:
            return await client.async_status()
        except (CamWiseConnectionError, CamWiseUnsupportedApiError, ValueError):
            return {}

    def _state_label(self, entity_id: str) -> str:
        state = self.hass.states.get(entity_id) if entity_id else None
        if state is None:
            return entity_id
        return str(state.attributes.get("friendly_name") or entity_id)

    def _states(self) -> list[State]:
        return self.hass.states.async_all()

    @staticmethod
    def _entity_id(state: State) -> str:
        return state.entity_id

    @staticmethod
    def _entity_text(state: State) -> str:
        attrs = state.attributes
        return " ".join(
            str(value or "")
            for value in (
                state.entity_id,
                attrs.get("friendly_name"),
                attrs.get("device_class"),
                attrs.get("manufacturer"),
                attrs.get("platform"),
                attrs.get("integration"),
            )
        ).casefold()

    @staticmethod
    def _shared_stem(entity_id: str) -> str:
        object_id = entity_id.split(".", 1)[1] if "." in entity_id else entity_id
        lowered = object_id.casefold()
        for suffix in (
            "_live_weergave",
            "_live_view",
            "_camera",
            "_motion",
            "_beweging",
            "_ding",
            "_doorbell",
            "_recording",
            "_last_video_id",
        ):
            if lowered.endswith(suffix):
                lowered = lowered[: -len(suffix)]
        return lowered.split("_", 1)[0] or lowered

    def _state_score(self, state: State, words: tuple[str, ...], stem: str | None) -> int:
        text = self._entity_text(state)
        score = sum(10 for word in words if word in text)
        if stem and stem in self._shared_stem(self._entity_id(state)):
            score += 8
        attrs = state.attributes
        if attrs.get("device_id") or attrs.get("ha_device_id"):
            score += 4
        if any(word in text for word in ("ring", "reolink")):
            score += 3
        return score

    def _local_route_options(self) -> dict[str, str]:
        states = self._states()
        camera_states = [state for state in states if self._entity_id(state).startswith("camera.")]
        camera = max(
            camera_states,
            key=lambda state: self._state_score(state, ("doorbell", "voordeur", "front", "camera"), None),
            default=None,
        )
        camera_id = self._entity_id(camera) if camera is not None else ""
        stem = self._shared_stem(camera_id) if camera_id else None
        selected: set[str] = set()

        def choose(role: str, words: tuple[str, ...]) -> str:
            candidates = [state for state in states
                          if state.domain in ROLE_DOMAINS[role]
                          and state.entity_id not in selected
                          and (any(word in self._entity_text(state) for word in words)
                               or (role == "recording_ready" and any(
                                   state.attributes.get(key) for key in
                                   ("last_video_id", "media_id", "video_id"))))]
            chosen = max(candidates, key=lambda state: self._state_score(state, words, stem), default=None)
            if chosen is None:
                return ""
            selected.add(chosen.entity_id)
            return chosen.entity_id

        route_options = {
            CONF_CAMERA_ENTITY: camera_id,
            CONF_MOTION_ENTITY: choose("motion", _MOTION_WORDS),
            CONF_DING_ENTITY: choose("ding", _DING_WORDS),
            CONF_RECORDING_ENTITY: choose("recording_ready", _RECORDING_WORDS),
        }
        return {key: value for key, value in route_options.items() if value}

    def _mapping_errors(self, options: dict[str, str]) -> dict[str, str]:
        keys = {"camera": CONF_CAMERA_ENTITY, "motion": CONF_MOTION_ENTITY,
                "ding": CONF_DING_ENTITY, "recording_ready": CONF_RECORDING_ENTITY}
        routes = {role: options.get(key, "") for role, key in keys.items()}
        return {keys[role]: "invalid_mapping" for role in mapping_errors(routes, self.hass)}

    def _suggestion_from_options(self, route_options: dict[str, str]) -> dict[str, Any] | None:
        if self._mapping_errors(route_options) or not route_options.get(CONF_CAMERA_ENTITY):
            return None
        if not any(route_options.get(key) for key in (CONF_MOTION_ENTITY, CONF_DING_ENTITY, CONF_RECORDING_ENTITY)):
            return None
        camera_label = self._state_label(route_options[CONF_CAMERA_ENTITY])
        brand = "Ring" if "ring" in camera_label.casefold() else None
        device_label = f"{brand} - {camera_label}" if brand and not camera_label.casefold().startswith("ring") else camera_label
        found = [
            label
            for key, label in _ROLE_LABELS.items()
            if route_options.get(key)
        ]
        return {
            "route_options": route_options,
            "device_label": device_label,
            "found": ", ".join(found),
        }

    async def _async_suggest_mapping(self) -> dict[str, Any] | None:
        current = {**self.config_entry.data, **self.config_entry.options}
        route_options = {
            key: str(current.get(key) or "").strip()
            for key in (
                CONF_CAMERA_ENTITY,
                CONF_MOTION_ENTITY,
                CONF_DING_ENTITY,
                CONF_RECORDING_ENTITY,
            )
        }
        if not any(route_options.values()):
            status = await self._async_status()
            recommended = status.get("recommended_route_options") or {}
            route_options = {
                key: str(recommended.get(key) or "").strip()
                for key in route_options
            }
        if not any(route_options.values()):
            route_options = self._local_route_options()
        return self._suggestion_from_options(route_options)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            if user_input.get(CONF_CHOOSE_ENTITIES) or not user_input.get(CONF_USE_RECOMMENDED, True):
                return await self.async_step_advanced()
            suggestion = self._suggestion
            if suggestion is None:
                suggestion = await self._async_suggest_mapping()
            if suggestion is not None:
                return self.async_create_entry(
                    title="",
                    data={**self.config_entry.options, **suggestion["route_options"]},
                )
            return await self.async_step_advanced()

        self._suggestion = await self._async_suggest_mapping()
        if self._suggestion is not None:
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_USE_RECOMMENDED, default=True): bool,
                        vol.Optional(CONF_CHOOSE_ENTITIES, default=False): bool,
                    }
                ),
                description_placeholders={
                    "device": self._suggestion["device_label"],
                    "found": self._suggestion["found"],
                },
            )
        return await self.async_step_advanced()

    async def async_step_advanced(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            cleaned = {
                key: str(value or "").strip()
                for key, value in user_input.items()
            }
            errors = self._mapping_errors(cleaned)
            if not errors:
                return self.async_create_entry(
                    title="", data={**self.config_entry.options, **cleaned}
                )
        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="advanced",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_CAMERA_ENTITY,
                        default=current.get(CONF_CAMERA_ENTITY, ""),
                    ): str,
                    vol.Optional(
                        CONF_RECORDING_ENTITY,
                        default=current.get(CONF_RECORDING_ENTITY, ""),
                    ): str,
                    vol.Optional(
                        CONF_MOTION_ENTITY,
                        default=current.get(CONF_MOTION_ENTITY, ""),
                    ): str,
                    vol.Optional(
                        CONF_DING_ENTITY,
                        default=current.get(CONF_DING_ENTITY, ""),
                    ): str,
                }
            ),
        )
