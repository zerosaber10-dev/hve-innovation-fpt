<!-- markdownlint-disable-file -->
# RPI Plan Critique: containerized-code-deployment-marketplace-managed-app

## Metadata

* Task ID: containerized-code-deployment-marketplace-managed-app
* Critique date: 2026-10-07
* Plan: .copilot-tracking/plans/2026-10-07/containerized-code-deployment-marketplace-managed-app-plan.md
* Critique execution status: Complete
* Critique depth: standard
* Depth provenance: default
* Invocation consumed: yes

## Inputs and Criterion Boundary

* Task context and caller requirements: Assess implementation plan for containerized code deployment and Marketplace Managed Application package finalization, checking task dependencies, parameter parity mechanics, App Service Docker configuration, zero hardcoded secrets, packaging automation, test coverage, and Partner Center documentation.
* Research and evidence considered:
  - .copilot-tracking/research/2026-10-07/azure-managed-app-packaging-parameterization-research.md
  - infra/main.bicep
  - infra/createUiDefinition.json
  - infra/mainTemplate.json
  - packaging/managed_app/package_managed_app.py
  - tests/test_managed_app.py
  - pyproject.toml
  - .github/skills/ms-marketplace-publish/SKILL.md
* Decisions, dependencies, task Goals, and task Requirements considered: Confirmed decisions D1-D5, phase goals P01-P04, task goals and requirements P01-T01 through P04-T02, functional requirements FR-001 through FR-004, non-functional requirements NFR-001 through NFR-011.
* Assessment boundary: Assesses feasibility, internal consistency, and credibility against supplied repository evidence and Microsoft Learn / Partner Center standards. Does not execute live cloud deployments or modify source code.

## Coverage Assessment

| Requirement, research, phase, or task ID | Coverage | Evidence or concern |
|---|---|---|
| FR-001 (Healthz & readyz endpoints) | Covered | P01-T01 specifies contract; P04-T01 tests endpoints |
| FR-002 (Bot Framework activity endpoint) | Covered | P01-T01 implements POST /api/messages dispatching to domain and manager cards |
| FR-003 (Background SLA queue ingestion) | Partial | P01-T02 creates function_app.py, but P04 lacks test coverage and P02 lacks function deployment configuration |
| FR-004 (Container deployment parameterization) | Covered | P02-T01 adds containerImage parameter in Bicep; P04-T02 verifies ARM template |
| NFR-001 (Health endpoint performance) | Partial | FastAPI framework specified, but web dependencies missing from pyproject.toml |
| NFR-002 (Non-root container user) | Covered | P01-T02 specifies appuser:10001; P04-T01 verifies Dockerfile |
| NFR-003 (App Service container configuration) | Partial | linuxFxVersion and WEBSITES_ENABLE_APP_SERVICE_STORAGE configured, but startup timeout limit omitted from P02-T01 |
| NFR-004 (100% parameter parity) | Partial | Ambiguity on whether containerImage is added to createUiDefinition.json risks test failure in test_managed_app.py |
| NFR-005 (Zero hardcoded secrets) | Covered | Entra ID Managed Identity and RBAC maintained; secret scanning enforced |
| NFR-011 (Automated verification gate) | Partial | Packaging checks must specifically target appService resource rather than all Microsoft.Web/sites |
| Phase 1 (Entrypoints and Packaging) | Partial | Blocked by missing fastapi/uvicorn dependencies in pyproject.toml |
| Phase 2 (Bicep Containerization & Parity) | Partial | containerImage default value mismatch and omitted startup timeout setting |
| Phase 3 (Packaging & Partner Center Guide) | Covered | Root app.zip structure, validation CLI, and publishing guide well-aligned |
| Phase 4 (Test Expansion & Validation) | Partial | Missing test coverage for function_app.py and rigid parity assertions need alignment |

## Verdict

* Verdict: Revise
* Rationale: The plan provides a strong architectural approach for bypassing Managed Resource Group Deny Assignments via containerization and adheres closely to Microsoft Marketplace packaging standards. However, revision is required before implementation due to five concrete credibility gaps: (1) missing FastAPI/Uvicorn/HTTPX dependencies in pyproject.toml which immediately breaks Phase 1 and Phase 4; (2) parameter parity decision ambiguity that risks breaking existing test fixtures in test_managed_app.py; (3) an inappropriate default container image (Functions base image for web app) and omission of the WEBSITES_CONTAINER_START_TIME_LIMIT setting in P02-T01; (4) architectural scope ambiguity regarding Azure Functions containerization and missing SLA trigger tests; and (5) multi-resource filtering in template container validation.

## Findings

<!-- rpi:critique id=PC-001 -->
### PC-001 [High]: Missing web framework and test dependencies in pyproject.toml

