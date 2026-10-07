<!-- markdownlint-disable-file -->
# RPI Changes: Implement containerized code deployment and finalize Marketplace Managed Application package

## Metadata

* Task ID: `containerized-code-deployment-marketplace-managed-app`
* Related plan: [.copilot-tracking/plans/2026-10-07/containerized-code-deployment-marketplace-managed-app-plan.md](../../plans/2026-10-07/containerized-code-deployment-marketplace-managed-app-plan.md)
* Implementation date: 2026-10-07

## Execution Status

* Status: Complete
* Declared invocation scope: full plan
* Completed scope markers: P01, P01-T01, P01-T02, P02, P02-T01, P02-T02, P03, P03-T01, P03-T02, P04, P04-T01, P04-T02
* All remaining active-plan markers: none
* Status basis: All four phases and eight tasks across the declared full plan scope have been successfully implemented, verified, and validated with 107/107 passing tests and zero errors.

## Execution Summary

Successfully completed full implementation of containerized code deployment and Azure Marketplace Managed Application packaging across all four phases:
1. P01 (Web Application Entrypoints and Container Packaging): Added `fastapi`, `uvicorn`, and `httpx` dependencies; implemented FastAPI web host in [src/hr_time_leave/app.py](../../../src/hr_time_leave/app.py) with `/healthz`, `/readyz`, and Bot Framework `/api/messages`; implemented Service Bus background trigger in [src/hr_time_leave/function_app.py](../../../src/hr_time_leave/function_app.py); authored non-root [Dockerfile](../../../Dockerfile) and [.dockerignore](../../../.dockerignore); and exported public interfaces in [src/hr_time_leave/__init__.py](../../../src/hr_time_leave/__init__.py).
2. P02 (Infrastructure Bicep Containerization and Parameter Parity): Updated [infra/main.bicep](../../../infra/main.bicep) to configure Linux container App Service (`linuxFxVersion: 'DOCKER|${containerImage}'`, port 8000, storage false, 600s startup limit); recompiled [infra/mainTemplate.json](../../../infra/mainTemplate.json) via Bicep CLI; and verified 100% parameter parity with [infra/createUiDefinition.json](../../../infra/createUiDefinition.json) and zero secrets.
3. P03 (Managed Application Packaging and Partner Center Documentation): Enhanced [packaging/managed_app/package_managed_app.py](../../../packaging/managed_app/package_managed_app.py) with `validate_container_configuration` targeting App Service resources specifically; built and verified certified root-level [packaging/managed_app/app.zip](../../../packaging/managed_app/app.zip) with summary JSON; and authored [docs/deployment/marketplace-managed-app-guide.md](../../../docs/deployment/marketplace-managed-app-guide.md) documenting technical configuration, 8-hour JIT access, and IP Co-sell qualification.
4. P04 (Test Suite Expansion and End-to-End Validation): Created [tests/test_container_app.py](../../../tests/test_container_app.py) (19 tests) covering web endpoints, Bot routing, Functions SLA trigger, and Dockerfile directives; expanded [tests/test_managed_app.py](../../../tests/test_managed_app.py) with App Service container configuration tests; and verified the entire test suite (107 passed, 0 failed) and code style (`ruff check` clean).

## Completed Work

### FastAPI Application Entrypoint and Dependencies

* Related phase or task: P01-T01
* Files:
  * [pyproject.toml](../../../pyproject.toml)
  * [src/hr_time_leave/app.py](../../../src/hr_time_leave/app.py)
  * [src/hr_time_leave/__init__.py](../../../src/hr_time_leave/__init__.py)
* What changed and why: Added `fastapi>=0.110.0` and `uvicorn>=0.28.0` runtime dependencies and `httpx>=0.27.0` dev dependency. Created FastAPI web host in `app.py` supporting Bot Framework activity routing (`/api/messages`), liveness probe (`/healthz`), readiness probe (`/readyz`), and CORS middleware to serve as the App Service container entrypoint. Exported `app`, `application`, and `process_bot_activity` from package root.
* Completion evidence: Verified `uv sync` resolution and importability of `hr_time_leave.app`.
* Validation: Run and passed (unit tests passing).

