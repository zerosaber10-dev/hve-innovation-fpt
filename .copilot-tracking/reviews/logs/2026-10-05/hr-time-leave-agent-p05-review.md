<!-- markdownlint-disable-file -->
# Review: HR Time and Leave Agent Implementation (Phase P05 - Azure Managed Application & Marketplace Readiness)

## Executive Summary

* Assessment: Conformant for bounded Phase P05 / Task P05-T01. The Azure Managed Application packaging artifacts (`infra/createUiDefinition.json`, `infra/mainTemplate.json`, `packaging/managed_app/package_managed_app.py`, and `packaging/managed_app/app.zip`), Teams app packaging artifacts (`packaging/teams/manifest.json`, icons, and `hr-time-leave-teams.zip`), deployment documentation (`docs/deployment/azure-managed-application.md`), and commercial marketplace baseline decisions (D-01 and D-02 in `.copilot-tracking/details/marketplace-plan.md`) completely satisfy the requirements of task P05-T01.
* Why this matters: Distributing the HR Time and Leave Copilot as an Azure Managed Application deployed into a customer-owned Managed Resource Group (MRG) guarantees customer data sovereignty and strict data residency for sensitive employee leave, medical certification, and compensation records. Operating under publisher Just-In-Time (JIT) access governance ensures zero standing vendor access, while parameter parity and schema compliance provide a reliable, automated deployment experience via the Microsoft Commercial Marketplace.
* Builder execution: Complete
* Proposed review execution: Complete
* Proposed outcome: Conformant
* Validation coverage: 84/84 unit tests passed across 6 test modules (`test_domain.py`, `test_policy.py`, `test_manager_cards.py`, `test_sla.py`, `test_packaging.py`, and `test_managed_app.py`); clean Azure Bicep template compilation (`az bicep build` 0 errors, 0 warnings); clean Bicep parameter compilation (`az bicep build-params` 0 errors); validated Managed Application packaging script with 100% parameter parity and zero hardcoded secrets; validated Teams packaging script with manifest schema v1.16 compliance; and clean Ruff linter and formatter passes across all 18 files.
* Confidence and limitations: High confidence in local template schema compliance, ARM parameter parity, secret detection, archive integrity, and automated test coverage. Limitations: live Partner Center commercial marketplace offer publication, live Azure subscription sandbox deployment, and customer tenant onboarding remain operational production gates outside the bounded implementation boundary.

The assessment above is the builder's proposal. Parent Decision Record contains the current final decision and next actions, or states that decisions are pending.

## What You May Not Know

* **Managed Resource Group (MRG) Deny Assignment Mechanics:** Deploying via Azure Managed Application places all backend resources (App Service, Azure AI Search, Azure Functions, Cosmos DB, Service Bus, Key Vault, and Storage) inside a customer-owned subscription but protected by an automated Azure Deny Assignment. This prevents customer administrators from accidentally altering or deleting dependencies while maintaining customer ownership over cloud billing and data residency.
* **Zero Standing Access & JIT Governance:** Publisher operations staff have zero permanent access to customer data or infrastructure. Any support or maintenance intervention requires a time-bound (max 4–8 hours) Just-In-Time (JIT) elevation request specifying role and justification, which customer administrators must explicitly approve in the Azure Portal and can revoke at any time.
* **Customer Data Sovereignty & Secondary Index Exclusions:** Sensitive employee medical certifications and compensation adjustment records never leave the customer's cloud boundary. In addition, the Cosmos DB `hr-ticket-store` configuration excludes medical notes and compensation amounts from secondary indexing, ensuring privacy-in-depth even within customer database analytics.
* **100% Parameter Parity Enforcement:** Every single output declared in `infra/createUiDefinition.json` maps 1:1 to a defined parameter in `infra/mainTemplate.json` (`location`, `environmentName`, `appNamePrefix`, `entraTenantId`, `botAppId`, `appServicePlanSku`, `searchSku`, and `existingOpenAiEndpoint`), preventing runtime deployment failures in the Azure Portal wizard.
* **Pure Managed Identity Posture (Zero Secrets):** Inter-service communications between App Service, Functions, Key Vault, Service Bus, Azure AI Search, and Cosmos DB rely entirely on Entra ID System-Assigned Managed Identity role assignments. All resources explicitly enforce `disableLocalAuth: true`, eliminating API keys, shared access signatures, and database connection strings from templates and configuration.
* **Marketplace Packaging vs. Publication Gating:** Generating a structurally valid `app.zip` archive and passing packaging tests fulfills technical packaging readiness for Phase P05, but does not equate to commercial marketplace publication or Azure IP Co-sell status. Official Microsoft Partner Center publisher enrollment, legal agreements, preview tenant testing, and commercial certification remain separate production gates.

