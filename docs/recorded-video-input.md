# Existing video recordings â€” local candidate

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

Explicit activation admits at most **one newest completed recording** from the
bounded initial listing, after the common **30-second** stable-revision observation
and complete-media validation. Subsequent automatic intake accepts only recordings
captured after the active connected window began. An ordinary restart, detected
connection failure, processing pause or polling gap closes that window; reconnect
never creates another initial sample or replays its offline history. Explicit off/on
creates a new one-item sample. Prior-day reads serve the explicit sample or an already
identified pending recording only.

The matching Desktop candidate requires typed `captured_at` (UTC epoch seconds),
`ended_at` (UTC seconds or null) and `completed` (boolean) in each metadata row.
Ready clip endpoints may have no end time; stable observations and MP4 validation
remain mandatory. Reolink uses its device timezone and structured FILE start/end,
UniFi uses event milliseconds, Tapo requires its explicit device offset, Blink uses
a timezone-aware clip time, and Ring requires an exact matching last-event ID,
created_at and ready recording status. Missing, naive, malformed or future capture
times are never guessed. Invalid or ambiguous individual Reolink recordings are
skipped with a visible message; unavailable source metadata or an untrustworthy
device clock pauses only that source. No title, last_updated or
first-seen timestamp is substituted. Older HA versions may therefore pause until
both sides of this unreleased contract are integrated. HA state timestamps are not
proof of when footage was captured.

Both peers must explicitly support recording contract **2**. Desktop advertises it
in discovery/authenticated status and sends it on each recording request. The HA
bridge checks both the authenticated Desktop status and request contract, and
returns its own contract in metadata. Older Desktop receives an HA Repair/update
notice; newer Desktop refuses to enable intake with an older bridge. Existing
pairings, cameras and user data remain intact. There is no older-policy fallback.

Reolink uses explicit device UTC/DST rules, with calendar-correct transitions and
zero/one/two possible UTC instants for a local time. Repeated autumn times and
nonexistent spring times are skipped individually. A fresh read-only GetTime
checks the clock; missing settings, unsupported rule shapes, excessive clock skew
or an over-five-second clock read pause this source. New-capture boundaries include
a conservative ten-second clock uncertainty margin, separate from the unchanged
30-second stability gate. A changed time-rule fingerprint closes the connected
window without importing its backlog. Discovery/download times never become capture
times. Correct historical camera settings remain a source prerequisite; arbitrary
manual rewriting of old device timestamps cannot be reconstructed.

General HA minimum remains 2025.2.0. That Core's five-part Reolink FILE identifiers
lack source start/end and explicitly disable automatic recordings for that source.
HA 2026.10.1 seven-part identifiers are supported when its device-time metadata
passes validation. Other brands are not blocked by an unsupported Reolink source.

Logical recording identity, durable receipt preparation and queue admission receipts
prevent duplicate jobs across process crashes, changed bytes and pruned terminal
queue history. Obsolete/untagged HA tasks are cancelled before claim and checked
again before analysis. Disabling or reactivating preserves stored footage, Review,
datasets and models; only obsolete execution is blocked. An analysis already holding
the lifecycle lock finishes before an off/on transition takes effect. One active
delivery route per physical camera and existing Free camera limits remain unchanged.

This is bounded polling, not a lossless archive service. Sub-poll outages with no
observable failure cannot be distinguished from uninterrupted connectivity; actual
provider clocks, SDK metadata and all-brand hardware behavior still need acceptance.
No reconnection-time or vendor-clock precision guarantee is inferred from mocks.

Validation: synthetic source/authorization/queue tests only until the owner tests
real recordings on the local candidate. Multiple-camera hardware acceptance,
Tapo custom-version compatibility, codec support and cloud availability remain
explicit acceptance checks.
