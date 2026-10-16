# Security policy

## Supported scope and reporting

The proposed first maintained candidate is `0.1.0-beta.1` (API 1). Send security
reports privately to **support@cam-wise.com**, the owner-supplied confidential route.
Do not post exploit details, credentials or camera data in GitHub Issues.
Security reports are handled confidentially. Access to this mailbox is restricted
to authorized people, and it is monitored for security reports. There is no
guaranteed response or fix time.
Support for ordinary bugs is [GitHub Issues](https://github.com/cam-wise/cam-wise-home-assistant/issues)
in the public repository. Codeowner: `@Bob-Cam-Wise`. You may also use
[GitHub private vulnerability reporting](https://github.com/Cam-Wise/cam-wise-home-assistant/security/advisories/new).
The first maintained release candidate is prepared; no beta tag/release exists yet.
After release, security maintenance targets the latest beta without a response-time guarantee.

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

Use this integration only on an explicitly trusted LAN. HACS custom installation
and lifecycle checks passed, but they do not establish Desktop listener security
or packaged Windows E2E compatibility. Windows packaged E2E remains NOT PROVEN.
See [compatibility](docs/compatibility.md) for the Linux source-runtime evidence.
`accepted` is not `processed`; do not use acceptance as a safety-critical receipt.
Internet/untrusted-LAN use is unsupported. Authenticated transport would require
a separate Desktop/API design; no such protection is provided by API 1.

HTTP redirects are not followed. Non-2xx outcomes are unknown for event delivery,
never safe-not-sent evidence. Unexpected result labels are normalized before diagnostics.