* Related IDs: P01-T01, P01-T02, P04-T01, NFR-001, Scope (In Scope)
* Evidence: pyproject.toml lines 6-14 declares only jsonschema, pytest, and ruff; plan lines 97-124 and 378-398 require FastAPI, Uvicorn, and HTTPX/Starlette TestClient.
* Concern: The plan instructs creating a FastAPI ASGI application in src/hr_time_leave/app.py and running pytest with HTTPX/Starlette in tests/test_container_app.py, but pyproject.toml does not declare fastapi, uvicorn, or httpx, and fastapi is not installed in the current environment. Running the test suite or importing app.py will immediately fail with ModuleNotFoundError.
* Impact: Implementation and test execution will fail upon first step of Phase 1 and Phase 4.
* Smallest useful change: Add a requirement in P01-T01 (and update Scope) to declare `fastapi`, `uvicorn`, and `httpx` (or `starlette`) in pyproject.toml dependencies / dev dependencies and synchronize the environment.
* Action owner: planning parent
* Exact resolving evidence: pyproject.toml contains required dependencies and `uv run python -c "import fastapi, uvicorn, httpx"` succeeds.
* Decision route: direct planner correction

<!-- rpi:critique id=PC-002 -->
### PC-002 [Medium]: Ambiguity and test breakage risk in parameter parity for containerImage

* Related IDs: P02-T01, P02-T02, P04-T02, NFR-004, NFR-011
* Evidence: plan lines 224-236 (P02-T02 details); tests/test_managed_app.py lines 76-90 and 152-170; infra/createUiDefinition.json lines 137-147.
* Concern: P02-T02 leaves whether containerImage is added to createUiDefinition.json as an open option ("Since containerImage has a defaultValue in main.bicep, it does not strictly break Parity Rule 2... but exposing an optional image textbox or drop-down... enables custom overrides"). However, tests/test_managed_app.py contains rigid assertions in `TestCreateUiDefinitionSchema` and `TestParameterParity` that assert exact set equality with an 8-output fixture. If an implementer exposes containerImage in the UI, test_managed_app.py will fail unless updated. If they omit it, Parity Rule 2 passes because containerImage has a defaultValue.
* Impact: Implementer confusion and test regression during Phase 4 validation.
* Smallest useful change: Make a definitive decision in P02-T02: either keep containerImage solely in main.bicep/mainTemplate.json with a defaultValue (keeping createUiDefinition.json at 8 outputs and leaving test_managed_app.py untouched), OR explicitly require adding containerImage TextBox to createUiDefinition.json in P02-T02 AND updating expected_elements and expected_outputs in test_managed_app.py in P04-T02.
* Action owner: planning parent
* Exact resolving evidence: package_managed_app.py --validate-only passes and tests/test_managed_app.py passes with consistent parameter sets.
* Decision route: direct planner correction

<!-- rpi:critique id=PC-003 -->
### PC-003 [Medium]: App Service container default image mismatch and unwired startup timeout

* Related IDs: P02-T01, NFR-003, Risks (App Service container startup timeout)
* Evidence: plan line 203, lines 504-506; infra/main.bicep lines 427-490.
* Concern: In P02-T01, the default value for containerImage is set to `mcr.microsoft.com/azure-functions/python:4-python3.11`. This is an Azure Functions base image that does not run Uvicorn or expose port 8000 for a FastAPI web service. Furthermore, the risk table identifies slow image pull startup failures and prescribes `WEBSITES_CONTAINER_START_TIME_LIMIT=600`, but P02-T01 Requirements fails to include this setting in the required App Service appSettings list.
* Impact: Provisioning with the default image starts an incompatible Functions host instead of the web application, and large container pulls in customer tenants risk timeout without the startup limit setting.
* Smallest useful change: Update P02-T01 to specify an application-appropriate container image reference as the default (or a public web container placeholder) and add `WEBSITES_CONTAINER_START_TIME_LIMIT: '600'` to the required App Service appSettings in P02-T01.
* Action owner: planning parent
* Exact resolving evidence: infra/main.bicep contains `WEBSITES_CONTAINER_START_TIME_LIMIT: '600'` in appService appSettings and an appropriate default container image string.
* Decision route: direct planner correction

<!-- rpi:critique id=PC-004 -->
### PC-004 [Medium]: Scope discrepancy regarding Azure Functions containerization and missing SLA trigger test

* Related IDs: P01-T02, P02-T01, P04-T01, FR-003, FR-004
* Evidence: plan line 12, lines 126-141, 196-209, 378-398; infra/main.bicep lines 497-550.
* Concern: The plan's Executive Summary states that containerized code deployment is implemented for both the web runtime AND the Azure Functions SLA processor. However, P01-T02 authors a Dockerfile whose entrypoint runs only `uvicorn hr_time_leave.app:app`, and P02-T01 only configures `appService` with Docker (`linuxFxVersion: 'DOCKER|...'`), leaving `functionApp` in main.bicep on `PYTHON|3.11` without code deployment. Additionally, P04-T01 provides unit tests for app.py and Dockerfile, but completely omits testing for `function_app.py` (`process_service_bus_message`).
* Impact: Unclear deployment architecture for the Functions background processor under MRG Deny Assignments, and missing test coverage for the Service Bus SLA consumer.
* Smallest useful change: Reconcile the Executive Summary and P02-T01 to state that App Service web containerization is the primary deployment path (or clarify Function App deployment), and add a test requirement in P04-T01 for `src/hr_time_leave/function_app.py`.
* Action owner: planning parent
* Exact resolving evidence: Reconciled scope descriptions across Executive Summary and P02-T01, plus unit tests in tests/test_container_app.py verifying `process_service_bus_message`.
* Decision route: direct planner correction

