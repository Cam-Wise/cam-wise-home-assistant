# Cam-Wise for Home Assistant

Connect configured Home Assistant camera events to the local Cam-Wise desktop
review workflow. Inference, media retrieval and storage remain in Cam-Wise.
This custom integration provides a status sensor, review-queue count sensor and
attention-required binary sensor. It does not provide camera streams or AI models.

**Pre-publication candidate:** repository identity is
[`cam-wise/cam-wise-home-assistant`](https://github.com/cam-wise/cam-wise-home-assistant),
codeowner `@Bob-Cam-Wise`, first candidate `v0.1.0-beta.1`. These are prepared
metadata; the repository has not been created or approved for publication.
HACS installation is unavailable until a public GitHub repository is separately approved. No official HA quality tier is claimed.

## Requirements

- Home Assistant 2025.2.0 or newer; tested boundaries are 2025.2.0 and 2026.10.1.
- Cam-Wise local API version `1`, with LAN access explicitly enabled when HA runs
  on another host. A desktop installation is needed for use, never for development.
- A trusted isolated LAN. HTTP is unencrypted and unauthenticated: do not expose
  the desktop API to the internet, guest networks or untrusted clients.
- For processing: a normally coupled Cam-Wise desktop account and enabled automatic
  processing are required. An unlinked desktop can expose status while declining
  events as paused; this is not a completed media-processing test.
- For events: existing camera and motion/doorbell/recording entities in HA, and
  the corresponding desktop HA/media configuration. The integration stores no token;
  the desktop may need its own HA credential to retrieve media.

## Install and configure

See [installation](docs/installation.md) for manual installation, future HACS
installation, configuration, reload, update and removal. See
[troubleshooting](docs/troubleshooting.md) for connectivity and event failures.

## Delivery limitations

`accepted` means background intake, **not processed**. Pending events and retries
are lost on HA restart/reload. FIFO media association can be heuristic. Unknown
HTTP outcomes are not replayed. Deduplication and retries are bounded, not durable
exactly-once delivery. Read the [API contract](docs/api-contract.md) and
[event reliability](docs/event-reliability.md) before using events in automations.

## Development and maintenance

[CONTRIBUTING](CONTRIBUTING.md) covers independent tests and required CI gates.
[Compatibility](docs/compatibility.md) distinguishes synthetic API tests from real
desktop evidence. [SECURITY](SECURITY.md) explains disclosure and network trust.
[License provenance](docs/licensing.md) records the MIT scope and separate brand terms.

Support: GitHub Issues in the future approved repository. Security: privately
report to support@cam-wise.com. Do not post
tokens, media identifiers, network addresses or unreviewed logs in public issues.

See [publication and post-publication gates](docs/publication-plan.md).