## Findings and Proposed Routes

No substantive findings or divergences were identified within the assessed Phase P05 boundary.

All packaging and deployment artifacts (`infra/createUiDefinition.json`, `infra/mainTemplate.json`, `packaging/managed_app/package_managed_app.py`, `packaging/managed_app/app.zip`, `packaging/teams/manifest.json`, `packaging/teams/package.py`, and `docs/deployment/azure-managed-application.md`) strictly adhere to the implementation plan, PRD requirements, ADR C5 constraints, and Decision D-01/D-02 closures. The 84-test test suite passes cleanly with zero errors.

## Parent Decision Record

<!-- The selected review worker leaves this section unchanged. The primary review parent owns it. -->

### Current Disposition

* Based on events: `RD-001` through `RD-007`
* Review execution: Complete
* Final outcome: Conformant; Phase P05 (Azure Managed Application packaging and marketplace readiness, Task P05-T01) satisfies all non-functional, security, and packaging requirements (PRD NFR-003, NFR-005, NFR-011, NFR-012, NFR-014, NFR-015, CON-004, ADR C5, Decision D-01, Decision D-02), ARM/Bicep templates compile cleanly, createUiDefinition.json adheres to schema 0.1.2-preview, parameter parity is 100%, zero hardcoded secrets exist, all 84 unit tests pass across 6 modules, and zero open defects exist within the declared scope
* Finding decisions and next actions: No open RV findings or defects identified; all acceptance criteria met; no remediation actions required for P05
* Decisions still needed: None for bounded P05 implementation. Production gates for live Microsoft Partner Center publisher registration, commercial marketplace offer certification, customer sandbox subscription deployment, tenant HR policy confirmation, and audit tamper-evidence selection remain tracked for subsequent phases.

This summary is derived from Decision History, not a second decision record. The latest event for each subject governs; refresh this summary after appending decisions and on recovery.

### Decision History

Append events in order. Never rewrite or delete an earlier row. The latest event for a subject is current.

| Event | Subject | Decision source | Status or value | Proposed destination | Final destination | Owner | More information needed | Smallest next action | Rationale |
|---|---|---|---|---|---|---|---|---|---|
| RD-001 | Review decision participation | User context | `user-owned`; standalone review | None | None | Review parent | None | Compare P05 evidence set | Standalone RPI Review uses user-owned decisions. |
| RD-002 | Review walkthrough | Parent | `not-needed-no-findings` | None | None | Review parent | None | Record final execution and outcome | Zero actionable findings or defects identified in assessed Phase P05 boundary. |
| RD-003 | P05-T01 Managed Application packaging & parameter parity | Parent | Accepted | None | None | Implementation owner | None | None | Complete Azure Managed Application packaging artifacts (`infra/createUiDefinition.json`, `infra/mainTemplate.json`, `packaging/managed_app/package_managed_app.py`, `packaging/managed_app/app.zip`), schema 0.1.2-preview compliance, 100% parameter parity across all 8 UI outputs, zero hardcoded secrets verified, and comprehensive deployment guide (`docs/deployment/azure-managed-application.md`), verified by 19 unit tests in `tests/test_managed_app.py` and 84/84 tests overall. |
| RD-004 | Decision D-01 & D-02 closure and commercial model | Parent | Accepted | None | None | Product Owner & Platform Architecture | None | None | Decision D-01 (Azure Managed Application deployed in customer subscription MRG with customer-approved JIT access and customer data sovereignty) and Decision D-02 (Monthly base fee + per-seat subscription + BYOL enterprise tier with customer-covered Azure consumption) formally closed in `.copilot-tracking/details/marketplace-plan.md` with complete architecture and trade-off analysis. |
| RD-005 | Scope adherence and isolation | Parent | Accepted | None | None | Implementation owner | None | None | Phase P05 and task P05-T01 marked complete in plan; P01-T01, P02/P02-T01, P03/P03-T01, and P04/P04-T01 remain complete; container phase P01 remains unchecked as container marker; all changes recorded in changes record; no out-of-scope code or unapproved production mutations. |
| RD-006 | Final Review execution | Parent | Complete | None | None | Review parent | None | Close review record | Standard-depth evidence review completed by review worker; full test suite (84/84 tests) passed across 6 test modules in 0.32s; Bicep build and build-params clean with 0 errors; Managed App package validation clean with 100% parameter parity; Teams package validation clean; Ruff lint and format clean across 18 files. |
| RD-007 | Final Review outcome | Parent | Conformant | None | None | User / project owner | None | Proceed to Partner Center onboarding and pilot readiness | Implementation conforms to PRD and plan requirements, ADR C5 constraints, and Marketplace Decision D-01/D-02 closures without defects or regressions in assessed scope. |

