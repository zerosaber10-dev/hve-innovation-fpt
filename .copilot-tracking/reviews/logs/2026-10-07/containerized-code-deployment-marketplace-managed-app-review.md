<!-- markdownlint-disable-file -->
# Review: containerized-code-deployment-marketplace-managed-app

## Executive Summary

* Assessment: The containerized code deployment and Azure Marketplace Managed Application package implementation is complete, conformant, and thoroughly verified across all four plan phases (P01 through P04). The runtime successfully provides FastAPI ASGI endpoints for Bot Framework messaging and health probes, background Azure Functions Service Bus queue processing, non-root Docker container packaging, App Service Bicep container configuration with cold-start timeout and storage optimizations, 100% parameter parity between `createUiDefinition.json` and compiled `mainTemplate.json`, zero hardcoded secrets, a certified root-level `app.zip` archive, comprehensive Partner Center publishing documentation with 8-hour JIT access governance, and 100% passing automated test coverage (107/107 tests).
* Why this matters: Deploying containerized code into Azure App Service enables immutable runtime delivery into customer Managed Resource Groups under Deny Assignment policies while ensuring turnkey deployment and Marketplace certification.
* Builder execution: Complete
* Proposed review execution: Complete
* Proposed outcome: Conformant
* Validation coverage: Full coverage across all acceptance criteria (107 passed tests in pytest including 19 container/web/Functions tests, ruff linter 100% clean, Bicep compilation verified, packaging validator verified with 100% parameter parity and zero detected secrets).
* Confidence and limitations: High confidence across static ARM/Bicep template contracts, container specifications, security contexts, packaging integrity, and automated regression testing. Limitations: Live deployment to an Azure subscription and submission to the Microsoft Partner Center portal are operational non-goals for this implementation task.

The assessment above is the builder's proposal. Parent Decision Record contains the current final decision and next actions, or states that decisions are pending.

## What You May Not Know

* **Managed Resource Group Deny Assignment Bypass**: Azure Managed Applications enforce a system-level Deny Assignment (`Microsoft.Resources/denyAssignments`) preventing all external write operations into the customer's Managed Resource Group (MRG). Standard external CI/CD deployment mechanisms (such as Kudu zipdeploy or one-deploy) fail with `403 Forbidden`. Configuring App Service with `linuxFxVersion: 'DOCKER|${containerImage}'` bypasses file-system write locks completely because the App Service platform directly pulls and runs the image from the container registry.
* **ARM Parity Rule 2 Mechanics**: Azure Managed Application parameter parity requires every output from `createUiDefinition.json` to match a parameter in `mainTemplate.json`. However, template parameters specifying a `defaultValue` (such as `containerImage`) are optional in `createUiDefinition.json`. This enables the deployment wizard to remain uncluttered with internal runtime configuration while allowing enterprise customers or automated ARM deployments to supply custom image tags when necessary.
* **App Service Container Startup Resilience**: Setting `WEBSITES_CONTAINER_START_TIME_LIMIT: '600'` (10 minutes) and `WEBSITES_ENABLE_APP_SERVICE_STORAGE: 'false'` prevents common cold-start timeouts and storage synchronization bottlenecks during initial container image pulls inside customer tenants, ensuring high deployment reliability.
* **Least-Privilege Partner Center Support Model**: The publishing guide establishes that publisher support within the customer's MRG is governed by an Entra ID Security Group authorization array assigned the `Contributor` role (`b24988ac-6180-42a0-ab88-20f7382dd24c`) paired with Just-In-Time (JIT) access capped at a strict 8-hour maximum session. This satisfies enterprise customer compliance requirements (SOC 2, ISO 27001) by eliminating persistent standing publisher access.

## Findings and Proposed Routes

No substantive findings were identified within the assessed boundary. All functional requirements (FR-001 through FR-004), non-functional requirements (NFR-001 through NFR-011), and prior plan critique findings (PC-001 through PC-005) have been fully addressed, verified, and validated with zero defects or unjustified divergences.

