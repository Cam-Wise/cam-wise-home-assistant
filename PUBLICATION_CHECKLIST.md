# Cam-Wise release checklist

## Regular v0.1.0 preparation (2026-10-17)

- [x] Record signed Windows Desktop 0.1.23 beta functional E2E, including actual
  restart, through loopback transport relay; direct LAN/mDNS/other versions unproven.
- [x] Align manifest, runtime and protocol fixture at 0.1.0; finalize notes,
  changelog, installation and bounded public compatibility summary.
- [ ] Verify all four required checks on the protected version PR and merged main;
  record the exact green release commit in the maintainer handoff.
- [ ] Obtain separate approval for immutable v0.1.0 tag/full regular GitHub release.
- [ ] After publication, verify exact regular HACS selection/install and genuine
  two-version update/rollback before the separately approved official submission.

No release, tag, HACS application or announcement is authorized by this checklist.
Historical beta record follows; its Windows limitations describe that prior decision.

## Historical first beta

`v0.1.0-beta.1` is published as a limited developer-preview prerelease.
This record does not authorize a further tag, release or HACS submission.

## Completed baseline (2026-10-16)

- [x] Standalone public repository, MIT scope, separate brand terms, CODEOWNER and
  confidential contact recorded; no private Desktop code/history or user data.
- [x] HA 2025.2.0 and 2026.10.1: 89 tests each; dependency/Ruff/syntax checks pass.
- [x] Hosted HACS Action and Hassfest pass without ignored checks.
- [x] HACS custom install, real-process restart/config/entities/reload/removal pass.
- [x] Linux Desktop 0.1.23 source-runtime media/inference/Review E2E passes.
- [x] Main requires PRs/four strict checks; force push/deletion blocked; no second
  reviewer required for the sole maintainer. Private vulnerability reporting enabled.

## Before v0.1.0-beta.1

- [x] Merge documentation PR through protected main; all four checks pass on the
  exact release candidate. Verify final commit, manifest/runtime version and notes.
- [x] Record Windows packaged E2E evidence using the [manual plan](docs/windows-test-plan.md),
  or explicitly approve a limited beta with Windows marked NOT PROVEN. Do not
  silently convert source-runtime evidence into Windows certification.
- [x] Owner approves the exact commit and draft [release notes](docs/release-notes-v0.1.0-beta.1.md),
  including trusted-LAN-only use and accepted != processed.
- [x] Obtain separate permission for immutable tag `v0.1.0-beta.1` and GitHub
  prerelease; verify which prereleases the installed HACS version offers.

Owner approved the explicitly limited scope with Windows NOT PROVEN. Tag
`v0.1.0-beta.1` points to `21516f8bff9fc8742bc215a602971a2b674f724d`, marked
Pre-release and not Latest; no binary assets. Exact HACS 2.0.5 install/lifecycle
passed on fresh HA 2026.10.1. No Windows certification is implied.

## After the approved first release

- [x] Test installing the exact released version in fresh HA and record HACS
  version/prerelease selection. Branch download evidence alone is insufficient.
- [ ] When a later version is separately approved, run the real update/rollback
  [plan](docs/publication-plan.md#hacs-update-test-after-the-first-release).
- [ ] Recheck current [official HACS requirements](https://www.hacs.xyz/docs/publish/include/)
  and obtain separate submission permission. No submission or announcement is implied.
