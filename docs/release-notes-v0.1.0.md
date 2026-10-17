# Cam-Wise v0.1.0

Cam-Wise connects Home Assistant camera events to local Cam-Wise Desktop
processing and review. It provides status, review-queue count and attention
entities, manual/discovered configuration, event mapping, reload and diagnostics.
The integration software is MIT licensed; Desktop and brand rights remain separate.

This regular version retains the existing API 1 functionality without new features.
The previous
v0.1.0-beta.1 remains available as a historical technical test release.

Validated HA boundaries: 2025.2.0/Python 3.13 and 2026.10.1/Python 3.14, with
89 standalone tests per version. Exact historical-tag HACS installation,
restart/configuration/entities/reload/removal and Linux source media/inference/Review
passed. The integration retains mandatory HA matrix, HACS and Hassfest checks.

Signed Cam-Wise Desktop **0.1.23 beta** passed Windows functional E2E with HA
2026.10.1: configuration, motion event, video download, ONNX inference, Review/image,
status updates, reload, actual shutdown/restart/reconnect and removal. The test
used a loopback transport relay to the real signed app, synthetic media/model and
normal account coupling. **Direct LAN/mDNS and other Desktop versions are not
proven.** This is no blanket packaged version-range or model-accuracy claim.

Select v0.1.0 in HACS as a regular release without beta visibility once published,
then restart HA. Exact stable selection/install and release-to-release update/
rollback are post-publication checks, not completed evidence. Back up HA before
upgrading. The existing beta remains unchanged for historical testing/rollback.

Use only a trusted restricted LAN; API 1 has no authentication or encryption.
`accepted` confirms background intake, not processing. Queues/retries/dedup memory
are volatile; media association is heuristic. Confirm actual results in Desktop
Review. Desktop needs a legitimate coupled account and automatic processing.
No camera stream, model or Desktop installer is included in this release.

Follow [installation](https://github.com/Cam-Wise/cam-wise-home-assistant/blob/main/docs/installation.md),
[compatibility](https://github.com/Cam-Wise/cam-wise-home-assistant/blob/main/docs/compatibility.md) and
[event reliability](https://github.com/Cam-Wise/cam-wise-home-assistant/blob/main/docs/event-reliability.md). Desktop and integration versions are
independent. Official HACS catalog inclusion is a later, separately approved step.