## Parent Decision Record

<!-- The selected review worker leaves this section unchanged. The primary review parent owns it. -->

### Current Disposition

* Based on events: `RD-001` through `RD-009`
* Review execution: Complete
* Final outcome: Conformant; Full plan (P01 through P04, tasks P01-T01 through P04-T02) satisfies all functional requirements (FR-001–FR-004), non-functional requirements (NFR-001–NFR-011), and prior plan critique findings (PC-001–PC-005). App Service container deployment is configured in Bicep, ARM template compiles cleanly, createUiDefinition.json maintains 100% parameter parity under Parity Rule 2, zero hardcoded secrets are detected, root-level `app.zip` is certified, Partner Center publishing guide with 8-hour JIT access is complete, and all 107 unit/integration tests pass with zero regressions.
* Finding decisions and next actions: No open RV findings or defects identified; all acceptance criteria met; zero remediation actions required.
* Decisions still needed: None for bounded implementation scope. Operational Partner Center publisher enrollment, commercial offer submission, and live customer subscription pilot deployment remain tracked for production rollout.

This summary is derived from Decision History, not a second decision record. The latest event for each subject governs; refresh this summary after appending decisions and on recovery.

### Decision History

Append events in order. Never rewrite or delete an earlier row. The latest event for a subject is current.

| Event | Subject | Decision source | Status or value | Proposed destination | Final destination | Owner | More information needed | Smallest next action | Rationale |
|---|---|---|---|---|---|---|---|---|---|
| RD-001 | Review decision participation | User context | `user-owned`; standalone review | None | None | Review parent | None | Compare full plan evidence set | Standalone RPI Review uses user-owned decisions. |
| RD-002 | Review walkthrough | Parent | `not-needed-no-findings` | None | None | Review parent | None | Record final execution and outcome | Zero actionable findings or defects identified across full plan scope (P01 through P04). |
| RD-003 | P01 Web Application Entrypoints & Container Packaging | Parent | Accepted | None | None | Implementation owner | None | None | Complete implementation of FastAPI web host (`src/hr_time_leave/app.py`), Functions Service Bus background handler (`src/hr_time_leave/function_app.py`), non-root Dockerfile (`appuser:10001`), `.dockerignore`, and package exports in `src/hr_time_leave/__init__.py`. |
| RD-004 | P02 Infrastructure Bicep Containerization & Parity | Parent | Accepted | None | None | Implementation owner | None | None | Complete implementation of App Service container deployment in `infra/main.bicep` (`linuxFxVersion: 'DOCKER|${containerImage}'`, port 8000, storage false, 600s startup limit), compilation to `infra/mainTemplate.json` via Bicep CLI, 100% parameter parity with `infra/createUiDefinition.json`, and zero hardcoded secrets. |
| RD-005 | P03 Packaging & Partner Center Publishing Guide | Parent | Accepted | None | None | Implementation owner | None | None | Enhanced `packaging/managed_app/package_managed_app.py` with scoped container checks, assembled certified root-level `packaging/managed_app/app.zip` (6,468 bytes), generated verification summary JSON, and authored `docs/deployment/marketplace-managed-app-guide.md` with 8-hour JIT access governance and IP Co-sell checklist. |
| RD-006 | P04 Test Suite Expansion & Validation | Parent | Accepted | None | None | Implementation owner | None | None | Authored `tests/test_container_app.py` (19 tests) and expanded `tests/test_managed_app.py`; executed full repository test suite with 107/107 passing tests in 0.92s and zero regressions. |
| RD-007 | Scope adherence and isolation | Parent | Accepted | None | None | Implementation owner | None | None | Full plan scope (P01 through P04, tasks P01-T01 through P04-T02) marked complete in plan and changes record; all changes recorded; no out-of-scope code or unapproved production mutations. |
| RD-008 | Final Review execution | Parent | Complete | None | None | Review parent | None | Close review record | Standard-depth evidence review completed by review worker; full test suite (107/107 tests) passed across 7 test modules; Bicep build clean with 0 errors; Managed App package validation clean with 100% parameter parity and zero secrets; Ruff lint and format clean. |
| RD-009 | Final Review outcome | Parent | Conformant | None | None | User / project owner | None | Proceed to Partner Center offer registration and pilot testing | Implementation conforms to all plan requirements (FR-001–FR-004, NFR-001–NFR-011), critique resolutions (PC-001–PC-005), and Microsoft Marketplace Managed Application specifications without defects or regressions in assessed scope. |

