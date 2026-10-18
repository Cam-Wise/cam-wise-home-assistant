"""Small async client for Cam-Wise's secret-free local API."""

from __future__ import annotations

from ipaddress import IPv6Address
import re
from typing import Any

from aiohttp import (
    ClientConnectorError,
    ClientError,
    ClientResponseError,
    ClientSession,
    ClientTimeout,
)

from .const import (
    DISCOVERY_PATH,
    EVENT_PATH,
    HEALTH_PATH,
    INTEGRATION_STATUS_PATH,
    STATUS_PATH,
    SUPPORTED_API_VERSION,
)


class CamWiseApiError(Exception):
    """Base Cam-Wise client error."""


class CamWiseConnectionError(CamWiseApiError):
    """Cam-Wise could not be reached or returned an invalid payload."""


class CamWiseAuthError(CamWiseConnectionError):
    """Desktop approval is missing or revoked."""


class CamWiseNotSentError(CamWiseConnectionError):
    """Connection establishment failed before sending the HTTP request."""


class CamWiseUnsupportedApiError(CamWiseApiError):
    """The Cam-Wise API version is not supported by this integration."""


def normalize_host(value: str) -> str:
    host = str(value or "").strip()
    if host.casefold().startswith("https://"):
        raise ValueError("HTTPS is not supported by API version 1")
    if host.casefold().startswith("http://"):
        host = host[7:]
    host = host.rstrip("./")
    if ":" in host:
        try:
            IPv6Address(host.removeprefix("[").removesuffix("]"))
        except ValueError as err:
            raise ValueError("invalid host") from err
    elif not re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?", host):
        raise ValueError("invalid host")
    return host


def base_url(host: str, port: int) -> str:
    normalized = normalize_host(host)
    if ":" in normalized and not normalized.startswith("["):
        normalized = f"[{normalized}]"
    return f"http://{normalized}:{int(port)}"


class CamWiseApiClient:
    """Local Cam-Wise status and event API client."""

    def __init__(self, session: ClientSession, host: str, port: int, token: str | None = None) -> None:
        self._token = token
        self.host = normalize_host(host)
        self.port = int(port)
        self._session = session
        self._base_url = base_url(self.host, self.port)
        self._timeout = ClientTimeout(total=10)

    async def _get_json(self, path: str) -> dict[str, Any]:
        try:
            async with self._session.get(
                f"{self._base_url}{path}", timeout=self._timeout, allow_redirects=False,
                **({"headers": {"Authorization": f"Bearer {self._token}"}} if self._token else {})
            ) as response:
                if response.status == 401:
                    raise CamWiseAuthError("Desktop approval required")
                response.raise_for_status()
                if not 200 <= response.status < 300:
                    raise CamWiseConnectionError(
                        "Cam-Wise returned an unexpected HTTP status"
                    )
                payload = await response.json(content_type=None)
        except (ClientResponseError, ClientError, TimeoutError, ValueError) as err:
            raise CamWiseConnectionError("Cannot connect to Cam-Wise") from err
        if not isinstance(payload, dict):
            raise CamWiseConnectionError("Cam-Wise returned an invalid response")
        return payload

    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with self._session.post(
                f"{self._base_url}{path}",
                json=payload,
                timeout=self._timeout,
                allow_redirects=False,
                **({"headers": {"Authorization": f"Bearer {self._token}"}} if self._token else {}),
            ) as response:
                if response.status == 401:
                    raise CamWiseAuthError("Desktop approval required")
                response.raise_for_status()
                if not 200 <= response.status < 300:
                    raise CamWiseConnectionError(
                        "Cam-Wise returned an unexpected HTTP status"
                    )
                result = await response.json(content_type=None)
        except ClientConnectorError as err:
            raise CamWiseNotSentError("Cannot establish Cam-Wise connection") from err
        except (ClientResponseError, ClientError, TimeoutError, ValueError) as err:
            raise CamWiseConnectionError("Cannot send data to Cam-Wise") from err
        if not isinstance(result, dict):
            raise CamWiseConnectionError("Cam-Wise returned an invalid response")
        return result

    async def async_validate(self) -> dict[str, Any]:
        health = await self._get_json(HEALTH_PATH)
        if health.get("status") != "ok":
            raise CamWiseConnectionError("Cam-Wise health check failed")
        info = await self._get_json(DISCOVERY_PATH)
        if (
            info.get("product") != "Cam-Wise"
            or not isinstance(info.get("device_id"), str)
            or not info["device_id"].strip()
        ):
            raise CamWiseConnectionError("This endpoint is not Cam-Wise")
        if str(info.get("api_version")) != SUPPORTED_API_VERSION:
            raise CamWiseUnsupportedApiError(str(info.get("api_version") or "unknown"))
        return info

    async def async_status(self) -> dict[str, Any]:
        status = await self._get_json(STATUS_PATH)
        if str(status.get("api_version")) != SUPPORTED_API_VERSION:
            raise CamWiseUnsupportedApiError(
                str(status.get("api_version") or "unknown")
            )
        for key in ("status", "review_queue", "attention_required"):
            if key not in status:
                raise CamWiseConnectionError(
                    "Cam-Wise returned an incomplete status response"
                )
        if (
            not isinstance(status["status"], str)
            or not status["status"]
            or type(status["review_queue"]) is not int
            or status["review_queue"] < 0
            or type(status["attention_required"]) is not bool
        ):
            raise CamWiseConnectionError("Cam-Wise returned invalid status values")
        for key in ("version", "environment"):
            if key in status and not isinstance(status[key], str):
                raise CamWiseConnectionError("Cam-Wise returned invalid metadata")
        recommended = status.get("recommended_route_options")
        if recommended is not None and (
            not isinstance(recommended, dict)
            or any(
                value is not None and not isinstance(value, str)
                for value in recommended.values()
            )
        ):
            raise CamWiseConnectionError("Cam-Wise returned an invalid mapping")
        return status

    async def async_request_pairing(self, verifier: str) -> dict[str, Any]:
        return await self._post_json("/integrations/home-assistant/pair", {"verifier": verifier})

    async def async_send_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._post_json(EVENT_PATH, payload)

    async def async_report_integration_status(
        self, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return await self._post_json(INTEGRATION_STATUS_PATH, payload)
