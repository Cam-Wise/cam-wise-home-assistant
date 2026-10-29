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
The maintained beta is `0.1.0-beta.1`, a limited developer-preview prerelease.
Security maintenance targets the latest beta without a response-time guarantee;
Windows packaged E2E remains NOT PROVEN.

## Unreleased paired candidate

The unreleased candidate adds explicit local discovery/pairing and revocable,
installation-scoped capabilities. The general Desktop API stays on loopback;
the separate HA listener exposes only the approved integration operations. Camera
reads require both the pairing capability and authorization for that camera.
Revocation denies subsequent bridge reads. Vendor credentials remain in HA.

Trusted-home HTTP is an explicit opt-in, not encrypted transport. A local attacker
able to intercept traffic can steal a bearer capability; a compromised HA host is
inside this trust boundary. Do not expose either service to the Internet or guest
networks. Discovery alone never authenticates a peer. Pairing does not grant access
to Desktop accounts, datasets, models, training or general management APIs.

Recording reads are bounded. Ring recording redirects are the only newly permitted
vendor redirect path: at most three hops, with every HTTPS origin checked before
connection and no incoming browser/pairing headers forwarded. General Desktop/HA
API redirects remain refused. Recording capture times must come from the source;
discovery/download times are not substitutes. See the current
[release compatibility gates](docs/release-integration-gates-20261029.md).

## Historical published beta threat model

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

## Historical published beta distribution decision

Use this integration only on an explicitly trusted LAN. HACS custom installation
and lifecycle checks passed, but they do not establish Desktop listener security
or packaged Windows E2E compatibility. Windows packaged E2E remains NOT PROVEN.
See [compatibility](docs/compatibility.md) for the Linux source-runtime evidence.
`accepted` is not `processed`; do not use acceptance as a safety-critical receipt.
Internet/untrusted-LAN use is unsupported. Authenticated transport would require
a separate Desktop/API design; no such protection is provided by API 1.

HTTP redirects are not followed. Non-2xx outcomes are unknown for event delivery,
never safe-not-sent evidence. Unexpected result labels are normalized before diagnostics.