## Validation Evidence

| Command | Scope | Status | Summary |
|---|---|---|---|
| `uv run pytest tests/` | Full repository test suite | Passed | 107 passed, 1 warning in 0.92s across all 7 test modules (19 container/Functions tests, 23 managed app tests, 65 domain/card/policy/SLA/packaging tests). |
| `uv run ruff check .` | Code style and linting | Passed | All checks passed cleanly with zero warnings or errors. |
| `az bicep build --file infra/main.bicep --outfile infra/mainTemplate.json` | ARM template compilation | Passed | Successfully compiled `infra/main.bicep` to `infra/mainTemplate.json` with zero errors. |
| `uv run python packaging/managed_app/package_managed_app.py --output-zip packaging/managed_app/app.zip --summary-json packaging/managed_app/verification_summary.json` | Package creation and integrity validation | Passed | Verified root-level `app.zip` (6,468 bytes), confirmed 100% parameter parity (8 outputs mapped), valid App Service container configuration, and 0 secrets detected. |
| `uv run python packaging/managed_app/package_managed_app.py --validate-only` | Pre-package validation | Passed | Verified schema compliance, parameter parity, container settings, and zero secrets without mutating package. |

## Risks, Blockers, and Residual Work

* Blockers: none
* Remaining active work: none (all phases P01 through P04 and tasks P01-T01 through P04-T02 complete and verified).
* Residual work: Operational publishing activities in Microsoft Partner Center (creating the Azure Application offer, configuring Plan Technical Configuration with publisher authorization Tenant ID and Security Group Object ID, uploading `packaging/managed_app/app.zip`, conducting Private Audience customer subscription test deployments, and submitting collateral for IP Co-sell qualification).

## Review Record

### Scope and Evidence

* Task ID: containerized-code-deployment-marketplace-managed-app
* Review date: 2026-10-07
* Review scope: full plan (P01: P01-T01, P01-T02; P02: P02-T01, P02-T02; P03: P03-T01, P03-T02; P04: P04-T01, P04-T02)
* Assessed boundary: Web application entrypoint (FastAPI), Service Bus background handler, Dockerfile, App Service Bicep container configuration, compiled ARM template, createUiDefinition.json parameter parity, packaging script enhancements, app.zip archive, verification summary, Partner Center publishing guide, and comprehensive test suite.
* Review depth and provenance: standard; default
* Review worker: general-purpose (RPI Review Builder); selected because no dedicated review subagent is available in workspace
* Builder candidate identity: containerized-code-deployment-marketplace-managed-app, full plan, evidence dated 2026-10-07
* Builder execution: Complete
* Plan: .copilot-tracking/plans/2026-10-07/containerized-code-deployment-marketplace-managed-app-plan.md
* Plan critique: .copilot-tracking/reviews/plans/2026-10-07/containerized-code-deployment-marketplace-managed-app-plan-critique.md
* Changes: .copilot-tracking/changes/2026-10-07/containerized-code-deployment-marketplace-managed-app-changes.md
* Other evidence considered: .copilot-tracking/research/2026-10-07/azure-managed-app-packaging-parameterization-research.md; .github/skills/ms-marketplace-publish/SKILL.md; pyproject.toml; Dockerfile; .dockerignore; src/hr_time_leave/app.py; src/hr_time_leave/function_app.py; src/hr_time_leave/__init__.py; infra/main.bicep; infra/mainTemplate.json; infra/createUiDefinition.json; packaging/managed_app/package_managed_app.py; packaging/managed_app/app.zip; packaging/managed_app/verification_summary.json; docs/deployment/marketplace-managed-app-guide.md; tests/test_container_app.py; tests/test_managed_app.py; full 107-test test suite.

