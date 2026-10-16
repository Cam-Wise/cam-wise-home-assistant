# Changelog

## 0.1.0-beta.1 — prepared, not released

- Prepare the first independent public integration beta for
  `cam-wise/cam-wise-home-assistant`, maintained by `@Bob-Cam-Wise`.
  Record MIT scope and separate brand permissions; publication approval is pending.
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
- Set proposed security contact and post-publication/official-HACS approval gates.
- Keep manifest, runtime diagnostics and protocol fixture versions consistent.

No public version, tag or release has been published by this preparation.
Desktop and integration updates have independent release processes.
