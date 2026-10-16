# v0.1.0-beta.1 — draft release notes

Prepared for a separately approved GitHub prerelease; no tag or release exists yet.

This first integration beta connects HA camera events to Cam-Wise's local review
workflow and exposes status, review-count and attention entities. Media retrieval,
storage and inference run in Desktop. Desktop has an independent release process.

## Tested scope

- HA 2025.2.0/Python 3.13 and HA 2026.10.1/Python 3.14: 89 tests each; hosted Ruff,
  dependency/syntax checks, HACS Action and Hassfest pass.
- HACS custom installation: PASS with HACS 2.0.5 on HA 2026.10.1, including actual
  download, separate-process restart, configure/entities/reload and removal.
- Linux Desktop 0.1.23 source-runtime E2E: PASS through HTTP media download,
  existing ONNX worker and Review API/image.
- Windows packaged E2E: NOT PROVEN. No packaged Desktop compatibility range is
  certified. The [Windows test plan](windows-test-plan.md) is a plan, not evidence.

## Limits and installation

API 1 uses HTTP without authentication or encryption: trusted LAN only; no public
proxy/port-forwarding or guest-network exposure. `accepted` means background
intake, not `processed`. Pending/retry/dedup state is volatile across HA restarts;
media association may be heuristic and unknown delivery may lose an event.

Use the [HACS custom-repository instructions](installation.md). Official HACS
default-list inclusion has not been requested. Before approving these notes,
record the exact released commit and confirm prerelease selection in HACS; the
existing installation proof covers branch source. Released-version install and
later version-to-version update/rollback still need their own evidence.

Report functional bugs through GitHub Issues without credentials or footage;
security reports use GitHub private reporting or support@cam-wise.com.
MIT applies to integration software/documentation; Cam-Wise branding has separate terms.