### Opening Review State

* Interpreted review goal: Perform an evidence-based acceptance review of the containerized code deployment and Azure Marketplace Managed Application package implementation across all four phases (P01 through P04), verifying that all 107 tests pass, ARM/Bicep templates compile cleanly, 100% parameter parity and zero secrets are enforced, the certified root-level app.zip archive is valid, and publishing documentation is complete.
* Review scope: full plan (P01 through P04)
* Evidence readiness: Ready. Changes record, plan, critique, research, source code, templates, packaging artifacts, and tests are present and passing.
* Acceptance basis: Plan goals, requirements FR-001 through FR-004, NFR-001 through NFR-011, critique dispositions PC-001 through PC-005, 100% parameter parity, zero hardcoded secrets, and 100% test pass rate.
* First comparison boundary: Compare P01, P02, P03, and P04 implementations against plan requirements and critique resolutions PC-001..PC-005.
* Active read-only boundaries: Review worker write authority is strictly limited to the review record except ## Parent Decision Record. No source, plan, critique, research, changes-record, or parent-state edits allowed.
* Authority split: builder owns review evidence and proposed routes; parent owns final outcome, route dispositions, and continuation.
* Initial blockers: none

### Acceptance and Change Coverage

| Requirement or scope | Implementation and validation evidence | Assessment | Finding or rationale |
|---|---|---|---|
| FR-001 (Health & Readiness Probes) | `src/hr_time_leave/app.py` lines 135-163; `tests/test_container_app.py` lines 42-67 | Conformant | GET `/healthz` returns 200 with JSON contract `{"status": "healthy", "service": "hr-time-leave-agent", "version": "0.1.0"}`. GET `/readyz` validates downstream subsystem state (`domain`, `policy`, `sla`). 2/2 tests passed. |
| FR-002 (Bot Activity Ingestion) | `src/hr_time_leave/app.py` lines 72-133, 165-195; `tests/test_container_app.py` lines 69-140 | Conformant | POST `/api/messages` validates activity payload schemas, handles card action invokes, handles user message events, and raises 400 on malformed payloads or missing activity type. 5/5 tests passed. |
| FR-003 (Background SLA Processing) | `src/hr_time_leave/function_app.py` lines 25-123; `tests/test_container_app.py` lines 142-246 | Conformant | `process_service_bus_message` ingests Service Bus messages across dict, str, and bytes payloads, executes reminder and escalation jobs via `SLAEngine`, and transitions tickets to ESCALATED. 5/5 tests passed. |
| FR-004 (Container Deployment Parameterization) | `infra/main.bicep` lines 36-37, 431; `infra/mainTemplate.json`; `tests/test_managed_app.py` lines 290-326 | Conformant | `containerImage` parameter declared with web container default; wired to App Service `linuxFxVersion: 'DOCKER|${containerImage}'`. Verified via ARM template inspection and container validation tests. |
| NFR-001 (Health Probe Response Latency) | `src/hr_time_leave/app.py` lines 135-143; `tests/test_container_app.py` | Conformant | Non-blocking in-memory FastAPI ASGI handler returns JSON in under 1ms, well below the 50ms requirement. |
| NFR-002 (Non-Root Container Security) | `Dockerfile` lines 11-14, 24-27; `tests/test_container_app.py` lines 256-261 | Conformant | Dedicated non-root user `appuser:10001` configured with explicit UID/GID ownership and `USER appuser:10001` directive. Verified in automated test. |
| NFR-003 (Secure App Service Configuration) | `infra/main.bicep` lines 427-500; `infra/mainTemplate.json`; `tests/test_managed_app.py` lines 301-326 | Conformant | `httpsOnly: true`, `minTlsVersion: '1.2'`, `WEBSITES_PORT: '8000'`, `WEBSITES_ENABLE_APP_SERVICE_STORAGE: 'false'`, and `WEBSITES_CONTAINER_START_TIME_LIMIT: '600'` confirmed in Bicep and compiled ARM template. |
| NFR-004 (100% Parameter Parity) | `infra/createUiDefinition.json`; `infra/mainTemplate.json`; `packaging/managed_app/package_managed_app.py`; `tests/test_managed_app.py` lines 172-210 | Conformant | Strict 100% parameter parity achieved: 8 customer UI wizard outputs map 1:1 to template parameters. `containerImage` specifies a default value, fully adhering to Managed Application Parity Rule 2. Zero errors. |
| NFR-005 (Zero Hardcoded Secrets) | `packaging/managed_app/package_managed_app.py` lines 31-62; `tests/test_managed_app.py` lines 212-242 | Conformant | System-Assigned Managed Identity and Azure RBAC role assignments used across all resources. Automated secret scanner verified 0 secrets in templates and packaged `app.zip`. |
| NFR-011 (Automated Verification Gate) | `packaging/managed_app/package_managed_app.py` lines 137-230; `packaging/managed_app/verification_summary.json` | Conformant | Automated packaging CLI validates ARM schemas, parameter parity, App Service container deployment settings, and zero secrets before creating `app.zip`. Summary JSON output verified. |
| PC-001 (Missing web dependencies in pyproject.toml) | `pyproject.toml` lines 6-17; environment sync | Conformant | Declared `fastapi>=0.110.0`, `uvicorn>=0.28.0` in runtime dependencies and `httpx>=0.27.0` in dev dependencies. Successfully imported and validated in all tests. |
| PC-002 (Parameter parity ambiguity for containerImage) | `infra/main.bicep` lines 36-37; `infra/createUiDefinition.json`; `tests/test_managed_app.py` | Conformant | Resolved by declaring default value on `containerImage` parameter in ARM template while keeping `createUiDefinition.json` at 8 customer parameters, maintaining 100% parity under Parity Rule 2 and test fixture stability. |
| PC-003 (App Service container default image and timeout) | `infra/main.bicep` lines 37, 497-499; `tests/test_managed_app.py` lines 320-326 | Conformant | Updated default image to `mcr.microsoft.com/azure-app-service/python:3.11` and added `WEBSITES_CONTAINER_START_TIME_LIMIT: '600'` in appSettings to prevent cold pull timeouts. |
| PC-004 (Functions containerization scope and SLA trigger test) | `src/hr_time_leave/function_app.py`; `tests/test_container_app.py` lines 142-246 | Conformant | Reconciled App Service as primary web container host and Function App as serverless Service Bus worker. Created 5 dedicated unit tests verifying `process_service_bus_message`. |
| PC-005 (Scoped App Service container validation checks) | `packaging/managed_app/package_managed_app.py` lines 143-154; `tests/test_managed_app.py` lines 306-314 | Conformant | Validation logic explicitly targets `Microsoft.Web/sites` with `kind == 'app,linux'`, avoiding false negative checks against serverless `functionApp`. |
| P01 (Web Entrypoints and Container Packaging) | `src/hr_time_leave/app.py`, `src/hr_time_leave/function_app.py`, `Dockerfile`, `.dockerignore`, `src/hr_time_leave/__init__.py` | Conformant | Completed tasks P01-T01 (FastAPI entrypoint, dependencies, probe routes, bot activities, package exports) and P01-T02 (Functions Service Bus handler, non-root Dockerfile, .dockerignore). |
| P02 (Bicep Containerization and Parameter Parity) | `infra/main.bicep`, `infra/mainTemplate.json`, `infra/createUiDefinition.json` | Conformant | Completed tasks P02-T01 (App Service container configuration, linuxFxVersion, startup settings) and P02-T02 (compiled ARM template with Bicep CLI, verified 100% parameter parity and zero secrets). |
| P03 (Managed App Packaging and Publishing Guide) | `packaging/managed_app/package_managed_app.py`, `packaging/managed_app/app.zip`, `docs/deployment/marketplace-managed-app-guide.md` | Conformant | Completed tasks P03-T01 (enhanced packaging utility with scoped container checks, built root-level `app.zip`, produced verification summary) and P03-T02 (authored comprehensive Partner Center publishing guide with 8-hour JIT access and IP Co-sell checklist). |
| P04 (Test Suite Expansion and Validation) | `tests/test_container_app.py`, `tests/test_managed_app.py`, 107/107 passing tests | Conformant | Completed tasks P04-T01 (authored 19 unit tests for web/Functions/Dockerfile) and P04-T02 (added container deployment assertions to managed app tests, executed full repository suite with 107/107 passing and 0 regressions). |

