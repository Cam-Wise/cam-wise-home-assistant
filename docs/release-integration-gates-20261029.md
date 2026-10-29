# Coordinated recording candidate — 2026-10-29

Status: **BLOCKED**, source integration/review only. No tag, release or HACS catalog
submission is authorized. Runtime source version is still 0.1.1b0; that identifier
is shared by older candidates and cannot establish recording-contract support.

## Source capture time

Ring Core 2025.2.0 and 2026.10.1 retain the last vendor history event and only set
the recording URL/video ID for status `ready`. The adapter requires that exact
ID and its `created_at`, normalized from an aware datetime/ISO time. This is
source event time, not the HA state update or file download time. Ring is latest
only and requires recording entitlement; missing/mismatched history pauses intake.
Real hardware acceptance of this new timing adapter is still required.

Reolink Core 2026.10.1 FILE identifiers contain SDK StartTime/EndTime values. The adapter
uses the device timezone, not the server timezone or media-browser title. Both
SDK versions now use a strict 14-digit standard-library parser, followed by
explicit device-timezone attachment. SDK 0.11.9 only parses time dictionaries,
whereas 0.21.18 also parses strings; the original adapter passed strings to both.
The test dependency sets now explicitly install the matching vendor libraries.

**Release blocker: older Reolink Core.** HA 2025.2.0 emits five-part FILE
identifiers, without StartTime/EndTime. The current adapter requires seven parts
for stable identity and source capture time. It cannot preserve recorded-video
intake on that route; even green synthetic seven-part fixtures on HA 2025.2.0 do
not prove otherwise. Resolve supported route/version negotiation or supply actual
source timing through the older vendor API. Do not infer it from titles, filenames,
discovery time or download time. Ring Core on that HA version does retain its event.

**Release blocker: Reolink DST.** SDK `Reolink_timezone` ignores `datetime.fold`.
The current fold comparison therefore cannot reject an ambiguous rollback wall
time. With synthetic DST rules and the actual 0.21.18 SDK, a wall time 30 minutes
before its own rollback boundary is accepted as completed with one guessed UTC
instant. Both occurrences have the same offset under fold=0/1. The SDK also
computes calendar transitions itself; do not assume an IANA-zone test proves this
type. Fixed-offset/no-DST tests pass but do not clear this blocker. Do not ship
the Reolink timed route until ambiguity is demonstrably rejected or unambiguous
source UTC/offset metadata is available. Do not substitute discovery time.

Other routes remain conditional: UniFi needs full event API access and uses vendor
event milliseconds; Tapo Cameras Control needs the explicit device offset and its
custom API version; Blink needs aware clip times and is bounded to cached clips.
Missing offsets, naive/local labels, future timestamps or unavailable metadata
must pause with the Desktop timing message. No all-vendor hardware certification.

## Mixed versions

| Desktop | HA bridge | Result |
|---|---|---|
| New timed intake | Matching new metadata | One explicit startup sample, then connected-window captures, subject to source timing validity |
| New timed intake | Old IDs without stable key/revision | Explicit identity/update error; no download |
| New timed intake | Stable IDs but no typed capture/completion | Explicit timing pause; enabled setting retained |
| Older intake | New additive metadata | Older code ignores extra fields and retains its older intake/backlog policy |
| No recording-intake support | New HA | No automatic recording feature is created by updating HA alone |

**Release blocker: mixed-version rollout.** Additive API 1 metadata does not make
older Desktop obey the new policy. There is no negotiated recording-contract
capability/minimum Desktop gate yet. A version label shared by several candidates
is insufficient. Do not advertise the new guarantees to mixed pairs or silently
update an existing working pair. Coordinated update and an explicit compatibility
gate/message must be resolved before final release validation; no new API has been
invented during this integration pass.

## Validation and remaining distribution work

The seven original Desktop edge regressions pass on the coordinated source.
Source tests do not prove a packaged artifact. Historical physical Ring download
and Reolink processing evidence predates the new time contract and is reused only
for the unchanged download paths. Existing user data is not a test fixture.

Keep the public repository limited to this MIT HA component, public documentation,
synthetic tests and CI. Use the protected PR; never merge private Desktop source or
history here. Keep historical beta tags unchanged. Select fresh compatible release
versions only after blockers are cleared; 0.1.23 Desktop and old draft 0.1.0 notes
must not be silently reused for changed release bytes.

After the blockers are cleared: require exact-source HA matrix, HACS, Hassfest and
Desktop release checks; then one isolated unsigned packaged test on 8017 with a full
WorkTest root. Test one explicit initial completed clip and one new clip for Ring
and Reolink, no offline backlog/replay after restart/reconnect, and unchanged camera,
model, Review and dataset ownership. Exercise pairing revocation/reconnect and full
shutdown. Do not repeat unchanged large manual tests. Signing/publication require
separate authorization.
