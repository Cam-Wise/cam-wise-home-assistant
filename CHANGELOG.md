# Changelog

## Unreleased integration candidate — 2026-10-29 (blocked)

- Bring the paired local camera bridge, five existing-recording adapters, stable
  recording identity, and typed source capture/completion metadata into review.
- Keep bounded Ring Phoenix downloads and validated redirects. No live recording
  or snapshot substitute is added.
- Remove the newer-SDK-only FILE parser dependency; pin matching vendor SDKs in
  the two test environments. Keep the existing minimum/current HA matrix.
- Source identity remains 0.1.1b0; no regular version, tag or release is selected.
  Reolink DST ambiguity and coordinated Desktop/HA upgrade guarantees remain
  release gates. See [compatibility gates](docs/release-integration-gates-20261029.md).

The older prepared 0.1.0 notes below do not describe this candidate or authorize
publication. They must be replaced when the final coordinated source is frozen.

## 0.1.0 — prepared 2026-10-17, not released

- Set manifest, runtime diagnostics and protocol fixture to regular version 0.1.0;
  retain the existing API 1 functionality without new features.
- Validate signed Windows Desktop 0.1.23 beta with HA 2026.10.1: configuration,
  motion event, video retrieval, ONNX, Review, entity updates, reload, actual
  shutdown/restart/reconnect and removal through a loopback transport relay.
  Direct LAN/mDNS and other Desktop versions remain unproven.
- Retain v0.1.0-beta.1 as the historical technical test release, unchanged.
- Finalize [release notes](docs/release-notes-v0.1.0.md) and regular installation
  instructions. Publishing requires separate approval; stable discovery and
  two-version update/rollback remain post-publication checks.

## 0.1.0-beta.1 — 2026-10-16 (developer-preview prerelease)

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

Published as a prerelease at commit `21516f8bff9fc8742bc215a602971a2b674f724d`,
without binary assets. Exact tagged-version HACS 2.0.5 installation/lifecycle passed
in fresh HA 2026.10.1. Windows packaged E2E is NOT PROVEN; version-to-version
HACS update/rollback is NOT TESTED.
Desktop and integration updates have independent release processes.
