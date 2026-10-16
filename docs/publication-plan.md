# Beta publication and verification plan

## Prepared choices (no publication authorization)

- Repository identity: `cam-wise/cam-wise-home-assistant`; codeowner: `@Bob-Cam-Wise`.
  The human confirms organization settings/2FA; the repository is not yet created.
- Intended first tag: `v0.1.0-beta.1`; manifest/runtime version: `0.1.0-beta.1`.
- License: MIT for integration software/documentation; brand assets have separate terms.
- Support: https://github.com/cam-wise/cam-wise-home-assistant/issues (intended
  repository URL, available only after separately approved publication).
- Confidential security route: `support@cam-wise.com`, supplied by the owner;
  confidential access, monitoring and maintenance ownership are confirmed.
- Network scope: explicitly trusted LAN only, no unauthenticated internet exposure.
- Desktop and integration have independent versions, CI and release processes.

These proposed choices prepare the source only. Repository creation, public push,
tags/releases and official HACS submission are not authorized.

## Before requesting GitHub publication approval

1. Record real owner/codeowner, public commit attribution, repository/default branch,
   documentation/issues URLs and support/security maintenance policy. Do not invent
   GitHub handles or publish personal email addresses through Git configuration.
2. Confirm legal copyright holder, rights for contributors/copied code and logo
   sublicensing. MIT is not proof of provenance. Remove optional assets if rights
   cannot be established; do not conceal unresolved rights issues.
3. Complete independent code/security review and resolve blockers. Record reviewer,
   exact source/package identity and findings. A same-author second pass is not an
   independent review. Obtain explicit trust-policy approval.
4. Prove HA-to-desktop event intake and desktop-to-HA media retrieval/processing in
   disposable environments with synthetic media. Record exact source/build versions,
   review-item result, retry/dedup, reload/restart, offline/recovery and teardown.
   Do not substitute a synthetic desktop server for real desktop evidence.
5. Run both pinned HA suites, dependency/lint/syntax/workflow checks and full official
   hassfest. Run every HACS check possible without creating/pushing a repository;
   identify GitHub-dependent checks as deferred, not passed or ignored.
6. Export only reviewed allowlisted files into a fresh directory, verify byte hashes,
   run a secrets/private-content scan and inspect the final archive. No monorepo
   `.git`, old objects, remotes, internal reports, userdata or desktop dependencies.
7. Owner approves the precise archive SHA, metadata, unresolved deferred checks and
   the bounded post-publication plan. Request a new explicit GitHub publication command.

## Immediately after separately authorized public GitHub creation

1. Create the approved empty repository and import a **fresh history** from the
   approved allowlist. Do not push/rewrite the private desktop repository history.
   Verify new initial commit contains exactly approved files and public attribution.
2. Verify repository visibility/name, description/topics, license display, README,
   Issues, security policy, codeowners and default branch. Add GitHub required status
   checks for HA 2025.2.0, HA 2026.10.1, HACS and Hassfest; no bypass/ignored checks.
3. Run all Actions and official HACS validation against the actual GitHub identity.
   Confirm every required job runs and passes. Record URLs, run IDs and commit SHA.
4. Clone anonymously into a clean environment; verify contents/hashes/history and
   no access to private repos, secrets or development paths. Independently run tests.
5. Test actual HACS custom-repository install plus manual install in disposable HA,
   followed by configure/reload/restart/remove and real desktop/media E2E. Test update
   only when a separately authorized subsequent candidate/version is available;
   don't fabricate a released upgrade or reuse an immutable published tag.
6. If any security/rights/private-content or validator blocker appears, stop promotion
   and releases. Notify owner and resolve before announcing install readiness. Do not
   silently lower gates, force-push or treat deletion as revoking leaked credentials.
7. Source publication and GitHub release publication are separate approvals. Only
   create the intended beta tag/release after release approval and all release gates.
   Reconfirm manifest/tag/source identity and beta limitations in release notes.

## Later official HACS listing (new approval required)

Public custom-repository usability does not equal official HACS inclusion. After
successful public validation, installation/update evidence and an approved release,
request another explicit permission before submitting to HACS default repositories.
No submission, PR, tag, release or external announcement is authorized by this plan.

References: [HACS general](https://hacs.dev/docs/publish/start/),
[HACS inclusion](https://hacs.dev/docs/publish/include/),
[HACS action](https://hacs.dev/docs/publish/action/).
