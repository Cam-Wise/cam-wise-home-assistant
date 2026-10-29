# Local API version 1

This documents the interface consumed by this integration, not a new desktop API.
JSON objects over unauthenticated HTTP; 10-second total timeout per request.
HA supplies its shared aiohttp session. No runtime private Python dependency.
Synthetic examples live in `tests/fixtures/` and never contain real media or tokens.

| Method and path | Consumer contract | Example |
| --- | --- | --- |
| GET `/health` | `status` must equal `ok`; other desktop fields are ignored | health.json |
| GET `/integrations/home-assistant/discovery-info` | `product: Cam-Wise`, nonempty string `device_id`, `api_version: 1`; version/environment metadata optional | discovery.json |
| GET `/integrations/home-assistant/status` | API 1; nonempty string status, nonnegative integer review_queue (not boolean), boolean attention_required; optional string version/environment and string/null-valued recommended_route_options | status.json |
| POST `/integrations/home-assistant/cam-wise/event` | trigger_type, trigger_entity_id, camera_entity_id, occurred_at, event_id, context_id, media_identifier; asynchronous intake | event.json, accepted.json, duplicate.json, retryable.json |
| POST `/integrations/home-assistant/cam-wise/status` | Entry-owned diagnostics: mapping, listener state, timestamps, media/error metadata and counters; desktop may ignore additional counters | integration-status.json, integration-status-response.json |

API version is compared as a string: only `1` is accepted. Discovery identifies a
device, not an authenticated principal. Status is polled every 30 seconds. Invalid
JSON/object/schema or HTTP errors cause unavailable state; unknown POST outcomes
are not safe replay permission. Desktop responses can have extra fields.

## Entities and configuration

One device per installation ID; unique IDs append `_status`, `_review_queue` and
`_attention_required`. Actual HA entity IDs may differ due to registry naming.
Status is a diagnostic sensor with version/environment/API attributes; review
queue is a measurement in items; attention-required is a problem binary sensor.
Entities become unavailable after a failed coordinator update.
Config-entry data has `host` and `port` (1..65535); options have
`camera_entity_id`, `motion_entity_id`, `ding_entity_id`, `recording_entity_id`.
No HA service actions, camera platform, subscription or cloud calls are added.

## Event semantics and result handling

Trigger types: `motion`, `ding`, `recording_ready`. Entity IDs are HA routing IDs;
occurred_at is timezone-aware ISO 8601; event_id/context_id preserve HA context.
Recording media comes from changed `last_video_id`, `media_id` or `video_id`
attributes. The client does not send `wait` or `is_test` (desktop defaults false).
No video bytes or credentials are sent by the integration.

`ok: true` and result `accepted` mean background acceptance; `duplicate` means a
desktop claim. Neither proves download, inference, review creation or processing.
`processed` remains null in diagnostics. At most three attempts are made only for
connection-establishment failure or `accepted: false, retryable: true`; scheduled
retries are 15 seconds apart within the original 120-second lifetime, with earlier
retry allowed upon coordinator recovery. Timeout/lost response/HTTP error is unknown
and is never blindly retried. Accepted work is never retried on a queue change.

FIFO waits/backlog/retry queues are bounded at 64 and recent terminal media IDs at
256 per entry. Pending events, retries and dedup memory are not durable over HA
restart/reload. FIFO media association is heuristic. These are bounded best-effort
guarantees, not at-least-once or exactly-once processing. Desktop claim behavior
is version-dependent; see [event reliability](event-reliability.md) for details.

## Network and compatibility

HA needs outbound TCP to the desktop API. Discovery optionally needs multicast
UDP 5353. Desktop-to-HA media retrieval uses desktop-owned configuration and
credentials and must be separately reachable. API 1 has neither authentication
nor TLS; the host/ID/status response can be spoofed on an untrusted network.
See [compatibility](compatibility.md) for measured version evidence.

HTTP redirects are not followed. Non-2xx outcomes are unknown for event delivery,
never safe-not-sent evidence. Unexpected result labels are normalized before diagnostics.


## Local pairing test candidate (0.1.1b0)

This additive API 1 capability requires the matching local Desktop pairing test
candidate, not an existing signed Desktop release. No public release/tag exists
for this candidate. Existing API 1 entries remain compatible and keep their IDs.

