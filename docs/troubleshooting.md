# Troubleshooting

| Symptom | Check |
| --- | --- |
| Cannot connect | Desktop running, LAN opt-in, correct hostname/port, firewall permitting only HA; loopback inside a container is not the desktop |
| No discovery | Multicast boundary; use manual setup |
| Unsupported API | Discovery and status must report API `1`; don't bypass validation |
| Unavailable entities | 30-second poll failed or response types are invalid; polling recovers automatically |
| Paused / automatic_processing_disabled | Check normal desktop account coupling, automatic processing and schedule; do not bypass gates |
| No forwarded events | Existing valid mappings, actual off-to-on binary edge/new event timestamp/new media ID, desktop route enabled and desktop media credentials configured |
| Accepted but no review | Acceptance is not completion; inspect desktop locally, do not automatically replay unknown/accepted work |
| Wrong clip associated | FIFO is heuristic; no authoritative trigger-to-recording correlation exists in API 1 |
| Events lost after restart | Pending waits/retries are intentionally volatile; no replay ledger |
| Invalid host | Port is separate; no HTTPS, credentials, paths or queries |

Pause competing legacy routes before an isolated event test to avoid duplicate
ingestion, preserving desktop profiles and credentials. Never silently toggle them.
Diagnostics redact host and configured entity IDs and omit raw payloads/media IDs.
Review diagnostics and logs manually before sharing: server strings are not proof of safe content. Desktop route-status POSTs
contain entity/media identifiers on the LAN. Debug logs may expose operational
metadata. Never attach credentials or real camera footage to an issue.