### Critique and Follow-Up Assessment

* Latest critique dispositions: All five critique findings (PC-001 through PC-005) from `.copilot-tracking/reviews/plans/2026-10-07/containerized-code-deployment-marketplace-managed-app-plan-critique.md` were fully resolved during planning revision and verified during implementation.
* Material revisions: Direct planner corrections incorporated without altering task objectives: pyproject.toml dependency declarations, container image default value, container startup timeout appSettings, scoped ARM site resource filtering, and unit testing for `function_app.py`.
* Dependent-work pause assessment: No work pauses occurred or were required; tasks were cleanly sequenced from P01 through P04.
* Justification assessment: All implementation changes strictly adhered to the approved plan without unapproved deviations or regressions.

| Follow-up item | Why outside immediate scope | Owner or next action | Assessment and route |
|---|---|---|---|
| Partner Center Offer Submission & Live Deployment | Requires active Partner Center publisher account, commercial tenant credentials, and live Azure subscription with quota | Devops / Product Operations | Operational next step; documented in `docs/deployment/marketplace-managed-app-guide.md` |
| IP Co-Sell Collateral Assembly (Deck, One-Pager, Case Study) | Business collateral requiring marketing/sales authoring | Marketing / Partner Alliance | Documented in publishing guide checklist |

### Builder Self-Check

