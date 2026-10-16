# Compatibility evidence

Measured on 2026-10-16. These observations cover different scopes.

| Check | Result and scope |
| --- | --- |
| HA 2025.2.0 / Python 3.13 | PASS: 89 standalone real-HA tests; hosted dependencies, Ruff and syntax checks |
| HA 2026.10.1 / Python 3.14 | PASS: same 89 tests and isolated real-process lifecycle checks |
| HA 2025.1 or older | Unsupported: required Zeroconf helper import unavailable |
| API 1 | Only supported protocol; schema/client tests and source-runtime E2E |
| HACS 2.0.5 on HA 2026.10.1 | PASS: custom repository recognized, actual download, restart/configuration/three entities/reload/removal |
| Linux Desktop 0.1.23 source with HA 2026.10.1 | PASS: real event, HTTP video/hash, existing ONNX worker, saved detection and Review API/JPEG |
| Windows packaged Desktop E2E | NOT PROVEN: no certified packaged version range |
| Upgrade between released integration versions | NOT TESTED: only branch refresh/same-ref redownload tested |

Hosted [HA tests](https://github.com/Cam-Wise/cam-wise-home-assistant/actions/runs/38944249283),
[HACS](https://github.com/Cam-Wise/cam-wise-home-assistant/actions/runs/38944249286)
and [Hassfest](https://github.com/Cam-Wise/cam-wise-home-assistant/actions/runs/38944249273)
passed on initial source `604e4d7a0d5c281461730f50d8fe2aef4ed8be54`.
Later documentation changes do not expand runtime compatibility claims.

The HACS lifecycle test used real HA/HACS handlers programmatically with a
synthetic Desktop HTTP API. Restart means a new HA process with saved settings.
No visual HACS UI/HAOS, camera-vendor or media-processing claim follows from it.

The separate Linux source E2E used isolated loopback, a fresh data root, synthetic
video/ONNX and a signed synthetic account with temporary test trust. Real
verification and inference ran; duplicates added no extra result. This source-only
fixture is disabled in packaged mode and must not be injected into a signed app.
It does not prove production account issuance, Windows packaging/DPAPI, model
accuracy or real-camera support. UI HTML was fetched, not visually tested.

Installed signed Windows 0.1.23 identity was verified, but the isolated E2E stopped
before startup because no legitimate isolated nonproduction account path was
available. This is an unexecuted test, not an observed product failure. Follow
the [manual Windows plan](windows-test-plan.md); record exact build/hash and scope.
Do not infer compatibility from the `0.1.23` value in synthetic API fixtures.

`accepted` means intake, not `processed`. API 1 has no durable correlated processing
receipt; HA restarts discard pending work and FIFO media association is heuristic.
HTTP is unauthenticated/unencrypted and restricted to a trusted LAN. Desktop and
integration releases remain independent; no packaged minimum version is claimed.