The separate HA-only HTTP endpoint advertises `pairing_required: true` in discovery.
After Desktop explicitly enables access on the trusted home network, HA generates
an independent random 256-bit credential. POST `/integrations/home-assistant/pair`
submits only its SHA-256 `verifier` during a two-minute window. The returned
`request_id` and six-hex-digit `code` are not access credentials. The user compares
the code in HA and Desktop and approves locally, then submits the HA form.
HA sends `Authorization: Bearer <credential>` only as a header. Desktop stores a
verifier in its DPAPI-protected per-user pairing store. HA stores its credential
in normal config-entry storage; protect HA configuration backups accordingly.

The gateway exposes public health/discovery and the bounded pairing request only.
Status GET and the two existing event/status POST paths require authorization.
No UI, camera-management, account, file, shutdown, or arbitrary proxy access exists.
Redirects are not followed, queries and browser Origins are rejected. Tokens must
never appear in URLs, diagnostics or log messages. Local Desktop can revoke each
peer or disable the gateway. A 401 requests reauthentication; existing mappings and
entity IDs survive reapproval. Failed/unknown event outcomes retain existing replay
limitations. Pairing does not change account or automatic-processing requirements.

Discovery of a changed address for a paired entry must pass an authenticated status
check before HA updates its address. An unpaired legacy entry is not automatically
moved to the paired listener; migration uses explicit Reconfigure and approval.
Windows consent is bound to the recorded network identity; a network change closes
access until new explicit consent. Discovery and reconnection are best effort.

**HTTP remains unencrypted.** This approval/token mechanism excludes unapproved
clients but cannot protect against interception, token theft, active spoofing or
replay by a hostile local peer. The comparison code is a user aid, not an encrypted
or authenticated channel. Use only a trusted home network; no internet/guest use.


The approved test connection also supplies a read-only HA camera bridge at
`/api/cam_wise_bridge/api/`. It accepts this pairing credential in the Authorization
header, not a Home Assistant user token. It exposes API health, camera identities,
the selected camera/event states and that camera's snapshot. It exposes no HA
services, templates, unrelated sensor states or arbitrary URL proxy. Unselected
camera metadata omits access tokens and media URLs. Unloading/removing the entry
or revoking Desktop access disables the bridge credential's use by Desktop.

An authenticated integration-status report may include `bridge_port` and a bounded
`camera_catalog` (entity/name, suggested motion/ding and recording capability).
Desktop derives the HA host from the actual approved client's transport address,
not an arbitrary supplied URL. The outbound credential is protected by Desktop's
existing per-user DPAPI store. Existing explicit Desktop HA credentials win; the
bridge is a fallback for a fresh installation, never an automatic replacement.
With multiple HA bridges, no implicit source is selected. Camera selection and
profile creation still enforce Desktop account/Free/Plus rules. A blank paired
entry can adopt the explicitly selected Desktop mapping on a later status poll;
nonempty mappings are never overwritten.

Recording media remains subject to the existing camera integration's actual media
attributes and availability. Snapshots are not advertised as video support.
# Recorded-video compatibility capability (local candidate)

API 1 is retained for general status/events. Automatic recorded-video intake
additionally requires the exact integer `recording_contract: 2` from Desktop
discovery/authenticated status and from HA recording-list responses. Each listing
and file request must carry `X-Cam-Wise-Recording-Contract: 2`; the bridge also
rechecks authenticated Desktop status. A missing, boolean, string or different
contract is incompatible, regardless of the displayed development version.

Incompatible Desktop receives HTTP 409 `desktop_recording_update_required` with
safe EN/NL update text and a localized HA Repair. Missing bridge support gives
Desktop `ha_recording_update_required` before activation, or pauses an already
enabled camera without deleting its setting. There is no older-policy fallback.
Normal pairing/event functionality is not globally disabled by this feature gate.

Reolink source limitations return `reolink_time_metadata_unavailable` or
`recording_clock_unreliable` as availability, with no recordings. Per-record
`timing_error` values `recording_time_ambiguous`, `recording_time_nonexistent` and
`recording_time_invalid` exclude only that logical recording. Valid Reolink rows
carry `capture_margin: 10` seconds; connected-window admission uses the capture
lower bound, independently of the existing 30-second revision stability gate.
The safe time-rule `time_basis` fingerprint closes the window on configuration
changes. No vendor credentials or resolved media URLs are included.
