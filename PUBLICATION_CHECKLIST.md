# Publication gates

This candidate is not ready for public distribution. No publication is authorized.

- Confirmed identity: `cam-wise/cam-wise-home-assistant`, codeowner `@Bob-Cam-Wise`.
  Prepared documentation/issues URLs refer to the not-yet-created repository.
  Confidential mailbox access/monitoring and maintenance ownership are confirmed.
  Public attribution uses Bob-Cam-Wise and the owner's GitHub noreply address;
  default branch and repository creation remain subject to final approval.
- Copyright holder, scoped MIT authorization and integration-use brand permissions
  are recorded. Preserve third-party notices if future contributions add any.
  Review every file in the explicit export inventory before publication.
- Run required HA 2025.2.0 and 2026.10.1 tests, dependency checks and lint.
- Run hassfest and HACS validators with zero errors/ignored checks. Hosted HACS
  checks require a real public repository; no pretend repository IDs or validators.
- Require both HA matrix jobs, HACS and Hassfest in repository branch protection;
  check names alone do not configure GitHub required status checks.
- Record real manual installation/configure/reload/restart/remove evidence, plus
  HACS install/update and actual desktop/media compatibility evidence.
- Decide trusted-LAN beta policy and version/release maintenance policy. Proposed
  first tag is v0.1.0-beta.1 (manifest 0.1.0-beta.1); no tag/release is made.
- Export only allowlisted reviewed files, never private repository Git history.
- Request separate explicit publication approval after blockers are resolved.

References checked 2026-10-14:
[HACS general](https://hacs.dev/docs/publish/start/),
[integration](https://hacs.dev/docs/publish/integration/),
[action](https://hacs.dev/docs/publish/action/),
[hassfest](https://developers.home-assistant.io/blog/2020/04/16/hassfest/).
Only public GitHub repositories work with HACS. `render_readme` is currently
documented; old claims that it is unsupported or private HACS tests work are stale.

Owner-proposed choices and immediate post-publication checks are recorded in
[publication-plan](docs/publication-plan.md). Official HACS listing needs new permission.
