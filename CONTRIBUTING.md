# Contributing

Clone this standalone repository and work on a feature branch. Tests require no
desktop application, camera, private repository, credentials or Cam-Wise data root.
Use Linux (WSL is suitable) and a separate environment for each matrix row.

| Home Assistant | Python | Pinned dependencies |
| --- | --- | --- |
| 2025.2.0 | 3.13 | requirements-test-min.txt |
| 2026.10.1 | 3.14.2 or newer 3.14 | requirements-test.txt |

On Debian/Ubuntu install build-essential for minimum-version native dependencies.
From the repository root:

```sh
python3.14 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-test.txt
python -m pip check
python -m ruff check custom_components tests
python -m pytest -c pytest.ini --confcutdir=. tests
```

Use Python 3.13, `.venv-min` and requirements-test-min.txt for the minimum row.
HA 2025.1 is unsupported because the canonical Zeroconf helper import is absent.
The explicit pytest config/conftest boundary prevents accidental parent-project
settings. Missing suites, import/collection errors and test failures must fail CI.

Tests use real HA flows, config entries, registries, states and platform lifecycle;
only the remote API is mocked with synthetic JSON in tests/fixtures. Sockets are
disabled. Do not substitute fake HA classes or include real media/credentials.
Fixes require meaningful regressions. Update HA and fixture pins together and run
both rows. Ruff explicitly targets Python 3.13 via pyproject.toml; no static type checker is
currently configured and no type-check pass or official quality tier is claimed.

## Architecture and review

client.py owns HTTP and schema validation; config_flow.py owns configuration;
coordinator.py owns shared polling; events.py owns bounded volatile delivery;
__init__.py owns setup/unload; entity/platform modules expose three status entities.
Prefer small fixes over speculative abstractions. Preserve config keys and IDs.
Read docs/api-contract.md and docs/event-reliability.md before delivery changes.

## Maintenance and release

Integration development, versioning, CI and releases are independent of desktop
updates. No private desktop source is needed or included. Shared API changes need
a separate approved design task; stronger receipts/authentication are not introduced
here. Do not couple integration releases to a desktop release branch or merge
unreviewed product changes. Keep development data isolated from active installations.

Main requires PRs and green HA 2025.2.0, HA 2026.10.1, HACS and Hassfest checks.
Force pushes/deletion are blocked; no second reviewer is required while there is
one maintainer. HACS/hassfest jobs run official actions with no ignored checks. Local
commands and successful workflow syntax checks do not prove hosted Actions passed.
Public HACS installation and hosted validation have passed. Follow
PUBLICATION_CHECKLIST.md before the separately approved first tagged beta;
Windows packaged E2E remains NOT PROVEN.
Codeowner: `@Bob-Cam-Wise`; repository: `cam-wise/cam-wise-home-assistant`.
Report functional bugs through GitHub Issues and propose code changes through pull
requests. Keep existing tests passing and add regression coverage for behavior fixes.
Document API-breaking changes explicitly in the contract and changelog; agree on
migration and versioning before merging them. Do not silently change API 1 behavior.
Security reports use the private route in SECURITY.md. There is no guaranteed
response or fix time. The intended security maintenance scope is the latest beta;
the maintainer handles reports through the monitored confidential mailbox.
