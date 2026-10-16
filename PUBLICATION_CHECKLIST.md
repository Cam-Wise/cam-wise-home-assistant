# First beta release checklist

Current source is public; this checklist does not authorize a tag or release.

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

- [ ] Merge documentation PR through protected main; all four checks pass on the
  exact release candidate. Verify final commit, manifest/runtime version and notes.
- [ ] Record Windows packaged E2E evidence using the [manual plan](docs/windows-test-plan.md),
  or explicitly approve a limited beta with Windows marked NOT PROVEN. Do not
  silently convert source-runtime evidence into Windows certification.
- [ ] Owner approves the exact commit and draft [release notes](docs/release-notes-v0.1.0-beta.1.md),
  including trusted-LAN-only use and accepted != processed.
- [ ] Obtain separate permission for immutable tag `v0.1.0-beta.1` and GitHub
  prerelease; verify which prereleases the installed HACS version offers.

## After the approved first release

- [ ] Test installing the exact released version in fresh HA and record HACS
  version/prerelease selection. Branch download evidence alone is insufficient.
- [ ] When a later version is separately approved, run the real update/rollback
  [plan](docs/publication-plan.md#hacs-update-test-after-the-first-release).
- [ ] Recheck current [official HACS requirements](https://www.hacs.xyz/docs/publish/include/)
  and obtain separate submission permission. No submission or announcement is implied.
