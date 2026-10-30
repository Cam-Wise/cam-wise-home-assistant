# Cam-Wise distribution preparation — 2026-10-30

Scope is frozen to automatic existing recordings, one newest completed sample on
activation, subsequent new captures only, no reconnect backlog, 30s stability,
source capture times, contract 2, durable deduplication, camera-scoped processing
and explicitly authorized revocable LAN pairing. No live recording, snapshot
fallback or additional camera functionality is included.

Current source identity is development 0.1.1b0. Final regular release identity must
be aligned in manifest, runtime and fixtures before publication. Old prepared
v0.1.0 notes are historical and must not be used for this candidate.

Local complete source gates: 187 tests on each supported HA version; dependencies,
Ruff, Bandit, workflow lint and full Hassfest pass. Diagnostic output now includes
the non-secret negotiated recording contract. Hosted checks must match the final
public review commit. Private Desktop source, media, accounts and runtime data
must never be included in this public repository.

Follow [current compatibility](compatibility.md#current-recording-candidate--2026-10-30)
for vendor limits, update order and rollback restrictions. Installation uses the
existing HACS custom repository and a matching contract-2 Desktop candidate;
pair explicitly, authorize only the intended camera, and retain Free's one slot.
Do not disconnect an existing camera to enable another acceptance test.

Remaining distribution gates: exact final identities and hosted validators,
Windows packaged acceptance, real Reolink/Ring contract-2 processing, clean install,
beta update/data preservation and genuine recovery. Existing physical evidence
may support unchanged parts only. A regular HACS version selection cannot be
certified before that separately approved version is published.

No merge, tag, signing, release, HACS catalog request or production deployment is
authorized by this document.
