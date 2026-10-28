# Existing video recordings — local candidate

This feature requires the matching unreleased Desktop recording candidate. It is
not a published compatibility promise or a hardware-test result for all brands.

1. Pair normally. Keep vendor accounts/credentials in their existing HA integration.
2. In Cam-Wise's HA integration options, choose **Choose other entities**. Under
   **Cameras for recorded videos**, explicitly select the cameras Cam-Wise may read.
   The original single-camera/event mapping remains available and is also authorized.
3. In Desktop, select each camera and enable **Receive videos automatically** for it.
   Downloading remains off by default. Existing completed videos are downloaded;
   no live stream, new recording, snapshot fallback or archive backfill is started.
4. A completed file is validated and submitted to Cam-Wise's existing recording
   delivery/storage/analysis queue. Processing uses that camera's active model,
   or onboarding when it has none. Dataset/model/review ownership remains per camera.
   The common scheduler shares CPU time fairly; it does not combine datasets.

Source adapters: Reolink replay/MP4, UniFi Protect full access event clips, Tapo
Cameras Control custom integration recordings, Ring latest ready video, and Blink
existing cached clip identities. Tapo's standard TP-Link integration is not the
Tapo Cameras Control custom integration. Tapo may first prepare a file in HA's
cache; Desktop retries once it is complete. Ring needs its recording entitlement.
SDK/custom-integration changes can require adapter updates. No vendor credentials
or resolved recording URLs are sent to the Desktop UI.

Retries and duplicate checks are per camera and recording. Initial opt-in begins
with the latest available recording. Later polls read recent available items
(including the previous day for replay sources), not an unlimited historical
archive. Latest-only providers cannot recover clips that HA never exposed before
the next clip replaced them. Long offline periods or more clips than the bounded
recent listing are not a lossless archive-replication guarantee.

Pause/account/route/network-revocation gates still apply. Disabling intake stops
new delivery but preserves queued work and downloaded media under normal Cam-Wise
retention. No user data is reset. One active delivery route per physical camera
remains required. Free camera limits are unchanged.

Validation: synthetic source/authorization/queue tests only until the owner tests
real recordings on the local candidate. Multiple-camera hardware acceptance,
Tapo custom-version compatibility, codec support and cloud availability remain
explicit acceptance checks.
