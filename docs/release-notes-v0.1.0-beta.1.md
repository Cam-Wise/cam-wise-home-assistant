# v0.1.0-beta.1 — developer-preview release notes

Published 2026-10-16 as a Pre-release, not a stable/Latest release. Limited developer
preview; **Windows packaged E2E: NOT PROVEN.** Exact source commit:
`21516f8bff9fc8742bc215a602971a2b674f724d`. No binary assets.

This first integration beta connects HA camera events to Cam-Wise's local review
workflow and exposes status, review-count and attention entities. Media retrieval,
storage and inference run in Desktop. Desktop has an independent release process.

## Tested scope

- HA 2025.2.0/Python 3.13 and HA 2026.10.1/Python 3.14: 89 tests each; hosted Ruff,
  dependency/syntax checks, HACS Action and Hassfest pass.
- Exact `v0.1.0-beta.1` prerelease installation: PASS with HACS 2.0.5 on fresh
  HA 2026.10.1 after enabling beta visibility, including download to
  `<HA config>/custom_components/cam_wise`, separate-process restart,
  configure/entities/reload and removal.
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
default-list inclusion has not been requested. The prerelease's exact selected
version and component bytes were verified. Version-to-version update/rollback
remains NOT TESTED because only one release exists; do not infer upgrade support
from redownloading the same tag.

Report functional bugs through GitHub Issues without credentials or footage;
security reports use GitHub private reporting or support@cam-wise.com.
MIT applies to integration software/documentation; Cam-Wise branding has separate terms.
