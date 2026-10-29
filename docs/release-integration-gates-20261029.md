# Recording compatibility gates — 2026-10-29

The three source compatibility blockers are repaired locally. Ready for final
validation under the support boundary below; no publication is implied. This
revision has not been pushed or run through hosted CI. Earlier green CI belongs
to the preceding checkpoint, not these changes. Runtime version remains 0.1.1b0;
actual recording compatibility is negotiated by capability contract 2, not a
version string shared by several development candidates. API 1 remains unchanged.

## Support matrix

| HA Core / bridge / Desktop | Automatic recording result |
|---|---|
| HA 2025.2.0, new bridge, contract-2 Desktop | General integration retained; real five-part Reolink FILE source blocked with Core update action |
| HA 2026.10.1, new bridge, contract-2 Desktop | Reolink seven-part source supported if clock/settings/rules validate |
| Either tested Core, new bridge, contract-2 Desktop | Ring remains latest ready event/video with exact source ID/time; other providers retain their existing prerequisites |
| New bridge, old Desktop without contract 2 | Recording metadata and file requests blocked; HA Repair asks to update Desktop |
| Old bridge, new Desktop | Explicit update refusal before enable; existing enabled setting retained but paused |
| Untested intermediate/future versions | No blanket vendor guarantee; missing source capabilities block that source only |

The general minimum stays 2025.2.0. A global increase would unnecessarily block
working brands. Per-source actual metadata, not a guessed Core version cutoff,
decides whether Reolink can supply reliable capture times.

## Source time and clock checks

Reolink SDK tzinfo ignores fold and its calendar transition calculation cannot be
used as proof. Conversion now uses the device's raw GetTime UTC/DST configuration:
seconds west of UTC, explicit DST offset and calendar transition rules. It computes
the offset at recording time, handles northern/southern seasons, rejects malformed
rules and checks both start and end. An autumn local time with two UTC candidates
or a spring time with none is skipped as an individual recording. Other valid
recordings continue. Skipped logical keys cannot later become late-old jobs when
their metadata changes.

A fresh read-only clock check rejects missing/wrong zone information, unsupported
settings and excessive device skew. Clock reads taking more than five seconds are
not accepted. The new-capture lower bound subtracts a conservative ten-second
uncertainty margin; no file inside that uncertainty interval is called new. The
30-second stable-revision and complete-media checks remain separate. Changed time
rules reset the connected window; reconnect still never imports an offline backlog.

The device must have correct historical clock/timezone configuration. Firmware
variants and manual historical clock rewrites cannot be universally certified from
current settings. No title, download/discovery time, current UTC offset or filename
timestamp is substituted. SDK PlaybackTime is not used as a universal UTC escape
hatch: some SDK paths synthesize it from a filename, and virtual file splitting can
retain the original PlaybackTime. Those are not proof of each chunk's capture time.

Ring still uses matching event ID, aware source created_at and recording ready status.
It needs recording entitlement and is latest-only. UniFi needs full event API access;
Tapo Cameras Control needs its explicit device offset/custom API; Blink needs an
aware source clip time. No new hardware certification is claimed.

## Contract 2 and user messages

Desktop advertises contract 2 in discovery/authenticated status. The bridge requires
that status and the matching per-request header for both listing and download. It
returns contract 2 with metadata. Desktop verifies it before enable and on every
listing, including revalidation before queue admission. Missing/unknown contracts
never fall back to an older intake policy. New HA keeps legacy general/event use,
but supplies an actionable EN/NL HA Repair and refuses new automatic video reads
from an old Desktop. New Desktop supplies EN/NL update/source/clock/skip messages.
No camera/model/dataset/Review deletion or re-pairing is required.

## Scoped verification and next gate

Targeted DST, clock, old/new metadata, mixed-peer, Repair, authorization and Ring
checks pass on HA 2025.2.0 and 2026.10.1. Relevant Desktop policy/contract, seven
original edges, dedup, 30s readiness, pairing and EN/NL JavaScript checks pass.
Unchanged broad test results are retained as historical evidence. Local Ruff and
Hassfest dependencies/manifest/translations pass. Hosted full validation must run
on the eventual approved push; no public push was authorized this session.

Next: exact-source final checks and coordinated packaged/hardware validation with
actual source timestamps, DST skips, one startup sample/new clip, reconnect/no
backlog, pairing revocation and preserved camera/model/Review ownership. Freeze
distinct distribution versions before building final artifacts. Existing signed
artifacts and historical beta tag remain immutable. No signing, release, tag,
HACS catalog submission or production deployment is authorized.
