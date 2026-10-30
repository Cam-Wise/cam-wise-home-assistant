# Compatibility evidence

## Current recording candidate — 2026-10-30

This section supersedes historical transport/security and recording claims below.
The candidate remains 0.1.1b0, unpublished; it is not the prepared old v0.1.0.
Recording contract 2 is required on both authenticated peers and every recording
request. Pairing and explicit revocable authorization are required. Missing or
incompatible contracts block automatic video intake; updating only one peer does
not authorize fallback to the old intake behavior.

- HA 2025.2.0/Python 3.13 and HA 2026.10.1/Python 3.14: 187 tests pass per version
  on the current candidate, including diagnostics contract reporting. Dependency
  checks, Ruff, Bandit, workflow lint and full local Hassfest pass.
- Reolink and Ring have historical physical recording-input evidence within the
  tested routes. The new contract/DST candidate has not yet passed physical
  Windows video-to-ONNX-to-Review acceptance; earlier evidence does not certify it.
- Older five-part Reolink FILE sources, including the tested HA 2025.2.0 source,
  are blocked for automatic video input. General integration remains supported.
  Seven-part sources require valid device clock and historical DST rules;
  ambiguous or invalid per-record times are skipped, never guessed.
- UniFi Protect, Tapo Cameras Control and Blink have source tests only; physical
  validation is outstanding. No all-model or all-firmware claim is made.
- Activation admits at most one newest completed recording, then new captures
  only; reconnect does not import historical backlog. The stability guard is 30s.
  Source tests establish these rules; physical acceptance is still required.

Update Desktop to a contract-2 build first; video input must stay blocked until
the matching integration is installed and HA restarted. Verify authenticated
contract 2 on both peers before enabling intake. An old peer is safe only while
the new peer blocks recording input. Rolling both peers back to versions without
contract 2 is **not a proven safe rollback**. Preserve backups and pause input
before recovery; do not remove cameras or change datasets to make a test pass.

## Historical evidence (through 2026-10-17)

Updated 2026-10-17. These observations cover different scopes.

| Check | Result and scope |
| --- | --- |
| HA 2025.2.0 / Python 3.13 | PASS: 89 standalone real-HA tests; hosted dependencies, Ruff and syntax checks |
| HA 2026.10.1 / Python 3.14 | PASS: same 89 tests and isolated real-process lifecycle checks |
| HA 2025.1 or older | Unsupported: required Zeroconf helper import unavailable |
| API 1 | Only supported protocol; schema/client tests and source-runtime E2E |
| HACS 2.0.5 on HA 2026.10.1 | PASS: custom repository recognized; exact v0.1.0-beta.1 prerelease installed with beta visibility enabled; restart/configuration/three entities/reload/removal |
| Linux Desktop 0.1.23 source with HA 2026.10.1 | PASS: real event, HTTP video/hash, existing ONNX worker, saved detection and Review API/JPEG |
| Signed Windows Desktop 0.1.23 beta with HA 2026.10.1 | PASS: configuration, motion event, video download, ONNX inference, Review/image, status, reload, actual shutdown/restart/reconnect and removal via loopback transport relay; no direct LAN/mDNS or other Desktop-version claim |
| Upgrade between released integration versions | NOT TESTED: only branch refresh/same-ref redownload tested |

Hosted [HA tests](https://github.com/Cam-Wise/cam-wise-home-assistant/actions/runs/38944249283),
[HACS](https://github.com/Cam-Wise/cam-wise-home-assistant/actions/runs/38944249286)
and [Hassfest](https://github.com/Cam-Wise/cam-wise-home-assistant/actions/runs/38944249273)
passed on initial source `604e4d7a0d5c281461730f50d8fe2aef4ed8be54`.
A fresh tagged-version test also passed for prerelease `v0.1.0-beta.1` at commit
`21516f8bff9fc8742bc215a602971a2b674f724d`, with the normal HACS install path
`<HA config>/custom_components/cam_wise`. This does not expand Desktop compatibility
claims. Only one release exists; update/rollback between versions remains untested.

The HACS lifecycle test used real HA/HACS handlers programmatically with a
synthetic Desktop HTTP API. Restart means a new HA process with saved settings.
No visual HACS UI/HAOS, camera-vendor or media-processing claim follows from it.

The separate Linux source E2E used isolated loopback, a fresh data root, synthetic
video/ONNX and a signed synthetic account with temporary test trust. Real
verification and inference ran; duplicates added no extra result. This source-only
fixture is disabled in packaged mode and must not be injected into a signed app.
It does not prove production account issuance, Windows packaging/DPAPI, model
accuracy or real-camera support. UI HTML was fetched, not visually tested.

On 2026-10-17, the actual signed Windows Desktop 0.1.23 beta passed functional E2E
with actual HA 2026.10.1/Python 3.14, an isolated Windows profile/data root and a
legitimate separately coupled Free account. Synthetic motion/video and an actual
input-dependent ONNX graph exercised the unchanged packaged worker. One media
download produced a Review detection and JPEG; status/review count/attention
updated. Reload preserved mapping/entity IDs. Normal Desktop shutdown, actual
restart, reconnect, Review persistence, entry removal and process/WebView/listener
release passed. No account fixture, product patch, test trust or signature bypass
was used. The signed EXE SHA-256 was
`47fa791a04bec1b7e3b9f24435079ac6a3b3415bc08e67fffcefc78a727e9f11`.

HA ran in WSL; a loopback transport relay forwarded real HTTP requests to the
Windows API without synthesizing Desktop responses. Desktop LAN remained disabled.
This does not prove direct LAN/mDNS, other Desktop versions, HA-minimum full Windows
E2E, visual HAOS/HACS UI, real camera-vendor support or model accuracy. The earlier
preflight account blocker is superseded for this exact build/route; no packaged
version range is certified. See the [Windows reproduction plan](windows-test-plan.md).
Internal logs, account data and camera media are not distributed with this evidence
summary. Synthetic API fixture version strings alone are not compatibility proof.

`accepted` means intake, not `processed`. API 1 has no durable correlated processing
receipt; HA restarts discard pending work and FIFO media association is heuristic.
HTTP is unauthenticated/unencrypted and restricted to a trusted LAN. Desktop and
integration releases remain independent; no packaged minimum version is claimed.
