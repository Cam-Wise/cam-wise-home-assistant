# Release, update test and HACS inclusion plan

The repository is public and `v0.1.0-beta.1` is published as a limited developer
prerelease at `21516f8bff9fc8742bc215a602971a2b674f724d`. No announcement or official
HACS submission has been made; further releases and external publicity need their
own approval. See the [release checklist](../PUBLICATION_CHECKLIST.md) and
[draft notes](release-notes-v0.1.0-beta.1.md).

The next target is regular `v0.1.0`, with product name **Cam-Wise**, without a
prerelease label. Its three source version fields are prepared at 0.1.0. The
Windows packaged gate passed for signed Desktop 0.1.23 beta through a loopback
transport relay; direct LAN/mDNS and other Desktop versions remain unproven.
See [regular release notes](release-notes-v0.1.0.md). No regular tag/release exists
yet; obtain separate approval after exact-source checks on merged main pass.
The [preparation record](regular-release-preparation.md) separates official HACS
requirements from project gates and contains the future submission checklist.

## First beta

PR #1 was merged through protected main with four green checks; the owner approved
the exact source, notes and limited scope with Windows packaged E2E NOT PROVEN.
The immutable tag/release was created without a Desktop build or binary assets.
Fresh HACS 2.0.5 on HA 2026.10.1 found and installed the exact tag with beta visibility
enabled; configuration/entities/restart/reload/removal passed. This was a real
programmatic websocket test, not visual UI testing. Do not change the published tag.

## HACS update test after the first release

1. In disposable HA, install the approved first release through HACS. Save versions,
   commit, entity IDs, mapping and a configuration backup; use only a synthetic API.
2. When a subsequent integration version is separately approved and available,
   refresh HACS. Record whether it is offered under the chosen prerelease settings.
   Verify release notes and expected source identity before accepting the update.
3. Update through HACS, restart HA, and confirm new files/version plus preserved
   config-entry/device/entity IDs and mapping. Check three entities, options,
   offline/recovery and reload. Record behavior rather than assuming migration.
4. Exercise a supported rollback/re-download of the prior immutable release in the
   same disposable environment, restart, verify settings/entities, then remove the
   entry and uninstall. If HACS cannot select it, record the limitation and restore
   the test backup; do not claim native rollback PASS.
5. Report PASS/FAIL/NOT TESTED with exact old/new versions and HACS version. Keep
   credentials/media private. No fabricated tags or Desktop/account changes.

Current evidence: refresh and same-main redownload passed without duplicate config
entries. There is no version-to-version update evidence yet. Publishing the first
release alone cannot prove an upgrade to a later one.

## Official HACS inclusion, after separate permission

The [official requirements](https://www.hacs.xyz/docs/publish/include/) require a
public GitHub repository usable as a custom repository, green HACS Action without
errors/ignores, green Hassfest for integrations, and a full GitHub release after
those checks. Our submission will use a regular release, even though the cited
inclusion page does not impose a blanket ban on every prerelease. Its explicit
alpha/beta prohibition concerns testing or overriding Core integrations.
Description/topics/Issues, valid manifests
and brand assets must remain correct.

An owner or major contributor submits the repository alphabetically in the
`integration` file of `hacs/default`, following its current template. Use an
editable PR from a personal fork/new branch based on its default branch, not an
organization-owned submission fork. Passing checks does not guarantee acceptance.
Our additional gate is recorded install/update evidence and a separate submission
approval. No submission, fork, external PR or announcement is authorized by this plan.

References checked 2026-10-16:
[HACS integration requirements](https://www.hacs.xyz/docs/publish/integration/),
[HACS default inclusion](https://www.hacs.xyz/docs/publish/include/).
