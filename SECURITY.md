# Security policy

## Supported scope and reporting

The proposed first maintained candidate is `0.1.0-beta.1` (API 1). Send security
reports privately to **support@cam-wise.com**, the owner-supplied confidential route.
Do not post exploit details, credentials or camera data in GitHub Issues.
Security reports are handled confidentially. Access to this mailbox is restricted
to authorized people, and it is monitored for security reports. There is no
guaranteed response or fix time.
Support for ordinary bugs is [GitHub Issues](https://github.com/cam-wise/cam-wise-home-assistant/issues)
in the intended repository (not yet created/published). Codeowner: `@Bob-Cam-Wise`.
Publication and release still require separate explicit approval.

## Threat model

The desktop local API uses HTTP without authentication. LAN opt-in and firewall
restrictions are deployment controls, not sender authentication. An untrusted LAN
peer can read exposed status, spoof discovery/status and inject events or route
diagnostics. Traffic interception can disclose entity/media identifiers and
operational state. Forged events can trigger expensive retrieval/processing.
Do not expose the API through port forwarding, public reverse proxies or guest
networks. Restrict the desktop listener to explicitly trusted HA peers. Use a
segmented trusted LAN; a compromised HA host is within this trust boundary.

The integration validates host syntax, API identity/version, required response
types and entity mappings; bounds pending work/retries; uses static paths and
does not execute received code. These controls cannot authenticate a LAN peer.
HTTP errors/unknown delivery are not blindly retried. Event association is heuristic.

Diagnostics whitelist operational fields and redact configured host/entity IDs.
They omit raw payloads/media IDs/tokens; server-provided strings still require human review. Desktop status reports contain route/media
metadata and are not anonymous. Logs use generic client errors; third-party HA
and desktop logs need separate review. No telemetry or external cloud request is
introduced by the integration itself.

## Distribution decision

Explicit trusted-LAN use with documented limitations is a possible beta policy,
subject to final owner confirmation and real installation evidence. Internet/untrusted-LAN
use is blocked. If authenticated transport is required for the intended audience,
stop that scope and approve a separate desktop/API design task. This repository
does not invent an authentication protocol or promise security it cannot enforce.

HTTP redirects are not followed. Non-2xx outcomes are unknown for event delivery,
never safe-not-sent evidence. Unexpected result labels are normalized before diagnostics.
