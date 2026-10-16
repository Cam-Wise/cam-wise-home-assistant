# Cam-Wise regular release and HACS preparation

Verified 2026-10-16 against public main `628a2ba0299273b74811dd88c3386428e9b5994a`.
This is preparation, not release or submission approval. Product name: **Cam-Wise**;
domain: `cam_wise`. Keep the existing beta tag/release immutable and available.

## Requirements and evidence

| Check | Result | Basis |
| --- | --- | --- |
| Public, active GitHub repository; one integration in custom_components | PASS | Public main; not archived |
| Description, topics, Issues | PASS | Description corrected; cam-wise/custom-component/hacs/home-assistant topics; Issues enabled |
| README, installation, maintainer, licensing | PASS | Public docs, MIT software scope, separately authorized brand images, @Bob-Cam-Wise CODEOWNER |
| manifest.json / hacs.json / branding | PASS | Name Cam-Wise, domain cam_wise, real URLs/codeowner; local brand/icon.png and logo.png |
| HACS Action with no disabled checks or ignores | PASS on audited main | [HACS run](https://github.com/Cam-Wise/cam-wise-home-assistant/actions/runs/38949840343) |
| Hassfest | PASS on audited main | [Hassfest run](https://github.com/Cam-Wise/cam-wise-home-assistant/actions/runs/38949840726) |
| Supported HA boundaries and dependencies | PASS | [HA matrix](https://github.com/Cam-Wise/cam-wise-home-assistant/actions/runs/38949840657): HA 2025.2.0/Python 3.13 and HA 2026.10.1/Python 3.14; 89 tests each, dependency/lint/syntax gates |
| Core domain conflict | PASS at audit | Current Core dev tree contains neither cam_wise nor camwise component; HACS validator also passes |
| Existing catalog duplicate | PASS at audit | No cam-wise/camwise repository in current hacs/default integration list; this is not a universal name reservation |
| Full GitHub release after validators | PASS for historical beta | v0.1.0-beta.1 exists; this does not satisfy our regular-release decision |
| Regular v0.1.0 | FAIL / pending | Not created; owner approval and Windows evidence required |
| Windows signed packaged E2E | FAIL / not proven | Project quality gate, not a separate official HACS Windows requirement |
| Real release-to-release update/rollback | NOT TESTED | Project gate before submission; requires second approved release |

Official requirements: [inclusion](https://www.hacs.xyz/docs/publish/include/),
[integration layout/manifest/brand](https://www.hacs.xyz/docs/publish/integration/).
HACS requires a full release after successful actions. The choice of a non-prerelease
`v0.1.0`, Windows E2E, protected-main HA matrix and recorded upgrade/rollback evidence
are additional Cam-Wise requirements. No official HA quality tier is claimed.
The project has no regional limitation, so a country restriction is unnecessary.
Independent HACS/Core review may still identify conflicts or maintenance concerns.

## Smallest release sequence

1. Complete the [Windows test](windows-test-plan.md) with legitimate isolated account
   activation and record exact signed build, media/inference/Review and lifecycle.
   Do not run another complete HACS/Linux E2E merely to reproduce existing proof.
2. In one protected PR, set manifest.json `version`, const.py `INTEGRATION_VERSION`
   and tests/fixtures/integration-status.json `version` to `0.1.0`. Add dated
   CHANGELOG entry and final release notes with the actual Windows result. Replace
   installation step 2 with selection of regular v0.1.0 without beta visibility.
   These version changes are deliberately deferred until the quality gate passes;
   the preparation branch remains honestly identified as the existing beta.
3. Run all four required checks on the exact proposed version and merged main.
   Review runtime/fixture identity through the existing metadata test. Record the
   final commit and check URLs; old green links cannot certify a changed version.
4. Obtain separate permission, then create tag/full GitHub release v0.1.0 at that
   exact green commit, prerelease=false. Do not replace beta. No Desktop build,
   installer, signing, Cloudflare changes or binary assets are needed.
5. In disposable HA, verify stable discovery without show_beta and the existing
   [two-version update/rollback plan](publication-plan.md#hacs-update-test-after-the-first-release)
   from beta. Check file/version identity, mappings/device/entity IDs, restart,
   offline/recovery, reload and rollback. A beta-to-stable upgrade is real two-version
   evidence; it does not prove later stable-to-stable migrations. If rollback is
   unavailable, record backup restoration and the limitation separately.
6. Recheck HACS requirements and obtain separate permission for the default-list PR.

Existing evidence covers custom HACS installation/configuration/entities/reload/
removal, Linux source event/media/ONNX/Review, and source tests for temporary Desktop
failure/recovery. Windows packaged processing and production account issuance are
not inferred from that evidence. No existing implementation defect requires a refactor.

## Future hacs/default submission packet (do not submit yet)

Submit as `Bob-Cam-Wise`, the recorded maintainer/contributor, from a personal fork.
Create a new branch from upstream `master`; allow maintainer edits. Change only
the JSON `integration` list, inserting alphabetically:

```json
  "caliusoptimus/venceiver",
  "caliusoptimus/venmulator",
  "Cam-Wise/cam-wise-home-assistant",
  "caplaz/home-assistant-controllable",
  "caplaz/home-assistant-sfpuc",
```

These neighbors were verified at audit time; fetch the current list and sort again
before submitting. Proposed title: `Add Cam-Wise integration`.

The current [official PR template](https://github.com/hacs/default/blob/master/.github/PULL_REQUEST_TEMPLATE.md)
has six checklist statements: publishing docs read; HACS Action added; Hassfest
added; all checks pass without disabled checks; successful action links supplied;
new release created after successful validation. Retain its exact current wording
when submitting. Do not mark the final release statement complete yet.

Required links for the future PR:

- Current release: https://github.com/Cam-Wise/cam-wise-home-assistant/releases/tag/v0.1.0
  (planned, absent; do not claim it exists).
- Successful HACS Action without ignore key: replace with exact final release-source run.
- Successful Hassfest: replace with exact final release-source run.

The audited-main run links above are baseline evidence, not final submission links.
Check submitter eligibility, release availability, active repo/Issues/topics,
manifest/brand, Core conflict and sorted valid JSON again. Do not request expedited
review; HACS documents that review can take months. Green checks do not guarantee
acceptance. No fork or hacs/default PR has been created for this preparation.
