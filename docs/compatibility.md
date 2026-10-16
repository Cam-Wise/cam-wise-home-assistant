# Compatibility evidence

| Component | Boundary | Evidence |
| --- | --- | --- |
| Home Assistant minimum | 2025.2.0 / Python 3.13 | Standalone real HA fixture suite; round-3 results recorded in validation report |
| Home Assistant current tested | 2026.10.1 / Python 3.14 | Same suite and isolated runtime smoke where executable |
| HA 2025.1 or older | Unsupported | Canonical Zeroconf helper import unavailable |
| Cam-Wise API | `1` only | Synthetic fixtures and client validation |
| Desktop 0.1.23 source with HA 2026.10.1 | Actual isolated Linux source proof | Real HA event, signed synthetic Free account, HTTP media/hash, existing ONNX worker, saved candidate/image and Review API; prior setup/reload/remove proof |
| Desktop packaged versions | Not established | No actual desktop integration run in this preparation round |

Only the specific Desktop 0.1.23 source snapshot with HA 2026.10.1 has this
functional proof; no packaged desktop version range is certified. The `0.1.23`
value in API fixtures alone is synthetic metadata, not compatibility certification.
Earlier/future desktop versions need contract and actual media tests; do not infer
compatibility from product version alone. Record exact desktop version/build, HA
version, install method and tested camera route before approving a compatibility
statement. Independent desktop updates are not blocked by integration development.

The completed source-runtime E2E used an approved new empty data-root, loopback
port 8017, no external network route, temporary signing keys/trust anchor, an
existing source-only synthetic account bootstrap and synthetic HTTP video/ONNX.
Real verification and inference were used. A repeated media event added no second
download or candidate; invalid signature/non-video/invalid trigger/stop cases were
rejected. The Review API and image succeeded; UI HTML loaded but was not rendered
in a browser. Windows packaging/DPAPI, production account issuance, real camera
behavior and model accuracy were not tested. Pending events remain volatile and
HA diagnostics still cannot certify background processing from acceptance alone.
