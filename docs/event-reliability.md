# Event reliability (API version 1)

The integration forwards local Home Assistant signals. The desktop owns media
retrieval, analysis and storage. An HTTP success response is not evidence that
a recording was downloaded or processed.

## Observable contract

Events use POST `/integrations/home-assistant/cam-wise/event` with unchanged
fields `trigger_type`, `trigger_entity_id`, `camera_entity_id`, `occurred_at`,
`event_id`, `context_id`, `media_identifier`. The integration does not request
synchronous processing (`wait`). `event_id` and `context_id` preserve HA's state
context; `occurred_at` preserves the trigger timestamp when awaiting media.

| Observation | Meaning | Automatic replay |
| --- | --- | --- |
| Valid HA state received | Signal entered local intake, possibly awaiting media | No HTTP request yet |
| Forward started | HTTP attempt initiated; delivery unconfirmed | Depends on outcome |
| `ok: true`, `result: accepted` | Desktop accepted background work; not completion | Never |
| `ok: true`, `result: duplicate` | Desktop recognized a claim; not completion | Never |
| `accepted: false`, `retryable: true` | Desktop explicitly declined acceptance and permits retry | Bounded |
| `accepted: false`, no retry permission | Rejected/paused/ignored | Never |
| Connection establishment failed | Request was not sent | Bounded |
| Timeout, lost response, HTTP error, malformed response | Delivery/acceptance unknown | Never |

The local diagnostics distinguish received signals, HTTP attempts, accepted
responses and uncertain deliveries. `processed` is always unknown (`null`).
The polled GET `/integrations/home-assistant/status` reports installation/API
metadata, availability, review-queue count, attention flag, route diagnostics and
mapping recommendations. It provides no durable, queryable processing receipt
for a submitted event/media pair. An attention flag or queue-count change does
not identify a particular accepted event. Local counters are diagnostic fields;
API version 1's desktop status-report receiver may ignore these additional fields.

## Concurrency, bursts and media correlation

Each config entry owns one event handler in `runtime_data`. An asyncio lock
serializes delivery and state changes across network awaits. The handler reserves
a media ID before the request, including while it is in flight. Received callbacks
have original expiry deadlines, so waiting for the lock cannot refresh their age.

Up to 64 triggers wait in FIFO order; each *new* recording consumes the oldest
unexpired trigger. Further triggers remain for further recordings instead of being
overwritten. Multiple signals for one recording are not all sent: one recording
has one local media claim. No clip is invented for unmatched triggers.

Triggers and safe retries expire after 120 seconds from the original occurrence
(not from a retry). A timer expires them even if no new state arrives. A callback
backlog is also limited to 64 tasks. Overflow and expiry have explicit diagnostic
counters; callback overflow logs a warning. Expiry cleanup waits for any active
bounded HTTP await to release the lock, but expired items cannot be sent afterward.

Without a recording timestamp tied to the signal, FIFO correlation is a bounded
arrival-order heuristic, not proof that a recording depicts a particular trigger.
Delayed/out-of-order clips inside the window can still be mismatched. Old triggers
outside the window cannot claim newly arriving media. An unchanged media attribute
on a new motion/ding state cannot identify new media.

## Deduplication and retries

The integration keeps the most recent 256 terminal media IDs per entry in memory:
accepted, duplicate, rejected, delivery-unknown, retry-exhausted or startup baseline.
It also prevents duplicate sends for media awaiting a safe retry. This catches
nonadjacent IDs and concurrent callbacks; it is not an unlimited durable ledger.

The desktop independently claims context/event IDs and a composite of camera,
trigger entity/type, media and occurrence time in a 90-second bucket. Current
claims expire after 360 seconds; recording-level deduplication is separately owned
by the desktop. Context IDs can be shared by HA actions, and bucket boundaries,
claim release after background failure, restarts and bounded caches mean these
identifiers do **not** guarantee end-to-end exactly-once processing.

Only a connection-establishment failure or explicit `accepted: false` with
`retryable: true` retains the unchanged payload. There are at most three attempts,
15 seconds between scheduled retries, within the original 120-second lifetime.
Coordinator recovery can retry earlier; offline status suspends scheduled delivery
until recovery or expiry. A lost response is conservatively retained as unknown:
this avoids blind duplicates but can lose an event that was never accepted.
Known accepted work is never retried based on an unrelated status change.

## Mapping and state validation

Camera requires `camera.*`; motion/ding require `event.*` or `binary_sensor.*`;
recording requires `sensor.*`, `event.*` or `camera.*`. Event roles must use distinct
entities, while the same camera may also supply recordings. Advanced options
require existing entities and report invalid mappings without changing saved
settings. Suggestions require a relevant role match, not merely a shared stem.

Invalid saved role/domain/conflict mappings disable intake without rewriting user
options. Missing entities can appear after setup; a missing camera suppresses
delivery until it exists. Removal, unknown/unavailable, malformed/stale/future event
timestamps, unchanged event timestamps and irrelevant attribute changes are ignored.
Binary sensors require an actual off-to-on edge (availability recovery is not a
physical event). Recording states require a new nonempty media identifier.

Configuration keys, config-entry identity, camera choice, entity unique IDs, names,
unrelated options, HTTP paths and API version remain unchanged. Existing ambiguous
or invalid mappings are preserved but require correction before forwarding.

## Reconnect, restart and unload

Coordinator success/failure drives connection diagnostics and safe retry recovery.
Listeners are installed after successful platform setup. Successful unload removes
state/coordinator listeners, cancels and awaits active/queued tasks, cancels the
timer and clears pending/retry state. A failed platform unload leaves intake active.
Cancellation during a request leaves delivery unknown; it cannot retract accepted
desktop work. Setup/platform errors cannot leave event listeners behind.

Pending triggers, retries and the recent-ID ledger do not survive HA restart/reload.
The recording ID visible at setup is a baseline, not a replay request. Older media
or events received while HA was stopped are not reconstructed. Desktop background
work is not durably acknowledged here and may be interrupted by desktop restart.

## Separate desktop API dependency (not implemented)

Reliable processing confirmation and recovery after ambiguous delivery require a
separate versioned API contract: a client-supplied idempotency key with documented
scope/retention, a durable intake receipt, and a receipt lookup returning correlated
accepted/processing/completed/failed states with explicit safe retry rules. Restart
behavior and expiry must be defined. A generic error flag or `duplicate` response
is insufficient. Recording correlation would also require authoritative recording
timestamps or a trigger-to-recording identity.

Processing acknowledgement/recovery is blocked on that separately authorized
desktop work. The HA integration does not add endpoints, change private code,
poll private diagnostics, use synchronous heavy processing or claim completion.
This dependency does not prevent the HA-side concurrency/lifecycle improvements.
