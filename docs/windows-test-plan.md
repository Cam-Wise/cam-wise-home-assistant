# Manual Windows compatibility test

Status: reproduction plan. Signed Windows Desktop 0.1.23 beta passed functional
E2E on 2026-10-17 through a loopback transport relay, including actual restart.
See [compatibility](compatibility.md) for the evidence scope. Direct LAN/mDNS and
other Desktop versions are not proven. A user with a legitimate signed installation
and account can reproduce this test after agreeing its scope. Do not use a live
camera or alter a working household installation.

## Prerequisite decision before starting

The completed test used a new regular Free account through normal production
registration, email verification and owner-approved device coupling. No supported
isolated nonproduction account/issuer route has been established. Reproduction
with a disposable account using the normal account service requires the
owner's explicit agreement to that service contact and confirmation that this
test identity/device is safe to activate. A VM alone does not isolate cloud data.
If service contact is excluded and no supported test issuer exists, report
`BLOCKED: legitimate account path unavailable`; do not launch an experiment.
No Cloudflare configuration change, new Desktop build or copied activation is needed
or authorized. Enter credentials only in the normal app, never in chat or reports.

## Execution

1. Use a disposable Windows test user/VM, separate HA configuration and a backup
   or snapshot. Record HA/HACS/integration versions, installed Desktop version,
   executable SHA-256 and valid Authenticode signer. No rebuild or signing.
2. Before launching, establish a new empty full root under that test user's
   `%LOCALAPPDATA%/Cam-Wise-WorkTest` using the build's supported root override
   (`CAM_WISE_USER_DATA_ROOT` in the inspected source). Request port 8017 with
   `CAM_WISE_PORT`; first verify it is free. These settings have not been proven
   on the packaged runtime. Confirm the actual root and port through `/environment`
   and `/health`; a preferred port can fall back. Stop on any mismatch, unknown
   write location or interaction with an existing instance. Do not change resource
   roots, bundled keys, signatures or install files.
3. Use only a legitimate account/device activation explicitly authorized for this
   disposable profile. Never copy an existing binding, DPAPI store or entitlement,
   forge one, or use source-only bootstrap/test trust. If a valid isolated account
   cannot be established, stop: report startup/status only, not processing PASS.
   Normal activation can contact the account service; agree that scope separately.
   Under a no-production-service test policy, require a supported nonproduction
   path or stop. Do not silently redirect production requests to a fake issuer.
4. Keep API access on a trusted test LAN, firewall-restricted to the test HA peer.
   Configure normal Desktop HA/media settings only in the empty profile. Use a
   synthetic clip accessible through the supported HA media route; protect any
   media credentials. Select an authorized model suitable for the synthetic test.
5. Install through HACS custom repositories, restart HA, configure Desktop host
   and actual port, and check status/review-count/attention entities. Send one
   controlled event through the test HA camera/event mapping. Record acceptance
   separately: `accepted` does not mean `processed`.
6. Check Desktop's actual media retrieval and processing evidence, then the Review
   item and image. If the model produces no detection, record download/inference
   separately and mark Review unproven; do not invent a successful detection.
   Never automatically replay an accepted event just because Review is empty.
7. Reload and restart HA, verify settings/entities, remove the integration entry,
   uninstall through HACS, and restart HA again. Stop Desktop normally and verify
   its test process/children/listener have stopped and 8017 has no listener.
8. Record PASS/FAIL/NOT TESTED for each step, exact build/hash, account scope (no
   identifiers or tokens), synthetic route and cleanup. Share only redacted evidence
   in Issues; send security findings privately. A Windows PASS applies only to the
   tested build/route, not every packaged version or camera vendor.

## Exact operator checklist and return record

Use a fresh Windows test user/VM and disposable HA, with snapshots. The following
launch preparation is only for that profile after the account prerequisite above
is resolved. Use the already installed signed executable; do not run the source
Work/Test start script for this packaged test. In PowerShell:

```powershell
$testExe = Join-Path $env:LOCALAPPDATA 'Programs\Cam-Wise\Cam-Wise.exe'
Get-AuthenticodeSignature -LiteralPath $testExe | Select-Object Status,SignerCertificate
Get-FileHash -LiteralPath $testExe -Algorithm SHA256
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object LocalPort -in 8000,8017,8021
```