## Validation Evidence

| Command | Scope | Status | Summary |
|---|---|---|---|
| `.venv\Scripts\python.exe -m pytest -v` | Full test suite (`tests/`) | Passed | 84/84 tests passed across 6 test modules (`test_domain.py`: 9, `test_policy.py`: 10, `test_manager_cards.py`: 13, `test_sla.py`: 16, `test_packaging.py`: 17, `test_managed_app.py`: 19) in 0.32s with zero failures. |
| `az bicep build --file infra/main.bicep` | Azure Infrastructure IaC | Passed | Compiled Bicep to ARM successfully with 0 errors and 0 warnings. |
| `az bicep build-params --file infra/main.bicepparam` | Bicep parameter validation | Passed | Validated Bicep parameters against main template with 0 errors. |
| `.venv\Scripts\python.exe packaging/managed_app/package_managed_app.py --validate-only` | Managed App packaging & parity | Passed | Verified schema compliance (`CreateUIDefinition.MultiVm.json#`), 100% parameter parity across all 8 outputs, and zero hardcoded secrets. |
| `.venv\Scripts\python.exe packaging/teams/package.py --validate-only` | Teams application packaging | Passed | Verified Teams manifest schema v1.16 compliance, icon specifications (192x192 color, 32x32 outline), and zero secrets. |
| `.venv\Scripts\python.exe -m ruff check src tests packaging` | Code quality & linting | Passed | Clean pass across 18 Python source files with 0 lint errors. |
| `.venv\Scripts\python.exe -m ruff format --check src tests packaging` | Code style & formatting | Passed | Clean pass across 18 Python source files with zero formatting discrepancies. |

## Risks, Blockers, and Residual Work

* Blockers: None for the bounded scope of Phase P05 (Task P05-T01). All deployment templates, UI definitions, packaging scripts, test suites, and documentation are complete and verified.
* Production Gates: Commercial marketplace publication remains gated by authoritative Partner Center publisher enrollment, execution of the Microsoft Publisher Agreement, preview deployment in a customer sandbox subscription, and final Microsoft technical certification. In addition, production tenant activation remains gated by human HR policy sign-off on SLA escalation thresholds (Decision D1), tenant-specific policy documents, and formal selection of durable audit tamper-evidence mechanisms.
* Remaining Active Work: Container phase marker `P01` remains unchecked in `.copilot-tracking/plans/implementation-plan.md` because the entire plan was executed incrementally rather than in a single monolithic invocation.
* Residual Work: Microsoft Partner Center offer creation and submission of `packaging/managed_app/app.zip`, preview tenant validation, and customer pilot rollout as outlined in `docs/deployment/azure-managed-application.md` and `.copilot-tracking/details/marketplace-plan.md`.

## Review Record

### Scope and Evidence

* Task ID: hr-time-leave-agent-implementation
* Review date: 2026-10-05
* Review scope: Phase P05 (Azure Managed Application packaging and marketplace readiness, Task P05-T01)
* Assessed boundary: Azure Managed Application packaging artifacts (`infra/createUiDefinition.json`, `infra/mainTemplate.json`, `packaging/managed_app/package_managed_app.py`, `packaging/managed_app/app.zip`), marketplace planning baseline and Decision D-01/D-02 closure (`.copilot-tracking/details/marketplace-plan.md`), deployment and governance guide (`docs/deployment/azure-managed-application.md`), Teams app packaging artifacts (`packaging/teams/manifest.json`, `packaging/teams/package.py`, `packaging/teams/hr-time-leave-teams.zip`), and comprehensive test suite (`tests/test_managed_app.py` with 19 tests, 84 tests repository-wide).
* Review depth and provenance: standard; default for RPI Review
* Review worker: general-purpose (RPI Review Builder); selected because no dedicated review subagent is available in workspace
* Builder candidate identity: hr-time-leave-agent-implementation, P05, evidence dated 2026-10-05
* Builder execution: Complete
* Plan: .copilot-tracking/plans/implementation-plan.md
* Plan critique: none
* Changes: .copilot-tracking/changes/2026-09-29/hr-time-leave-agent-implementation-changes.md
* Other evidence considered: .copilot-tracking/details/marketplace-plan.md (Decision D-01 and D-02 closure); .copilot-tracking/prd-sessions/requirements.md (NFR-003, NFR-005, NFR-011, NFR-012, NFR-014, NFR-015, CON-004); docs/planning/adrs/0001-choose-agentic-hr-architecture.md (C5); infra/createUiDefinition.json; infra/mainTemplate.json; infra/main.bicep; infra/main.bicepparam; packaging/managed_app/package_managed_app.py; packaging/managed_app/app.zip; docs/deployment/azure-managed-application.md; tests/test_managed_app.py; tests/test_packaging.py; full 84-test test suite.