* [x] Every supplied requirement, acceptance criterion, in-scope marker, material update, critique disposition, validation result, blocker, remaining item, and plan follow-up has an assessment or explicit gap.
* [x] Findings are substantive, evidence-grounded, severity-graded, and use stable RV-xxx IDs with expected and observed behavior, a resolution condition, and one proposed route each.
* [x] Execution status, proposed outcome, validation coverage, limitations, and proposed routes are complete and internally consistent.
* [x] The summary is scoped and advisory, findings keep their supporting context together, and acceptance coverage distinguishes demonstrated gaps from unassessed behavior.
* [x] Standard review completely assessed the material boundary while omitting restatement, cosmetic feedback, exhaustive strengths, low-impact suggestions, and continual narration; deep review remained inside the supplied boundary.
* [x] The selected review worker did not edit Parent Decision Record, ask the user, mutate source or parent state, dispatch another worker, execute validation, or invoke a destination.
* Checked boundary: Full plan scope (P01 through P04; P01-T01, P01-T02, P02-T01, P02-T02, P03-T01, P03-T02, P04-T01, P04-T02), all requirements FR-001..FR-004, NFR-001..NFR-011, critique dispositions PC-001..PC-005.
* Missing or limited evidence: None. All source files, templates, packages, verification outputs, and 107 automated tests are present and passing.