Stop if 8017 is occupied. A fresh VM should have no existing Cam-Wise process;
close only the test user's instance normally if needed. Do not stop a household
instance. Previous reference EXE: signed 0.1.23, SHA256
`47fa791a04bec1b7e3b9f24435079ac6a3b3415bc08e67fffcefc78a727e9f11`.
If the installed official build differs, record it and reassess supported options;
do not assume this reference certifies another binary.

```powershell
$testRoot = Join-Path $env:LOCALAPPDATA ('Cam-Wise-WorkTest\ha-packaged-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
if (Test-Path -LiteralPath $testRoot) { throw 'Test root must be new' }
$env:CAM_WISE_USER_DATA_ROOT = $testRoot
$env:CAM_WISE_PORT = '8017'
Start-Process -FilePath $testExe -WindowStyle Hidden
```

Open `http://127.0.0.1:8017/ui`. Before activation or importing anything, inspect
`http://127.0.0.1:8017/environment` and `/health`: full data paths must be under
the new root, port 8017 and packaged=true with the recorded version. Stop normally
on mismatch. In the VM, restrict network access to the test HA/media peer and only
the account-service destinations agreed above; verify those rules before launch.
Do not assert that URL overrides alone prevent production access.

Then follow these actions and record each result:

1. Activate only the authorized test identity normally. Confirm coupled/active and
   automatic processing enabled. Configure Desktop's HA connection/media credential
   against the disposable HA only; never export that credential.
2. In disposable HA HACS, add this repo as Integration, select the existing beta
   explicitly, download and restart. Add Cam-Wise using the test PC's reachable
   test-LAN address and **8017** (not HA's own loopback on a different machine).
   Enable Desktop LAN access only on the isolated peer-restricted network. Record
   the three actual entity IDs and initial status/count/attention values.
3. Configure one test camera mapping, a motion/event mapping and recording mapping.
   Use a synthetic recording already reachable via Desktop's supported HA media
   route, with no real footage. Record its SHA256 and an authorized model/version.
   In HA Developer tools > States, change the mapped recording entity's `video_id`,
   `media_id` or `last_video_id` attribute from its baseline to that valid test media
   identifier; if a motion event is required by the selected mapping, trigger its
   normal off-to-on event first. Use a new identifier for a new test. Preserve the
   entity's other attributes. This exercises HA forwarding, not a physical camera.
4. Record integration received/forwarded/accepted diagnostics (redacted). Check
   Desktop media download, inference completion and Review image separately. A
   successful event without a detection is not Review PASS; choose a suitable
   synthetic test clip/model, or report that missing result. Do not replay accepted
   work simply to obtain a Review item. Check count/attention reflect actual state.
5. Reload Cam-Wise in HA and restart HA; verify mappings and the same entity/device
   IDs. Stop only the test Desktop normally; allow at least 45 seconds for HA to
   become unavailable. Relaunch with the same two environment variables/root and
   verify status recovers within 60 seconds. Report observed timings/failures;
   do not silently broaden timeouts. Existing accepted work need not replay.
6. Delete the HA integration, uninstall via HACS and restart HA. Close Desktop
   normally. Check test process/children exited and 8017 is free; retain snapshots
   and test evidence until reviewed. Do not uninstall or delete another profile.

Return this filled record to the maintainer (no tokens, account/device identifiers,
private IPs, media URLs or raw logs). Screenshots may be redacted:

```text
Windows / HA / HACS / integration versions:
Desktop version / EXE SHA256 / signature status and signer:
Dedicated profile + empty WorkTest root + actual port verified: PASS/FAIL
Legitimate test account/service scope agreed and activated: PASS/FAIL/BLOCKED
HACS install / configure / three entity values: PASS/FAIL + observations
Synthetic clip hash / authorized model version:
Event received / forwarded / accepted: values or NOT TESTED
Media download / inference / Review item+image: PASS/FAIL/NOT TESTED each
Status, review count and attention updates: observations
HA reload / restart / preserved IDs+mapping: PASS/FAIL each
Desktop unavailable / recovery: PASS/FAIL + elapsed seconds
HA entry deletion / HACS uninstall / restart: PASS/FAIL each
Desktop process+children exited / port 8017 free: PASS/FAIL each
Unexpected error or changed data outside test profile: NONE or redacted detail
```

This test does not cover a future stable release installation or two-version
update/rollback. Those follow the separate release sequence after approval.
