# SESSION HANDOFF

Date: 2026-10-29
Task: Coordinated one-completed-recording HA/Desktop intake repair.
Branch: codex/ha-intake-contract-20261029
Base/rollback: f9f22c52ce1e0cc5a87f844ae1f9a98c6cef4a09
Worktree: .worktrees/ha-intake-contract-20261029 in Desktop root (separate HA repository).
Companion Desktop branch: codex/ha-intake-stabilization-boundary-20261029.

Changes: Add captured_at/ended_at/completed to existing opaque metadata, retaining
all stable identity and authorization behavior. Typed UTC vendor times only;
missing/ambiguous metadata is explicit, never derived from first-seen/title/state
update times. Ring requires matching vendor event ID and ready recording status.
Tapo requires explicit device offset; Reolink requires device timezone; Blink
requires aware clip time. Complete-media and 30s observation gates remain Desktop-owned.
No version bump, install, build, service restart, push, deployment or publication.

Tests: 54 targeted HA source tests PASS (recording_timing_contract, recordings,
ring_recording_download), /venv-current on existing CamWise-HATest-Round1 WSL.
All fixtures synthetic, socket-disabled. User config/camera events untouched.
Original HA branch/worktree remains clean at f9f22c5. This repair worktree is clean
after its checkpoint commit. Exact final HEAD: git rev-parse HEAD.
Docs: recorded-video-input.md and this handoff. No shared Desktop root WIP staged.

Open P0/P1: none in the tested source repair scope. Hardware acceptance remains
unproven for all five vendors, timezone/SDK variants, brief unobserved sub-poll
outages and real power-loss/storage failure. See recorded-video-input.md.
Next safe action: integrate BOTH companion source checkpoints, then separately
authorize packaged/hardware validation; no publication is authorized here.
Do not touch: existing HA runtime/config, Desktop installed8000, user datasets,
models/Review, other worktrees, previous artifacts, paid-launch or cloud production.

Final adapter-through-list check: Reolink structured times reach returned metadata;
existing channel-authorization test asserts UTC capture and completed flag. Final
54-test scoped rerun PASS in 2.74s after this wiring correction.
