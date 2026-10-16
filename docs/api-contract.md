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
