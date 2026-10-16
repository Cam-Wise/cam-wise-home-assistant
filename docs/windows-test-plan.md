# Manual Windows compatibility test

Status: plan only; Windows packaged E2E is NOT PROVEN. A user with a legitimate
signed Cam-Wise installation and account can perform this small test after agreeing
to its scope. Do not use a live camera or alter a working household installation.

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