### Opening Review State

* Interpreted review goal: Review the Azure Managed Application packaging and marketplace readiness implementation evidence in .copilot-tracking/changes/2026-09-29/hr-time-leave-agent-implementation-changes.md against the implementation plan (.copilot-tracking/plans/implementation-plan.md) and Decision D-01 closure in .copilot-tracking/details/marketplace-plan.md. Verify that all 84 tests pass, Bicep and createUiDefinition.json adhere to schemas and parameter parity, zero hardcoded secrets exist, and record the canonical review log under .copilot-tracking/reviews/logs/2026-10-05/hr-time-leave-agent-p05-review.md.
* Review scope: Phase P05 (Task P05-T01: Azure Managed Application packaging and marketplace readiness)
* Evidence readiness: Changes record, implementation plan, marketplace plan with closed decisions D-01 and D-02, ARM template `infra/mainTemplate.json`, portal UI definition `infra/createUiDefinition.json`, packaging script `packaging/managed_app/package_managed_app.py`, archive `packaging/managed_app/app.zip`, deployment guide `docs/deployment/azure-managed-application.md`, and 19 unit tests in `tests/test_managed_app.py` (84 total tests) are ready and verified.
* Acceptance basis: Decision D-01 closure in `marketplace-plan.md` (Azure Managed Application with customer MRG and JIT governance); Decision D-02 (Monthly subscription + BYOL); PRD NFR-003, NFR-005, NFR-011, NFR-012, NFR-014, NFR-015; Plan Phase P05 Goals, Requirements, Details; createUiDefinition.json schema 0.1.2-preview compliance; 100% parameter parity with mainTemplate.json; zero hardcoded secrets; 84 passing unit tests.
* First comparison boundary: Verify Decision D-01 closure and architecture rationale in `marketplace-plan.md`; verify `infra/createUiDefinition.json` schema and element constraints; verify parameter parity between UI outputs and `mainTemplate.json` parameters; verify zero hardcoded secrets via scanner; verify `packaging/managed_app/package_managed_app.py` utility and `packaging/managed_app/app.zip` archive integrity; verify `docs/deployment/azure-managed-application.md` documentation; verify unit test suite (84 tests passing); verify scope isolation and plan marker consistency.
* Active read-only boundaries: Review worker write authority is limited to the review record except ## Parent Decision Record; no source, plan, critique, research, changes, or state files may be edited.
* Authority split: builder owns review evidence and proposed routes; parent owns final outcome, route dispositions, and continuation.
* Initial blockers: none

### Acceptance and Change Coverage

