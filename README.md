# Cam-Wise

Cam-Wise processes camera and doorbell media locally on your Windows PC and helps
you review the results. Your images, recordings and AI processing stay in Cam-Wise.

## What the Home Assistant integration does

The integration forwards configured camera events from Home Assistant to Cam-Wise
Desktop and shows processing status in Home Assistant. Desktop retrieves the media
and handles local processing and Review. This integration does not add camera
streams, supply AI models or replace your camera manufacturer's HA integration.

The existing Desktop Home Assistant route can also work without HACS. If that
route already works, keep it until you deliberately choose to switch event delivery.
Installing HACS alone does not replace it or prevent duplicate triggers.

## Requirements

- Home Assistant 2025.2.0 or newer. The tested versions are 2025.2.0 and 2026.10.1.
- Cam-Wise Desktop with local API version 1, a normally linked account and automatic
  processing enabled for media processing.
- A camera already available in Home Assistant, with suitable event and media entities.
- A trusted, isolated local network when Home Assistant runs on another device.

**Network security:** API 1 uses HTTP without authentication or encryption. Desktop
LAN access is off by default and requires explicit consent. Do not expose it to the
internet, public or guest networks. Restrict inbound access to the trusted HA host.
The local test candidate adds explicit Desktop approval and revocable tokens;
HTTP remains unencrypted. See [the pairing test contract](docs/api-contract.md#local-pairing-test-candidate-011b0).

## Install with HACS

1. Open **HACS > Custom repositories**.
2. Add `https://github.com/Cam-Wise/cam-wise-home-assistant` as **Integration**.
3. Download Cam-Wise and restart Home Assistant.
4. Open **Settings > Devices & services > Add integration > Cam-Wise**.

Currently, the available tagged release is **v0.1.0-beta.1**; enable prerelease
visibility in HACS to select it. This is a custom repository, not an integration
in the default HACS catalogue. See [installation](docs/installation.md) for details.

## Connect to Cam-Wise Desktop

Start Desktop under your normal Windows account and complete its normal account
setup. Desktop selects that account's local storage automatically; you do not need
to choose a Windows profile or move datasets.

For Home Assistant on another device, Desktop must first allow LAN access explicitly.
The current controls are under the Desktop Home Assistant network settings, in the
advanced LAN/firewall section. Restart Desktop after changing its LAN binding.
Enabling LAN alone does not configure or verify the Windows firewall.

When discovery is available, confirm the intended Cam-Wise installation in Home
Assistant. Check its displayed environment: a **worktest** entry is a separate test
installation. If discovery fails, use the Desktop hostname/IP and API port as the
manual fallback. The installed Desktop normally uses port 8000. Do not use a test
instance's address for your normal installation.

Direct LAN discovery has not yet been verified end to end with the signed Windows
app. Existing signed Windows processing evidence used a loopback transport relay;
see [compatibility](docs/compatibility.md) for the exact tested scope.

## Set up a camera or doorbell

1. Use the Desktop camera wizard to select the existing HA camera and media source.
   Desktop keeps the HA credentials needed to retrieve media; HACS does not copy them.
2. In the Cam-Wise integration, open **Configure** and review the suggested entities,
   or choose them manually. Recommendations are suggestions, not device verification.
3. Use one event-delivery route for the camera. Before enabling HACS events, explicitly
   pause the competing legacy route or automation. Keep the existing camera profile.
   Current Desktop route switches apply globally, so check other cameras before pausing.
4. Trigger one test event and check the result in Desktop Review.

A recording-capable configuration downloads a video when suitable media is available.
A snapshot configuration retrieves a still image through HA. The camera's actual
capabilities and Desktop profile determine the route; HACS does not turn snapshots
into video recordings. A received event does not guarantee a completed Review item.

## Status entities

| Entity | Purpose |
| --- | --- |
| Status | Current Cam-Wise processing status |
| Review queue | Number of items waiting for review |
| Attention required | Whether Cam-Wise reports that attention is needed |

## Limitations and troubleshooting

- **Old or offline installation:** HA keeps its saved entry and retries. Start the
  intended Desktop instance. For a changed address, use the integration menu's
  **Reconfigure** action; it rejects a different installation ID. Do not point a
  WorkTest entry at a different normal installation.
- **Remove a test link:** deliberately delete that HA integration entry. This does
  not delete Desktop datasets, camera profiles or Review history.
- **No discovery:** multicast may be blocked. Use manual setup on the trusted network.
  Discovery can update an existing installation's address after validating its ID;
  it is not authenticated identity proof under API 1.
- **No Review result:** check Desktop account linking, automatic processing, camera
  configuration and media availability. `accepted` means intake, not completion.
- **Restarts and duplicates:** pending event waits/retries are lost on HA restart or
  reload. Deduplication is bounded; delivery is not durable exactly once. Matching an
  event to a later recording can be heuristic.

See [troubleshooting](docs/troubleshooting.md), [compatibility](docs/compatibility.md)
and [event reliability](docs/event-reliability.md) for detailed evidence and limits.

## Support, contributions and licence

Report issues through [GitHub Issues](https://github.com/Cam-Wise/cam-wise-home-assistant/issues).
Do not include credentials, camera media or unreviewed logs. For security reports,
use GitHub private vulnerability reporting or support@cam-wise.com; see
[Security](SECURITY.md).

Contributions are welcome through pull requests; see [Contributing](CONTRIBUTING.md).
The integration source is MIT licensed. Desktop and brand terms are separate;
see [licensing](docs/licensing.md) and [LICENSE](LICENSE).


### Trying the local pairing candidate

The `0.1.1b0` source candidate is for manual installation in a separate disposable
HA 2026.10.1 instance with the matching local Desktop test build. It is not a
published HACS release. Do not replace a working HA installation for this test.
In Desktop's Home Assistant settings, review the trusted-network warning and
choose Connect. Add Cam-Wise in HA, confirm discovery (or use the displayed manual
address), compare the code and approve in Desktop, then submit the HA form.
Select the camera from Available HA cameras in Desktop. This uses the existing
camera-profile creation rules and explicitly selects HACS as its event route.
An otherwise blank HA mapping adopts that choice on the next poll; existing
nonempty mappings remain unchanged. The existing wizard remains available.
A Desktop release predating this candidate does not contain these controls.

### Existing recorded video input (local candidate)

See [recorded video input](docs/recorded-video-input.md) for the five source
adapters, explicit per-camera authorization and enablement, separate camera
ownership, and current validation limits. This is not a published HACS release.
