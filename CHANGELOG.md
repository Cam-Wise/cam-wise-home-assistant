# Changelog

## 0.1.0-beta.1 — prepared, not released

- Prepare the first independent public integration beta for
  `cam-wise/cam-wise-home-assistant`, maintained by `@Bob-Cam-Wise`.
  MIT covers integration software/documentation; branding has separate terms.
- Support manual/Zeroconf configuration, entity mapping, reload and diagnostics.
- Provide status/review-queue sensors and attention-required binary sensor.
- Serialize event intake with bounded volatile FIFO/retries and media deduplication;
  never represent accepted background work as confirmed processing.
- Reject HTTP redirects/non-2xx results without unsafe safe-retry classification.
- Normalize untrusted server result labels before exported diagnostics.
- Reject ambiguous hosts/HTTPS downgrade and malformed status responses; use
  IPv6-safe device links and omit unknown saved options from diagnostics.
- Include independent real-HA tests, synthetic protocol fixtures, API/security/
  installation documentation and mandatory CI gates.
- Validate HACS custom installation with HACS 2.0.5 on HA 2026.10.1: actual download,
  process restart, configuration, entities, reload and removal.
- Pass 89 standalone tests on each HA version: 2025.2.0 and 2026.10.1; hosted
  HACS Action, Hassfest, Ruff, dependency and syntax checks pass.
- Verify Linux Desktop 0.1.23 source-runtime E2E through media retrieval, ONNX and
  Review API/image. Windows packaged E2E remains NOT PROVEN.
- Document trusted-LAN-only use, acceptance versus processing, confidential
  reporting, manual Windows checks and post-release update validation.
- Keep manifest, runtime diagnostics and protocol fixture versions consistent.

Public source and HACS custom installation are available; no tag or GitHub release
has been published. Version-to-version HACS upgrade is not yet tested.
Desktop and integration updates have independent release processes.
