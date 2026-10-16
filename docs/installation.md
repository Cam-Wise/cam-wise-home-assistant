# Installation and lifecycle

## Manual installation

1. Obtain the standalone source package. No desktop source or private repository
   is required. Copy only `custom_components/cam_wise/` to
   `<HA config>/custom_components/cam_wise/` (avoid a nested `cam_wise/cam_wise`).
2. Restart Home Assistant. Open Settings > Devices & services > Add integration >
   Cam-Wise. Accept discovery or enter the desktop hostname/IP and API port.
3. Enable desktop LAN access explicitly if needed. Restrict its TCP listener with
   a firewall to the trusted HA host. `127.0.0.1` refers to HA's own host/container.
4. Configure entity mappings through Configure. Review recommendations; they are
   heuristics. Camera uses `camera.*`; motion and ding use `event.*` or
   `binary_sensor.*`; recording uses `sensor.*`, `event.*` or `camera.*`.
   Event roles must be distinct. Blank event mappings allow status-only use.

The default desktop port is 8000. Development/test desktop runs use their explicitly
configured isolated port, never an active installed desktop instance.
Host input is a hostname/IP, optionally prefixed `http://`; supply port separately.
HTTPS, credentials, paths and query strings are rejected. API 1 has no TLS support.
Zeroconf `_camwise._tcp.local.` needs multicast UDP 5353 on the same network;
manual configuration works across routed trusted networks with TCP access.

## HACS custom repository

1. In HACS, open Custom repositories and add
   `https://github.com/cam-wise/cam-wise-home-assistant` as type **Integration**.
2. Download Cam-Wise. Until the first tagged release, this installs the available
   branch source; do not mistake the manifest version for a published release.
3. Restart HA, then add and configure Cam-Wise as described above.

**PASS:** HACS 2.0.5 on HA 2026.10.1 downloaded the exact component files; separate
HA processes verified configuration, three entities, reload and removal. HACS was
controlled through its real websocket handlers, not visual frontend clicks.
This is custom-repository support, not official HACS default-list inclusion.
Windows packaged E2E remains **NOT PROVEN**; see [compatibility](compatibility.md).

## Reload, restart, update, reconfigure

Reload from the integration menu; options changes reload automatically. Pending
events/retries and recent-ID memory are discarded. The current recording ID at
setup is a baseline and is not replayed. Restart HA after replacing integration
files. For a new host/port, use Reconfigure; a different device ID is rejected.
Back up HA configuration before updates and retain the previous component folder
for rollback. HACS refresh and redownload of the same branch passed; a real
version-to-version upgrade and rollback are not yet tested. Follow the
[post-release update plan](publication-plan.md#hacs-update-test-after-the-first-release).

## Remove

Delete the integration entry first. Polling and listeners stop after successful
unload. Remove the component through HACS or delete only its installed component
folder and restart HA. Desktop review history and desktop credentials are unchanged.

## Verification checklist

In a disposable HA configuration, verify startup, manual setup, all three entities,
Configure, reconfigure, reload, process restart, offline/reconnect, diagnostics,
entry deletion and component removal. Use a synthetic API for contributor checks;
real desktop/media and HACS install/update checks must be recorded separately.

## Desktop processing prerequisite

The desktop must be normally coupled to its account and automatic processing must
be enabled. Configuration/status availability alone does not establish permission
to process recordings. A fresh unlinked source desktop was observed returning
`accepted: false`, `processing_status: paused`, `automatic_processing_disabled`.
Do not bypass account gates or expect rejected recordings to replay after coupling.
`accepted` is not `processed`; confirm processing separately in Desktop/Review.
Use only a trusted LAN: API 1 has no authentication or encryption. A manual
[Windows test plan](windows-test-plan.md) is available; it is not a completed test.