### Functions SLA Background Trigger and Container Packaging

* Related phase or task: P01-T02
* Files:
  * [src/hr_time_leave/function_app.py](../../../src/hr_time_leave/function_app.py)
  * [src/hr_time_leave/__init__.py](../../../src/hr_time_leave/__init__.py)
  * [Dockerfile](../../../Dockerfile)
  * [.dockerignore](../../../.dockerignore)
* What changed and why: Implemented `process_service_bus_message` in `function_app.py` to ingest Service Bus messages and evaluate SLA jobs via `SLAEngine`. Authored production `Dockerfile` with non-root security context (`appuser:10001`), `EXPOSE 8000`, `/healthz` HEALTHCHECK probe, and Uvicorn launch command. Added `.dockerignore` to exclude development caches and sensitive files. Exported `process_service_bus_message` from package root.
* Completion evidence: `Dockerfile`, `.dockerignore`, and `function_app.py` created and validated against specifications.
* Validation: Run and passed (unit tests passing).

### Bicep App Service Containerization and Parameterization

* Related phase or task: P02-T01
* Files:
  * [infra/main.bicep](../../../infra/main.bicep)
* What changed and why: Added `containerImage` parameter defaulting to `mcr.microsoft.com/azure-app-service/python:3.11`. Updated `appService` resource siteConfig to `linuxFxVersion: 'DOCKER|${containerImage}'`, and added appSettings `WEBSITES_PORT: '8000'`, `WEBSITES_ENABLE_APP_SERVICE_STORAGE: 'false'`, and `WEBSITES_CONTAINER_START_TIME_LIMIT: '600'` to ensure fast cold starts and prevent MRG Deny Assignment file-system write lockups. Preserved serverless `functionApp` and zero-secrets RBAC.
* Completion evidence: Successfully updated `infra/main.bicep`.
* Validation: Run and passed (`az bicep build` compiled cleanly).

### ARM Template Compilation and Strict Parameter Parity Verification

* Related phase or task: P02-T02
* Files:
  * [infra/mainTemplate.json](../../../infra/mainTemplate.json)
  * [infra/createUiDefinition.json](../../../infra/createUiDefinition.json)
* What changed and why: Recompiled `infra/mainTemplate.json` from `infra/main.bicep` using Bicep CLI v0.47.16. Validated parameter parity against `infra/createUiDefinition.json`. Since `containerImage` specifies a `defaultValue`, it adheres to Managed Application Parity Rule 2 without altering the 8 customer-facing UI wizard parameters.
* Completion evidence: `package_managed_app.py --validate-only` confirmed schema validity, zero secrets, and 100% parameter parity.
* Validation: Run and passed (parity check and 84 tests passing).

### Scoped Container Packaging Validation and app.zip Assembly

* Related phase or task: P03-T01
* Files:
  * [packaging/managed_app/package_managed_app.py](../../../packaging/managed_app/package_managed_app.py)
  * [packaging/managed_app/app.zip](../../../packaging/managed_app/app.zip)
  * [packaging/managed_app/verification_summary.json](../../../packaging/managed_app/verification_summary.json)
* What changed and why: Added `validate_container_configuration` to `package_managed_app.py` targeting `Microsoft.Web/sites` (kind `app,linux`) for `DOCKER|...`, port 8000, 600s startup limit, and storage disabled. Wired check into `create_managed_app_package` and CLI. Assembled and verified root-level `app.zip` (6,468 bytes) containing `mainTemplate.json` and `createUiDefinition.json` with zero secrets. Generated verification summary JSON.
* Completion evidence: Verified package created and inspected `verification_summary.json`.
* Validation: Run and passed (packaging CLI passed with zero errors).

### Partner Center Managed Application Publishing Guide