| Requirement or scope | Implementation and validation evidence | Assessment | Finding or rationale |
|---|---|---|---|
| **Decision D-01** (Offer Type: Azure Managed Application) | `.copilot-tracking/details/marketplace-plan.md` lines 44, 70–92; `docs/deployment/azure-managed-application.md` Sections 1–3. Managed Application deployed into customer subscription MRG with Deny Assignment and customer-approved JIT access. | Fully Addressed | Conformant. Ensures customer data sovereignty, local data residency for sensitive HR data, dedicated PaaS isolation, and zero standing vendor access. |
| **Decision D-02** (Commercial Pricing Model) | `.copilot-tracking/details/marketplace-plan.md` lines 45, 80–84; `docs/deployment/azure-managed-application.md` Section 4. Transactable offer: monthly base fee + tiered per-seat subscription + enterprise BYOL tier, with customer covering Azure consumption. | Fully Addressed | Conformant. Commercial model eliminates hosting margin volatility while enabling enterprise procurement via Azure Marketplace commits. |
| **createUiDefinition.json Schema & Constraints** | `infra/createUiDefinition.json` matching schema `CreateUIDefinition.MultiVm.json#`, handler `Microsoft.Azure.CreateUIDef`, version `0.1.2-preview`. Declares Basics blade and App Settings step with DropDowns, TextBoxes, defaults, and regex constraints. | Fully Addressed | Conformant. Verified by 6 tests in `TestCreateUiDefinitionSchema` in `tests/test_managed_app.py` and `packaging/managed_app/package_managed_app.py --validate-only`. |
| **100% Parameter Parity** | All 8 outputs from `createUiDefinition.json` (`location`, `environmentName`, `appNamePrefix`, `entraTenantId`, `botAppId`, `appServicePlanSku`, `searchSku`, `existingOpenAiEndpoint`) map 1:1 to parameters in `infra/mainTemplate.json`. | Fully Addressed | Conformant. Verified by 5 tests in `TestParameterParity` in `tests/test_managed_app.py` and preflight checks in packaging script. |
| **Zero Hardcoded Secrets Posture** | Scan of `infra/mainTemplate.json`, `infra/createUiDefinition.json`, `infra/main.bicep`, and `infra/main.bicepparam`. System-Assigned Managed Identity role assignments configured with `disableLocalAuth: true`. | Fully Addressed | Conformant. Verified by 3 tests in `TestZeroHardcodedSecrets` in `tests/test_managed_app.py`, 2 tests in `tests/test_packaging.py`, and synthetic secret detection controls. |
| **Managed App Packaging Utility & app.zip** | `packaging/managed_app/package_managed_app.py` validates schemas, parity, and secrets, then packages `app.zip` (6,348 bytes) containing `mainTemplate.json` and `createUiDefinition.json` at root. | Fully Addressed | Conformant. Verified by 5 tests in `TestManagedAppPackaging` in `tests/test_managed_app.py` and archive integrity verification. |
| **PRD NFR-003** (99.9% Monthly Availability) | App Service Premium/Standard tier capability, Cosmos DB multi-region readiness, Service Bus Standard with dead lettering, Linux Functions SLA processing (`infra/mainTemplate.json`, `docs/deployment/azure-managed-application.md`). | Fully Addressed | Conformant. High-availability PaaS architecture provided in deployment templates; operational availability SLA monitoring enabled via Application Insights. |
| **PRD NFR-005** (Entra ID Authentication & RBAC) | Entra ID tenant GUID parameter, Bot App registration ID, and granular RBAC role assignments (Key Vault Secrets User, Service Bus Data Sender/Receiver, Search Index Data Contributor, Cognitive Services OpenAI User, Cosmos DB Data Contributor). | Fully Addressed | Conformant. Enforces least-privilege identity boundaries; zero credential sharing across microservices. |
| **PRD NFR-008 & NFR-009** (Medical & Compensation Privacy) | Cosmos DB `hr-ticket-store` container secondary indexing exclusion policy for sensitive fields; Application Insights telemetry PII-denylist rules in `docs/deployment/azure-managed-application.md`. | Fully Addressed | Conformant. Secondary indexing excludes medical notes and compensation calculations; MRG boundary ensures physical residency. |
| **PRD NFR-011** (Maintainability & Configuration) | Template parameters and UI elements allow configuring environment, app prefix, SKUs, tenant ID, and external endpoints without touching application code. | Fully Addressed | Conformant. Portal wizard provides configurable deployment options adhering to parameter schemas. |
| **PRD NFR-012** (Operational Alerting) | Deployment of Log Analytics Workspace and Application Insights resource linked to App Service and Functions. | Fully Addressed | Conformant. Diagnostics and monitoring infrastructure declared in ARM template and Bicep. |
| **PRD NFR-014** (Observability & Metrics) | Application Insights telemetry pipeline and Azure Monitor metric hooks. | Fully Addressed | Conformant. Foundational infrastructure for metric tracking (resolution time, SLA dispatch, error rates) deployed with application. |
| **PRD NFR-015** (Interoperability & Versioned Contracts) | Azure Bot Service Teams channel integration (`Microsoft.BotService/botServices/channels`), Service Bus queues, Cosmos DB NoSQL APIs, and Azure AI Search endpoints. | Fully Addressed | Conformant. Verified by ARM resource declarations and Teams app manifest integration. |
| **PRD CON-004** (M365 Identity & Tenant Protection) | Teams app package (`packaging/teams/manifest.json` schema v1.16) and Bot Service channel integration configured for single-tenant customer Entra ID. | Fully Addressed | Conformant. Verified by 17 unit tests in `tests/test_packaging.py`. |
| **ADR C5** (Planned Azure Topology) | Template codifies App Service (Python 3.11), Functions (Python 3.11), separate Cosmos DB databases (`hr-ticket-store`, `hr-conversation-memory`), AI Search, Storage, Service Bus, and Key Vault. | Fully Addressed | Conformant. 100% faithful codification of ADR-0001 C5 architecture into ARM and Bicep artifacts. |
| **Plan Marker Adherence** | Phase `P05` and task `P05-T01` marked complete in `.copilot-tracking/plans/implementation-plan.md` and changes log; container phase marker `P01` preserved as unchecked. | Fully Addressed | Conformant. Clean plan marker tracking with bounded implementation scope discipline. |

