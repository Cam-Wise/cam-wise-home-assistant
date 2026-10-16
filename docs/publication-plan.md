# Beta release, update test and HACS inclusion plan

The repository is public and HACS custom installation is validated. No tagged
release, announcement or official HACS submission has been made. Each requires
its own approval. See the [release checklist](../PUBLICATION_CHECKLIST.md) and
[draft notes](release-notes-v0.1.0-beta.1.md).

## First beta

Merge the documentation PR through protected main, require all four checks on the
exact candidate, and record commit/manifest/runtime identity. Obtain owner approval
for `v0.1.0-beta.1`, the release notes and the unproven Windows scope before creating
an immutable tag and prerelease. No new Desktop release is required.
After approval, verify a fresh HACS installation selects the exact released commit
and version; record HACS's prerelease selection behavior. Do not call a main-branch
download a successful tagged-release install. Do not change a published tag.

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
those checks. Recheck these requirements before submission; prerelease sufficiency
must be verified rather than assumed. Description/topics/Issues, valid manifests
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
