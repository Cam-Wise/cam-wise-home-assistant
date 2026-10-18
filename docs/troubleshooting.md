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

## An old WorkTest entry keeps retrying

A saved entry belongs to one Desktop installation ID, not whichever Cam-Wise is
currently running at its address. An offline test installation does not imply lost
Desktop data. HA retains the entry and retries; its three entities may be unavailable.

- To use that same installation again, start it and check its network settings.
- If only its host or port changed, use **Reconfigure** in the integration menu.
  A different installation ID is rejected. Discovery may update the address of a
  matching ID, but API 1 does not cryptographically authenticate that ID.
- To use your normal Desktop instead, add it separately and deliberately confirm
  its environment. Remove the old test entry only when you choose to do so.
- Deleting an HA entry stops that entry's listeners and polling; it does not delete
  Desktop datasets, Review history, account credentials or camera profiles.

Never enable an old test runtime or broaden firewall access just to make a stale
entry stop retrying. Check which installation you actually intend to use first.