<!-- rpi:critique id=PC-005 -->
### PC-005 [Low]: Multi-resource specificity for Docker configuration checks in packaging and tests

* Related IDs: P03-T01, P04-T02, NFR-005, NFR-011
* Evidence: plan lines 291-296, 406-411; infra/mainTemplate.json resources array.
* Concern: Both package_managed_app.py enhancements (P03-T01) and test_managed_app.py (P04-T02) require verifying that mainTemplate.json contains `linuxFxVersion` configured for `DOCKER|`. Since mainTemplate.json defines multiple `Microsoft.Web/sites` resources (`appService` and `functionApp`), an unqualified scan across all site resources could observe `PYTHON|3.11` on functionApp and generate false negatives.
* Impact: Fragile package validation logic or test failures when verifying compiled ARM templates.
* Smallest useful change: Clarify in P03-T01 and P04-T02 that `linuxFxVersion` and `WEBSITES_PORT` validation must target the `appService` resource specifically (filtering by name or kind `app,linux`).
* Action owner: planning parent
* Exact resolving evidence: Validation functions in package_managed_app.py and test assertions in test_managed_app.py inspect the appService resource specifically.
* Decision route: direct planner correction

## Strengths and Residual Risk

* Grounded Architectural Foundation: The plan correctly identifies the Managed Resource Group Deny Assignment constraint (`Microsoft.Resources/denyAssignments`) and accurately selects container image deployment as the optimal bypass.
* Zero Hardcoded Secrets Enforcement: The plan consistently preserves Entra ID System-Assigned Managed Identity and Azure RBAC assignments, backed by automated regex secret scanning across templates and archives.
* Standardized Marketplace Packaging: The plan adheres strictly to Microsoft Marketplace specifications for root-level `app.zip` archive structure, schema validation, and Partner Center publishing documentation.
* Accepted Residual Risk: Customer tenant capacity quotas for Azure OpenAI models remain a known external factor, properly mitigated through the parameterized `existingOpenAiEndpoint` option.

## Questions or Blocking Evidence Gaps

* None. The codebase, Bicep templates, packaging scripts, test suites, and Microsoft Marketplace skills provide complete evidence to resolve all findings without external research.

## Limitations

* Live deployment to an Azure subscription and submission to Partner Center are non-goals for this task; assessment is grounded in static template analysis, packaging validation, and automated unit test execution.

## Recommended Next Action

* Highest-impact finding: PC-001 (Missing web framework and test dependencies in pyproject.toml)
* Action owner: planning parent
* Smallest next action: Update the plan with planner corrections addressing PC-001 through PC-005 (adding pyproject.toml dependency management to P01-T01, deciding parity strategy in P02-T02, fixing default image and startup timeout in P02-T01, reconciling functionApp scope and adding test in P04-T01, and scoping template checks in P03-T01/P04-T02).
* User response required: no (all findings are direct planner corrections based on existing codebase evidence).

---

### Artifact Reference Table

| [.copilot-tracking/plans/2026-10-07/containerized-code-deployment-marketplace-managed-app-plan.md](.copilot-tracking/plans/2026-10-07/containerized-code-deployment-marketplace-managed-app-plan.md) | Implementation plan under critique |
| [.copilot-tracking/research/2026-10-07/azure-managed-app-packaging-parameterization-research.md](.copilot-tracking/research/2026-10-07/azure-managed-app-packaging-parameterization-research.md) | Sourced research on packaging, Deny Assignments, and parameterization |
| [infra/main.bicep](infra/main.bicep) | Azure infrastructure definition |
| [infra/createUiDefinition.json](infra/createUiDefinition.json) | Azure Portal wizard UI definition |
| [infra/mainTemplate.json](infra/mainTemplate.json) | Compiled ARM deployment template |
| [packaging/managed_app/package_managed_app.py](packaging/managed_app/package_managed_app.py) | Packaging and validation utility |
| [tests/test_managed_app.py](tests/test_managed_app.py) | Managed application test suite |
| [pyproject.toml](pyproject.toml) | Python project dependencies configuration |
| [.github/skills/ms-marketplace-publish/SKILL.md](.github/skills/ms-marketplace-publish/SKILL.md) | Microsoft Marketplace publishing skill reference |

## Next Steps

Active-parent action: Planning parent incorporates direct planner corrections for findings PC-001 through PC-005 into `.copilot-tracking/plans/2026-10-07/containerized-code-deployment-marketplace-managed-app-plan.md` and finalizes the plan for implementation handoff. No user response is required.