* Related phase or task: P03-T02
* Files:
  * [docs/deployment/marketplace-managed-app-guide.md](../../../docs/deployment/marketplace-managed-app-guide.md)
* What changed and why: Authored comprehensive guide detailing offer creation, Managed Application plan setup, publisher authorization array (Tenant ID, Security Group Object ID, Contributor role `b24988ac-6180-42a0-ab88-20f7382dd24c`), 8-hour JIT access governance, metering dimensions, private audience testing steps, and IP Co-sell qualification requirements.
* Completion evidence: `docs/deployment/marketplace-managed-app-guide.md` created.
* Validation: Manual document structure review and link verification.

### Web Service, Functions SLA, and Dockerfile Unit Tests

* Related phase or task: P04-T01
* Files:
  * [tests/test_container_app.py](../../../tests/test_container_app.py)
* What changed and why: Implemented comprehensive test suite in `tests/test_container_app.py` covering GET `/healthz` probe schema, GET `/readyz` dependency checks, POST `/api/messages` activity routing and error handling (400 on malformed/missing type), `process_service_bus_message` SLA execution and ticket state transitions, and `Dockerfile`/`.dockerignore` compliance.
* Completion evidence: 19 unit and integration tests passing cleanly.
* Validation: Run and passed (`pytest tests/test_container_app.py`).

### Managed App Container Deployment Assertion Tests & Full Suite Verification

* Related phase or task: P04-T02
* Files:
  * [tests/test_managed_app.py](../../../tests/test_managed_app.py)
* What changed and why: Added `TestAppServiceContainerDeployment` class to `tests/test_managed_app.py` testing App Service Docker container configuration in compiled ARM template, siteConfig settings, and negative validation cases. Executed full test suite across entire repository.
* Completion evidence: 107/107 tests passing in 0.75s with zero regressions.
* Validation: Run and passed (`uv run pytest` and `uv run ruff check .`).

## Implementation-Time Plan Updates

None required. All implementation adhered to approved plan specifications and critique resolutions.

## Validation Record

| Check | Scope | Status | Evidence or reason |
|---|---|---|---|
| `uv run pytest tests/` | Full repository test suite | Passed | 107 passed in 0.75s across all 7 test modules |
| `uv run ruff check .` | Code style and formatting | Passed | All checks passed cleanly with zero warnings |
| `az bicep build` | Infrastructure ARM compilation | Passed | Compiled `infra/main.bicep` to `infra/mainTemplate.json` |
| `package_managed_app.py` | Package integrity and parity | Passed | Verified root-level `app.zip` (6,468 bytes), 100% parameter parity, 0 secrets |

## Pre-Review Reconciliation

* Plan markers and task-local context: All 4 phases and 8 tasks checked and reconciled.
* Completed-work evidence and handoff prose: Detailed evidence and links documented for all tasks.
* Validation, blockers, remaining work, and follow-up items: All validation checks passed, zero blockers, zero remaining work.
* Review readiness: Ready for review (`/rpi review`).

## Blockers

* None

## Remaining Work

* None (full plan scope complete)

## Follow-Up Items

* Canonical plan list: [.copilot-tracking/plans/2026-10-07/containerized-code-deployment-marketplace-managed-app-plan.md](../../plans/2026-10-07/containerized-code-deployment-marketplace-managed-app-plan.md), `## Follow-Up Items`
* None

## Return-to-Caller State

* Implementation execution status: Complete
* Declared scope and markers: full plan (P01: P01-T01, P01-T02; P02: P02-T01, P02-T02; P03: P03-T01, P03-T02; P04: P04-T01, P04-T02)
* Validation coverage: 107 tests passed (100% pass rate), ruff linter clean, ARM template compiled, package verified
* Blockers: None
* Current plan updates: None
* Planning and critique state: All critique findings (PC-001 through PC-005) fully implemented and verified
* Follow-up items: None
* Review readiness or no-handoff reason: Ready for review
* Continuation owner: user
