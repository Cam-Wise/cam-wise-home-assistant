# Cam-Wise v0.1.0 — release notes draft

PREPARATION ONLY. Do not publish this draft or create a release yet. Finalize the
exact green source commit, release date and Windows result before approval.

Cam-Wise connects Home Assistant camera events to local Cam-Wise Desktop
processing and review. It provides status, review-queue count and attention
entities, manual/discovered configuration, event mapping, reload and diagnostics.
The integration software is MIT licensed; Desktop and brand rights remain separate.

The planned regular release retains the existing API 1 functionality. The previous
v0.1.0-beta.1 remains available as a historical technical test release.

Validated baseline: HA 2025.2.0/Python 3.13 and HA 2026.10.1/Python 3.14, 89 tests
per version; HACS/Hassfest/lint/dependencies pass. Exact beta HACS installation,
restart/configuration/entities/reload/removal and Linux source media/inference/Review
passed. Final v0.1.0 source checks must be linked here after the version PR passes.

Windows signed packaged E2E: PENDING — release blocker. Replace with exact tested
build/hash and bounded result, linking sanitized compatibility evidence.
Stable HACS discovery/install and beta-to-stable update/rollback: PENDING until
the approved regular release exists; record results before official submission.

Use only a trusted restricted LAN; API 1 has no authentication or encryption.
`accepted` confirms background intake, not processing. Queues/retries/dedup memory
are volatile; media association is heuristic. Confirm actual results in Desktop
Review. Desktop needs a legitimate coupled account and automatic processing.
No camera stream, model or Desktop installer is included in this release.

Follow [installation](installation.md), [compatibility](compatibility.md) and
[event reliability](event-reliability.md). Desktop and integration versions are
independent. Official HACS catalog inclusion is a later, separately approved step.