### Critique and Follow-Up Assessment

* Latest critique dispositions: none (no critique was run during implementation).
* Material revisions: none.
* Dependent-work pause assessment: No pause required for bounded Phase P05 delivery; operational deployment pause remains appropriately enforced for live commercial marketplace onboarding and production tenant policy adoption.
* Justification assessment: Implementation directly fulfilled the authorized scope for Task P05-T01 following confirmed Decision D-01 without unwarranted expansion or drift.

| Follow-up item | Why outside immediate scope | Owner or next action | Assessment and route |
|---|---|---|---|
| Complete uncovered ticket rules and tests (overtime, attendance, remaining leave) | P05-T01 is bounded to Azure Managed Application packaging and marketplace readiness; ticket domain logic is in P01. | HR policy owner & Product Owner | Follow-up tracked in `.copilot-tracking/plans/implementation-plan.md`. |
| Define `Request Information` card action behavior, state transitions, and audit events | P05-T01 is bounded to deployment packaging; card action semantics are under P03. | Product Owner & HR policy owner | Follow-up tracked in `.copilot-tracking/plans/implementation-plan.md`. |
| Resolve durable audit integrity and retention mechanism (tamper-evident store / ledger) | P05-T01 provisions standard Cosmos DB PaaS; tamper-evident immutability requires architectural selection. | Security/Privacy lead & Platform Architecture | Follow-up tracked in `.copilot-tracking/plans/implementation-plan.md`. |

### Builder Self-Check

* [x] Every supplied requirement, acceptance criterion, in-scope marker, material update, critique disposition, validation result, blocker, remaining item, and plan follow-up has an assessment or explicit gap.
* [x] Findings are substantive, evidence-grounded, severity-graded, and use stable RV-xxx IDs with expected and observed behavior, a resolution condition, and one proposed route each.
* [x] Execution status, proposed outcome, validation coverage, limitations, and proposed routes are complete and internally consistent.
* [x] The summary is scoped and advisory, findings keep their supporting context together, and acceptance coverage distinguishes demonstrated gaps from unassessed behavior.
* [x] Standard review completely assessed the material boundary while omitting restatement, cosmetic feedback, exhaustive strengths, low-impact suggestions, and continual narration; deep review remained inside the supplied boundary.
* [x] The selected review worker did not edit Parent Decision Record, ask the user, mutate source or parent state, dispatch another worker, execute validation, or invoke a destination.
* Checked boundary: Azure Managed Application packaging artifacts (`infra/createUiDefinition.json`, `infra/mainTemplate.json`, `packaging/managed_app/package_managed_app.py`, `packaging/managed_app/app.zip`), Teams packaging artifacts (`packaging/teams/manifest.json`, `package.py`, icons, `hr-time-leave-teams.zip`), deployment documentation (`docs/deployment/azure-managed-application.md`), marketplace plan (`.copilot-tracking/details/marketplace-plan.md`), changes record (`.copilot-tracking/changes/2026-09-29/hr-time-leave-agent-implementation-changes.md`), implementation plan (`.copilot-tracking/plans/implementation-plan.md`), PRD requirements, ADR-0001, and unit tests (`tests/test_managed_app.py`, `tests/test_packaging.py`, and full 84-test test suite).
* Missing or limited evidence: Live Microsoft Partner Center publisher registration, live commercial marketplace offer certification, and live customer Azure subscription sandbox deployment are operational external processes that cannot be executed in this workspace; verified via comprehensive local static analysis, automated schema validation, parameter parity checks, and unit tests.

