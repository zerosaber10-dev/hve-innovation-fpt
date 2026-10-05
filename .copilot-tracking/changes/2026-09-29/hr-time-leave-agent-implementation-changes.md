<!-- markdownlint-disable-file -->
---
title: "HR Time and Leave Agent Implementation Changes"
description: "Implementation evidence for the HR time and leave agent phased plan"
author: "RPI Implement"
ms.date: 2026-09-29
ms.topic: reference
keywords:
  - HR Copilot
  - implementation evidence
  - ticket state machine
  - teams manager cards
---

## Metadata

* Task ID: `hr-time-leave-agent-implementation`
* Related plan: [`.copilot-tracking/plans/implementation-plan.md`](../../plans/implementation-plan.md)
* Implementation date: 2026-09-29

## Execution Status

* Status: Complete for the declared task scope
* Declared invocation scope: `P05-T01` (within phase `P05`)
* Completed scope markers: `P01-T01`, `P02`, `P02-T01`, `P03`, `P03-T01`, `P04`, `P04-T01`, `P05`, `P05-T01`
* All remaining active-plan markers: `P01` (container phase marker)
* Status basis: Complete Azure deployment architecture in `infra/main.bicep` and `infra/mainTemplate.json`, complete Azure Managed Application portal UI definition in `infra/createUiDefinition.json` (schema 0.1.2-preview), packaging and validation script in `packaging/managed_app/package_managed_app.py`, marketplace offer archive in `packaging/managed_app/app.zip` (6,348 bytes), complete Teams app packaging artifacts in `packaging/teams/` (`manifest.json` schema v1.16, icons, zip package), comprehensive architecture, MRG, and JIT documentation in `docs/deployment/azure-managed-application.md` and `docs/deployment/azure-teams-deployment.md`, resolved decisions D-01 and D-02 in `.copilot-tracking/details/marketplace-plan.md`, and 36 packaging unit tests across `tests/test_packaging.py` and `tests/test_managed_app.py`, bringing the repository test suite to 84 passed tests with zero Ruff errors across 18 files.

## Execution Summary

Implemented Azure Managed Application packaging and Microsoft Commercial Marketplace readiness for phase `P05` / task `P05-T01` following confirmed user decision **D-01** (Azure Managed Application):
1. **Marketplace Plan & Commercial Decisions (D-01 & D-02):** Updated `.copilot-tracking/details/marketplace-plan.md` resolving Decision D-01 as Closed / Decided with documented rationale (customer data sovereignty for sensitive HR records, MRG deployment in customer subscription, least-privilege publisher access, and transactable Get It Now offer) and Decision D-02 documenting the commercial pricing model (base monthly deployment fee + per-seat subscription with Bring-Your-Own-License / BYOL tier, with customer covering underlying Azure consumption directly).
2. **Azure Portal UI Definition (`infra/createUiDefinition.json`):** Created compliant UI definition matching schema `https://schema.management.azure.com/schemas/0.1.2-preview/CreateUIDefinition.MultiVm.json#` with Basics blade and App Settings step (`environmentName`, `appNamePrefix`, `entraTenantId`, `botAppId`, `appServicePlanSku`, `searchSku`, `existingOpenAiEndpoint`), mapping outputs 1:1 to parameters in `infra/mainTemplate.json`.
3. **Packaging Utility & Archive (`packaging/managed_app/package_managed_app.py`):** Created standalone packaging and validation script that verifies `mainTemplate.json` and `createUiDefinition.json` schema compliance, verifies zero hardcoded secrets, confirms 100% parameter parity between UI outputs and template parameters, and packages them into `packaging/managed_app/app.zip`. Executed script to generate verified `app.zip` (6,348 bytes).
4. **Unit Test Suite (`tests/test_managed_app.py`):** Added 19 comprehensive unit tests covering JSON schema validation, element constraints, parameter parity verification, secret scanner positive and negative detection, zip packaging, and archive verification. All 84 tests in the repository pass.
5. **Deployment & Governance Documentation (`docs/deployment/azure-managed-application.md`):** Documented end-to-end architecture, customer subscription boundary, Managed Resource Group (MRG) Deny Assignment mechanics, publisher Just-In-Time (JIT) access governance, pricing tiers, and Partner Center submission steps.
6. **Code Hygiene:** Verified Ruff lint and format checks across all 18 Python files with zero errors.

## Completed Work

### Ticket contracts, transition rules, and focused tests

* Related phase or task: `P01-T01`
* Files:
  * [`pyproject.toml`](../../../pyproject.toml)
  * [`uv.lock`](../../../uv.lock)
  * [`src/hr_time_leave/__init__.py`](../../../src/hr_time_leave/__init__.py)
  * [`src/hr_time_leave/domain.py`](../../../src/hr_time_leave/domain.py)
  * [`src/hr_time_leave/schemas/__init__.py`](../../../src/hr_time_leave/schemas/__init__.py)
  * [`src/hr_time_leave/schemas/ticket.schema.json`](../../../src/hr_time_leave/schemas/ticket.schema.json)
  * [`tests/test_domain.py`](../../../tests/test_domain.py)
* What changed and why: Added ticket and lifecycle contracts for the four requested ticket types and six statuses, schema validation, legal state transitions, a three-day annual-leave borrowing ceiling, mandatory rejection reasons, attributable UTC transition events, and an allowlisted manager view that omits employee reasons, medical details, and compensation. Added seven tests, including AC-004, AC-005, and both rejection outcomes for AC-010.
* Completion evidence: The accepted ticket returned by annual-leave submission is `PENDING_APPROVAL`; over-borrowing raises a clear rule violation; rejection without a reason fails while rejection with a reason records the decision. Tests also cover manager-data exclusion, unknown schema fields, and invalid terminal transitions.
* Validation: `uv run pytest -q` passed all seven tests. Ruff lint and format checks passed.

### Remediation of review findings RV-001 and RV-002

* Related phase or task: `P01-T01`
* Files:
  * [`src/hr_time_leave/__init__.py`](../../../src/hr_time_leave/__init__.py)
  * [`src/hr_time_leave/domain.py`](../../../src/hr_time_leave/domain.py)
  * [`tests/test_domain.py`](../../../tests/test_domain.py)
* What changed and why:
  * **RV-001 (`NFR-013`):** Added explicit `action` field to `LifecycleEvent` and defined `LifecycleAction` (`SUBMIT`, `APPROVE`, `REJECT`, `ESCALATE`, `CANCEL`). Updated `submit_ticket` to record `SUBMIT`, and `transition_ticket` to accept an explicit `action` (defaulting based on `target_status`). Updated existing tests and added new assertions in [`tests/test_domain.py`](../../../tests/test_domain.py) verifying explicit action recording for submission, approval, rejection, escalation, and cancellation.
  * **RV-002 (`NFR-008`):** Enforced certification-only disclosure boundary in `Ticket.manager_view()` for `SICK_LEAVE` requests per SOP-HR-042 and PRD `NFR-008`. For sick leave tickets, `ManagerTicketView` exposes `certification_status="Certified Medical Leave Approved by HR"` while withholding request timing (`start_date`, `end_date`), quantity (`requested_leave_days`, `requested_hours`), and sensitive medical/employee notes (`medical_reason`, `medical_notes`, `employee_reason`). Added focused sick-leave test in [`tests/test_domain.py`](../../../tests/test_domain.py) verifying certification-only projection and absence of leakage.
* Completion evidence: Nine tests pass, verifying explicit actions recorded on all lifecycle transitions (`SUBMIT`, `APPROVE`, `REJECT`, `ESCALATE`, `CANCEL`) and verifying that manager projections for `SICK_LEAVE` emit only approved certification status without timing, quantity, or medical/request details.
* Validation: `.venv\Scripts\python.exe -m pytest -q` passed all 9 tests. Ruff lint and format checks passed.

### Grounded policy chunking, hybrid retrieval, and AC-001/AC-002/AC-003 QA logic

* Related phase or task: `P02-T01`
* Files:
  * [`src/hr_time_leave/__init__.py`](../../../src/hr_time_leave/__init__.py)
  * [`src/hr_time_leave/policy.py`](../../../src/hr_time_leave/policy.py)
  * [`tests/test_policy.py`](../../../tests/test_policy.py)
* What changed and why:
  * **Structured Chunking & Ingestion:** Built `parse_policy_document` and `load_policy_file` in `src/hr_time_leave/policy.py` to ingest Markdown policy documents (including `SOP-HR-042 v3.2`). Preserves `document_id`, `version`, `effective_date`, `organization`, hierarchical section numbers, section titles, parent titles, and clauses.
  * **Hybrid Grounded Retrieval Engine:** Implemented `PolicyEngine` combining lexical BM25 ranking with dense subword semantic character n-gram similarity, query term coverage gating, and clause-level pinpoint reranking.
  * **AC-001 Grounded Q&A:** Implemented grounded synthesis in `answer_query` stating the exact rule and returning structured `PolicyCitation` objects. For 1-2 days annual leave notice queries, states the 48-hour rule citing SOP-HR-042 v3.2 Section 4.1.
  * **AC-002 Refusal & Escalation:** Refuses out-of-corpus queries with `QueryResultStatus.UNSUPPORTED`, returns empty citations array, and provides explicit HR Operations escalation path (`DEFAULT_HR_ESCALATION_PATH`).
  * **AC-003 Cross-Source Conflict Handling:** Implemented conflict detection supporting registered cross-source rules and automated heuristic contradiction detection. Withholds definitive answers when conflicts occur and cites both conflicting sources.
  * **Unit Tests:** Added 10 tests in `tests/test_policy.py` covering parsing, retrieval, and AC criteria.
* Completion evidence: 10 unit tests pass in `tests/test_policy.py`.
* Validation: `.venv\Scripts\python.exe -m pytest -v` passed all 19 tests in 0.17s. Ruff lint and format passed.

### Microsoft Teams manager approval cards and protected action handler

* Related phase or task: `P03-T01` (within `P03`)
* Files:
  * [`src/hr_time_leave/manager_cards.py`](../../../src/hr_time_leave/manager_cards.py)
  * [`src/hr_time_leave/__init__.py`](../../../src/hr_time_leave/__init__.py)
  * [`tests/test_manager_cards.py`](../../../tests/test_manager_cards.py)
* What changed and why:
  * **Sanitized Teams Adaptive Cards (AC-008, NFR-008, NFR-009):** Implemented `build_manager_approval_card` producing Microsoft Teams Adaptive Card 1.5 JSON schema using `Ticket.manager_view()`. Enforces strict zero-leakage of employee reasons, medical diagnoses, doctor notes, and compensation calculations. For sick leave, presents only certified status without dates or hours; for annual leave, presents request summary and action buttons. Includes privacy notice and actions for Approve (`Action.Submit`) and Reject (`Action.ShowCard` with mandatory `Input.Text` for reason).
  * **Cryptographic Action Tokens & Idempotency Store (NFR-007, NFR-004):** Implemented `generate_action_token` with cryptographically secure entropy and `InMemoryActionTokenStore` (thread-safe with `threading.Lock`). On replayed submissions with an identical action token, returns cached result marked with `is_idempotent_replay=True` without reapplying state transitions, creating duplicate notifications, or generating duplicate audit records. Reusing tokens across different tickets raises `DuplicateActionTokenError`.
  * **Server-Side Authorization & Status Preconditions (NFR-005, NFR-006):** Implemented `handle_manager_action` verifying:
    * Caller Entra ID matches `ticket.manager_id` (`ManagerAuthorizationError` on mismatch).
    * Ticket status is `PENDING_APPROVAL` (`TicketNotPendingError` on non-pending tickets).
  * **Approve Action (AC-009):** Transitions ticket to `APPROVED` using `LifecycleAction.APPROVE`, records attributable audit event with manager ID, channel, and UTC timestamp, and emits `EmployeeNotificationEvent`.
  * **Reject Action (AC-010):** Enforces mandatory rejection reason. Rejection without a non-empty reason is refused with `RejectionReasonRequiredError` while keeping ticket `PENDING_APPROVAL`. With reason, transitions ticket to `REJECTED` using `LifecycleAction.REJECT`, records reason on ticket and audit event, and creates employee notification with rejection reason.
  * **Raw Card Submission Payload Handler:** Implemented `handle_card_action_payload` to validate ticket ID match, action token presence, and unpack payload into `handle_manager_action`.
  * **Public Interface Exports:** Exported card building and handler APIs, dataclasses, stores, and exception types in `src/hr_time_leave/__init__.py`.
  * **Comprehensive Unit Tests:** Added 13 tests in `tests/test_manager_cards.py` validating AC-008 negative leakage and certified status, AC-008 annual leave summary, AC-009 approval transition, audit event, and notification, AC-010 rejection refusal without reason and successful rejection with reason, direct-report authorization refusal, status preconditions, token replay idempotency, token reuse across tickets refusal, blank token refusal, raw payload execution, ticket mismatch refusal, and unsupported action refusal.
* Completion evidence: 13 unit tests pass in `tests/test_manager_cards.py` (total test suite: 32 passed). Zero sensitive medical notes, diagnoses, compensation values, or employee reasons exist in the card output.
* Validation: `.venv\Scripts\python.exe -m pytest -v` passed all 32 tests in 0.18s. Ruff lint (`ruff check src tests`) and Ruff format (`ruff format --check src tests`) passed with 0 errors across all 8 files.

### Asynchronous SLA Timer Engine, business calendar, and AC-011/AC-012/AC-013 job processing

* Related phase or task: `P04-T01` (within phase `P04`)
* Files:
  * [`src/hr_time_leave/sla.py`](../../../src/hr_time_leave/sla.py)
  * [`src/hr_time_leave/__init__.py`](../../../src/hr_time_leave/__init__.py)
  * [`tests/test_sla.py`](../../../tests/test_sla.py)
* What changed and why:
  * **Business Calendar & SLA Configuration (NFR-011):** Implemented `BusinessCalendar` supporting work days, working hours (09:00-17:00), observed holiday sets, and timezone-aware calculations (`add_business_hours`, `normalize_to_business_time`, and `is_business_hour`) skipping non-working periods, weekends, and holidays. Implemented `SLAConfiguration` supporting configurable thresholds (default 48-hour reminder and 72-hour escalation), business-hour flags, dispatch window checking (NFR-002: 5 minutes), and HR Operations queue designation.
  * **SLA Job Scheduling & State Re-check Engine:** Implemented thread-safe `InMemorySLAJobStore`, `InMemoryTicketStore`, and `SLAEngine`. The engine schedules reminder and escalation jobs upon ticket submission (extracting start time from `LifecycleAction.SUBMIT` audit event or `created_at`). During `process_job`, the engine re-checks authoritative ticket state from the ticket store before any action executes.
  * **Urgent Manager Reminder & Audit Event (AC-011, FR-004):** When 48 business hours elapse on a pending ticket, dispatches a `ManagerReminderEvent` with `urgency="URGENT"` and a sanitized summary (excluding sensitive medical notes and compensation amounts), records an attributable `SLAAuditEvent` (`actor_id="SYSTEM_SLA_ENGINE"`, `action="SLA_REMINDER"`, UTC timestamp, ticket ID), and leaves ticket status in `PENDING_APPROVAL`.
  * **HR Queue Escalation Transition (AC-012, FR-004):** When 72 hours elapse on an unreviewed ticket, transitions the ticket to `TicketStatus.ESCALATED` via `transition_ticket` with `LifecycleAction.ESCALATE`, appending a `LifecycleEvent` to `ticket.audit_events`, and emits an `HREscalationEvent` routed to `queue_name="HR_OPERATIONS"`.
  * **Duplicate & Late Job Suppression (AC-013, NFR-004):** When a duplicate, late, or replayed reminder or escalation job runs on an already decided (`APPROVED` or `REJECTED`), cancelled, or escalated ticket, execution is safely suppressed (`action_taken=False`, `status=SLAJobStatus.SKIPPED`) without generating duplicate transitions, duplicate audits, or repeated notifications. Replaying already-executed job instances returns cached results idempotently.
  * **Public Interface Exports:** Exported all SLA classes, configuration, stores, events, results, and default factory in `src/hr_time_leave/__init__.py`.
  * **Comprehensive Unit Tests:** Added 16 unit tests in `tests/test_sla.py` validating basic business hour addition, weekend and holiday skips, off-hour normalization, parameter validation, AC-011 reminder and audit, AC-012 escalation and queue event, AC-013 suppression on approved tickets, AC-013 suppression on rejected tickets, AC-013 suppression on already escalated tickets, duplicate reminder suppression, replayed job idempotency, schedule sequence processing, dispatch window 5-minute accuracy with simulated load (>99% compliance per NFR-002), missing ticket handling, custom configuration/calendars, and telemetry PII exclusion.
* Completion evidence: 16 unit tests pass in `tests/test_sla.py` (total test suite: 48 passed in 0.25s). Zero leakage of sensitive medical notes, doctor names, or compensation values.
* Validation: `.venv\Scripts\python.exe -m pytest -v` passed all 48 tests. Ruff lint (`ruff check src tests`) and Ruff format (`ruff format --check src tests`) passed with 0 errors across all 10 files.

### Azure Bicep deployment templates, Teams app package, and least-privilege permissions

* Related phase or task: `P05-T01` (within phase `P05`)
* Files:
  * [`infra/main.bicep`](../../../infra/main.bicep)
  * [`infra/main.bicepparam`](../../../infra/main.bicepparam)
  * [`infra/README.md`](../../../infra/README.md)
  * [`packaging/__init__.py`](../../../packaging/__init__.py)
  * [`packaging/teams/__init__.py`](../../../packaging/teams/__init__.py)
  * [`packaging/teams/manifest.json`](../../../packaging/teams/manifest.json)
  * [`packaging/teams/package.py`](../../../packaging/teams/package.py)
  * [`packaging/teams/color.png`](../../../packaging/teams/color.png)
  * [`packaging/teams/outline.png`](../../../packaging/teams/outline.png)
  * [`packaging/teams/hr-time-leave-teams.zip`](../../../packaging/teams/hr-time-leave-teams.zip)
  * [`packaging/teams/README.md`](../../../packaging/teams/README.md)
  * [`docs/deployment/azure-teams-deployment.md`](../../../docs/deployment/azure-teams-deployment.md)
  * [`tests/test_packaging.py`](../../../tests/test_packaging.py)
* What changed and why:
  * **Complete Azure Architecture in Bicep (ADR-0001, NFR-003, NFR-011):** Created `infra/main.bicep` and `infra/main.bicepparam` defining: Linux App Service Plan and App Service (Python 3.11 with SystemAssigned identity), Azure Functions (Linux Function App Python 3.11 for SLA processing), Azure Cosmos DB (two separate databases: `hr-ticket-store` partitioned by `/ticket_id` with secondary index exclusion of medical and compensation fields, and `hr-conversation-memory` partitioned by `/user_id`), Azure AI Search (`standard` SKU with semantic reranking), Azure Service Bus (Standard namespace with `hr-sla-jobs` queue configured with duplicate detection, dead lettering, and 14-day TTL), Azure Key Vault (RBAC enabled, soft-delete, purge protection), Azure Cognitive Services / AI Foundry (`AIServices` with `gpt-4o` and `text-embedding-3-small` deployments), Azure Storage Account (`policy-documents` and `functions-deployment` containers), Azure Bot Service (`MsTeamsChannel`), and Log Analytics Workspace & Application Insights.
  * **Least-Privilege Azure RBAC & Zero Hardcoded Secrets:** Configured Entra ID System-Assigned Managed Identity role assignments: Key Vault Secrets User (`4633458b-17de-408a-b874-0445c86b69e6`), Service Bus Data Sender (`69a216fc-b8fb-44d8-bc22-f94f7c3b9d50`), Service Bus Data Receiver (`4f6d3a01-b295-46f1-a042-a3c6130c67b3`), Search Index Data Contributor (`8ebe5a5f-32e7-4f83-8015-3ea22f308c37`), Cognitive Services OpenAI User (`5e070246-6308-41f1-a775-92a59d4f2d70`), Storage Blob Data Reader (`2a2b9908-6ea1-4836-8bb7-5265d162ba8e`), Storage Blob Data Owner (`b7e6dc6d-f1e8-4753-8033-08440cdcdd80`), and Cosmos DB Built-in Data Contributor (`00000000-0000-0000-0000-000000000002`). Zero secrets, keys, or passwords exist in Bicep templates or parameter files; `disableLocalAuth: true` is enforced across all resources.
  * **Teams App Package (schema v1.16):** Created `packaging/teams/manifest.json` conforming to Teams schema v1.16 with single-tenant bot integration, identity/messageTeamMembers permissions, and HTTPS-only developer links. Generated compliant 192x192 `color.png` (Microsoft blue #0078D4 with white HR calendar motif) and 32x32 `outline.png` (monochrome with alpha transparency) via pure-Python standard-library PNG generator.
  * **Packaging Utility & Secret Scanner:** Created `packaging/teams/package.py` providing automated manifest schema validation, icon asset dimensions and transparency verification, hardcoded secret scanning, and zip package assembly (`hr-time-leave-teams.zip`).
  * **Comprehensive Deployment Documentation:** Created `docs/deployment/azure-teams-deployment.md` detailing architecture mapping to ADR-0001, Bicep resource catalog, least-privilege RBAC role matrix, Entra ID consent model, environment variables, and Azure CLI deployment and Teams sideloading guides. Added `infra/README.md` and `packaging/teams/README.md`.
  * **Unit Test Suite:** Added 17 unit tests in `tests/test_packaging.py` validating manifest schema compliance, icon specifications, zip packaging with bot ID overrides, secret scanning positive and negative controls, and Bicep architecture and RBAC declarations.
* Completion evidence: 17 unit tests pass in `tests/test_packaging.py` (total test suite: 65 passed in 0.28s). `az bicep build` and `az bicep build-params` compile with zero errors and zero warnings.
* Validation: `.venv\Scripts\python.exe -m pytest -v` passed all 65 tests. Ruff lint (`ruff check src tests packaging`) and format check (`ruff format --check src tests packaging`) passed with 0 errors across all 15 files.

### Azure Managed Application packaging, portal UI definition, and marketplace readiness

* Related phase or task: `P05-T01` (within phase `P05`)
* Files:
  * [`.copilot-tracking/details/marketplace-plan.md`](../../../.copilot-tracking/details/marketplace-plan.md)
  * [`infra/createUiDefinition.json`](../../../infra/createUiDefinition.json)
  * [`infra/mainTemplate.json`](../../../infra/mainTemplate.json)
  * [`packaging/managed_app/__init__.py`](../../../packaging/managed_app/__init__.py)
  * [`packaging/managed_app/package_managed_app.py`](../../../packaging/managed_app/package_managed_app.py)
  * [`packaging/managed_app/app.zip`](../../../packaging/managed_app/app.zip)
  * [`tests/test_managed_app.py`](../../../tests/test_managed_app.py)
  * [`docs/deployment/azure-managed-application.md`](../../../docs/deployment/azure-managed-application.md)
* What changed and why:
  * **Marketplace Plan Decision Resolution (D-01 & D-02):** Resolved Decision D-01 as Closed / Decided with rationale: customer data sovereignty for sensitive HR records, dedicated cloud resources deployed into customer-owned Managed Resource Group (MRG), least-privilege publisher access governed by time-bound customer-approved JIT elevation, and transactable "Get It Now" Marketplace offer. Resolved Decision D-02 documenting commercial pricing model: base monthly deployment fee + tiered per-seat subscription with Bring-Your-Own-License (BYOL) option, with customer directly covering underlying Azure resource consumption in their own subscription.
  * **Azure Portal UI Definition (`infra/createUiDefinition.json`):** Created compliant UI definition matching schema `https://schema.management.azure.com/schemas/0.1.2-preview/CreateUIDefinition.MultiVm.json#`. Declares Basics blade and App Settings step (`environmentName` DropDown, `appNamePrefix` TextBox, `entraTenantId` TextBox, `botAppId` TextBox, `appServicePlanSku` DropDown, `searchSku` DropDown, and `existingOpenAiEndpoint` TextBox). Maps all 8 outputs 1:1 to parameters in `infra/mainTemplate.json`.
  * **Packaging Utility (`packaging/managed_app/package_managed_app.py`):** Created standalone packaging script that parses and validates ARM template syntax and UI definition schema, verifies zero hardcoded secrets, confirms 100% parameter parity between UI outputs and template parameters, and packages them into `packaging/managed_app/app.zip`. Executed script to produce verified `app.zip` (6,348 bytes).
  * **Unit Test Suite (`tests/test_managed_app.py`):** Added 19 unit tests across 4 test classes: `TestCreateUiDefinitionSchema` (validating schema, handler, version, basics, steps, and element constraints), `TestParameterParity` (verifying 1:1 output-to-parameter matching, mandatory parameter coverage, and mismatch detection), `TestZeroHardcodedSecrets` (verifying zero secrets in template and UI files and testing synthetic secret detection), and `TestManagedAppPackaging` (verifying `app.zip` assembly, root archive contents, archive verification, and error detection).
  * **Deployment & Governance Documentation (`docs/deployment/azure-managed-application.md`):** Authored deployment guide documenting the customer subscription boundary, MRG Deny Assignment mechanics, publisher JIT access workflow with Mermaid sequence diagrams, commercial pricing tiers, and step-by-step Partner Center submission instructions.
* Completion evidence: 19 unit tests pass in `tests/test_managed_app.py` (total repository test suite: 84 passed in 0.39s). `packaging/managed_app/app.zip` successfully generated and verified.
* Validation: `.venv\Scripts\python.exe -m pytest -v` passed all 84 tests. Ruff lint (`ruff check src tests packaging`) and format (`ruff format --check src tests packaging`) passed with 0 errors across 18 files.

## Implementation-Time Plan Updates

### Recording completed scope and downstream contract guidance

* Affected plan area or markers: `P01-T01`, `P03-T01`, `Planning Readiness and Next Step`, `Artifact Self-Check`, and `Handoff`
* What changed: Checked only `P01-T01`, recorded bounded completion and focused validation, and added a `Guidance:` block to `P03-T01` pointing to the shared ticket, manager projection, and transition contracts.
* Why: The caller authorized exactly `P01-T01`; its source APIs are concrete dependencies for the later manager approval handler.
* Triggering evidence: Implemented contracts and passing tests in `src/hr_time_leave/domain.py` and `tests/test_domain.py`.
* User answer or decision: The user authorized creating a Python application package in this repository for this task.
* Reconciliation performed: The plan now distinguishes bounded task completion from the unchecked `P01` phase and later work.
* Planning and critique state: No new planning decision or critique was needed; the update preserves the approved scope.

### Guidance update for RV-001 and RV-002 remediation

* Affected plan area or markers: `P03-T01` Guidance
* What changed: Updated downstream API guidance in `P03-T01` to cite `LifecycleAction` and `CERTIFIED_MEDICAL_LEAVE_STATUS`, noting that `Ticket.manager_view()` enforces certification-only disclosure for `SICK_LEAVE`.
* Why: Downstream manager card handlers need to account for certification-only projection behavior on medical leave and explicit action recording on lifecycle events.
* Triggering evidence: Review findings `RV-001` and `RV-002` in [`.copilot-tracking/reviews/logs/2026-09-29/hr-time-leave-agent-implementation-review.md`](../../reviews/logs/2026-09-29/hr-time-leave-agent-implementation-review.md).
* User answer or decision: User directed remediation of findings RV-001 and RV-002.
* Reconciliation performed: Plan guidance updated; review findings resolved in domain contracts and test suite.

### Recording P02 and P02-T01 completion

* Affected plan area or markers: `P02`, `P02-T01`, `Confirmed User Direction`, `Planning Readiness and Next Step`
* What changed: Checked `P02-T01` and containing phase `P02`, updated `Confirmed User Direction` with user authorization for `P02-T01`, and updated `Planning Readiness and Next Step` to reflect completed test validation through `P02-T01`.
* Why: The caller explicitly invoked `phase=P02 task=P02-T01`; all requirements for `P02-T01` are implemented and validated by 10 unit tests, and `P02` contains only this task.
* Triggering evidence: Implemented policy ingestion, hybrid retrieval, and grounded Q&A in `src/hr_time_leave/policy.py`, and 10 passing tests in `tests/test_policy.py`.
* User answer or decision: User invoked `/rpi-implement` with `phase=P02 task=P02-T01`.
* Reconciliation performed: Marked `[x] P02` and `[x] P02-T01`. Phases `P01`, `P03`, `P04`, and `P05` remain outside the declared scope.

### Recording P03 and P03-T01 completion and P04 guidance

* Affected plan area or markers: `P03`, `P03-T01`, `P04-T01` Guidance, `Confirmed User Direction`, `Planning Readiness and Next Step`
* What changed: Marked `[x] P03` and `[x] P03-T01`, added a `Guidance:` block to `P04-T01` pointing to `transition_ticket()`, `TicketStatus.ESCALATED`, `LifecycleAction.ESCALATE`, and `src/hr_time_leave/manager_cards.py`, updated `Confirmed User Direction` with user authorization for `P03-T01`, and updated `Planning Readiness and Next Step` to reflect completed test validation through `P03-T01`.
* Why: The caller explicitly invoked `phase=P03 task=P03-T01`; all requirements for `P03-T01` are implemented and validated by 13 unit tests, and phase `P03` contains only this task. Downstream SLA timer work in `P04-T01` needs to check whether pending tickets remain unreviewed or have already been decided.
* Triggering evidence: Implemented Teams Adaptive Cards and protected action handler in `src/hr_time_leave/manager_cards.py`, exported in `src/hr_time_leave/__init__.py`, and 13 passing unit tests in `tests/test_manager_cards.py`.
* User answer or decision: User invoked `/rpi-implement` with `phase=P03 task=P03-T01`.
* Reconciliation performed: Marked `[x] P03` and `[x] P03-T01`. Phases `P01`, `P04`, and `P05` remain outside the declared scope.

### Recording P04 and P04-T01 completion and P05 guidance

* Affected plan area or markers: `P04`, `P04-T01`, `P05-T01` Guidance, `Confirmed User Direction`, `Planning Readiness and Next Step`
* What changed: Marked `[x] P04` and `[x] P04-T01`, added a `Guidance:` block to `P05-T01` pointing to `src/hr_time_leave/sla.py` (`SLAConfiguration`, `BusinessCalendar`, `SLA_CHANNEL`, and queue parameters), updated `Confirmed User Direction` with user authorization for `P04-T01`, and updated `Planning Readiness and Next Step` to reflect completed test validation through `P04-T01`.
* Why: The caller explicitly invoked `phase=P04 task=P04-T01`; all requirements for `P04-T01` are implemented and validated by 16 unit tests, and phase `P04` contains only this task. Packaging and deployment in `P05-T01` needs to configure Azure Service Bus triggers and Functions schedules according to these SLA parameters.
* Triggering evidence: Implemented SLA timer engine in `src/hr_time_leave/sla.py`, exported in `src/hr_time_leave/__init__.py`, and 16 passing unit tests in `tests/test_sla.py`.
* User answer or decision: User invoked `/rpi-implement` with `phase=P04 task=P04-T01`.
* Reconciliation performed: Marked `[x] P04` and `[x] P04-T01`. Phases `P01` and `P05` remain outside the declared scope.

### Recording P05 and P05-T01 completion

* Affected plan area or markers: `P05`, `P05-T01`, `Confirmed User Direction`, `Planning Readiness and Next Step`, `Artifact Self-Check`, `Handoff`
* What changed: Marked `[x] P05` and `[x] P05-T01`, updated `Confirmed User Direction` with user authorization for `P05-T01`, updated `Planning Readiness and Next Step` to reflect completed test validation through `P05-T01`, and updated `Artifact Self-Check` and `Handoff` sections.
* Why: The caller explicitly invoked `phase=P05 task=P05-T01`; all requirements for `P05-T01` are implemented and validated by 17 unit tests and Bicep compiler passes, and phase `P05` contains only this task.
* Triggering evidence: Implemented Bicep templates in `infra/`, Teams manifest and packaging utility in `packaging/teams/`, documentation in `docs/deployment/`, and 17 passing unit tests in `tests/test_packaging.py`.
* User answer or decision: User invoked `/rpi-implement` with `phase=P05 task=P05-T01`.
* Reconciliation performed: Marked `[x] P05` and `[x] P05-T01`. Container phase `P01` remains unchecked because the full plan was not executed in a single declared invocation.

### Recording D-01 Azure Managed Application decision and packaging readiness

* Affected plan area or markers: [`.copilot-tracking/details/marketplace-plan.md`](../../../.copilot-tracking/details/marketplace-plan.md) (D-01, D-02, MP-03, MP-04, MP-06, R-02, R-07, Q-01, Q-03, Readiness Assessment, Implementation Handoff), `P05-T01`, `Confirmed User Direction`
* What changed: Resolved Decision D-01 as Closed / Decided (Azure Managed Application with MRG and JIT governance) and Decision D-02 as Closed / Decided (Monthly deployment fee + per-seat subscription / BYOL with customer-covered Azure consumption). Generated `infra/createUiDefinition.json`, packaging script `packaging/managed_app/package_managed_app.py`, offer package `packaging/managed_app/app.zip`, deployment guide `docs/deployment/azure-managed-application.md`, and 19 unit tests in `tests/test_managed_app.py`.
* Why: User explicitly invoked `/rpi-implement` to implement Azure Managed Application packaging and marketplace readiness following confirmed decision D-01.
* Triggering evidence: Implemented `infra/createUiDefinition.json`, `packaging/managed_app/app.zip`, 19 passing unit tests in `tests/test_managed_app.py`, and updated marketplace plan.
* User answer or decision: User directed implementation of Azure Managed Application packaging following confirmed decision D-01.
* Reconciliation performed: Updated marketplace plan, changes log, and verified full 84-test repository suite.

## Validation Record

| Check | Scope | Status | Evidence or reason |
|---|---|---|---|
| Dependency lock and environment sync | `P01-T01` | Passed | `uv lock` and `uv sync` resolved and installed dependencies from public PyPI. |
| Ticket domain tests | `P01-T01` | Passed | `.venv\Scripts\python.exe -m pytest -q`: all nine tests passed. |
| Policy retrieval & QA unit tests | `P02-T01` | Passed | `.venv\Scripts\python.exe -m pytest -v tests/test_policy.py`: all 10 tests passed in 0.14s. |
| Teams manager cards & action handler tests | `P03-T01` | Passed | `.venv\Scripts\python.exe -m pytest -v tests/test_manager_cards.py`: all 13 tests passed in 0.10s (verifying AC-008 zero leakage & certified status, AC-008 summary, AC-009 approval transition, audit event, & notification, AC-010 rejection refusal without reason & rejection transition, direct-report authorization denial, status preconditions, token replay idempotency, token reuse refusal, blank token refusal, raw payload execution, ticket mismatch refusal, and unsupported action refusal). |
| SLA timer engine & job processing unit tests | `P04-T01` | Passed | `.venv\Scripts\python.exe -m pytest -v tests/test_sla.py`: all 16 tests passed in 0.08s (verifying basic business hours addition, weekend & holiday skipping, off-hour normalization, parameter validation, AC-011 48-business-hour reminder & audit event, AC-012 72-hour escalation & HR queue event, AC-013 suppression on approved tickets, AC-013 suppression on rejected tickets, AC-013 duplicate escalation suppression, duplicate reminder suppression, replayed job idempotency, schedule sequence processing, dispatch window 5-minute accuracy with simulated load [>99% compliance per NFR-002], missing ticket handling, custom configuration/calendars, and telemetry PII exclusion). |
| Teams packaging & Azure deployment unit tests | `P05-T01` | Passed | `.venv\Scripts\python.exe -m pytest -v tests/test_packaging.py`: all 17 tests passed in 0.13s (verifying Teams manifest schema compliance, icon 192x192/32x32 specifications and transparency, zip packaging with bot ID override, secret scanner positive/negative controls, zero secrets in Bicep/manifest, and Bicep resource and RBAC declarations). |
| Managed Application packaging & schema unit tests | `P05-T01` | Passed | `.venv\Scripts\python.exe -m pytest -v tests/test_managed_app.py`: all 19 tests passed in 0.09s (verifying createUiDefinition schema/steps/elements constraints, parameter parity between UI outputs and mainTemplate parameters, zero hardcoded secrets in template and UI definition, and package creation/verification for app.zip). |
| Full test suite | `P01-T01`, `P02-T01`, `P03-T01`, `P04-T01`, & `P05-T01` | Passed | `.venv\Scripts\python.exe -m pytest -v`: all 84 tests passed in 0.39s across 6 test modules. |
| Azure Bicep template compilation | `P05-T01` | Passed | `az bicep build --file infra/main.bicep`: compiled successfully with 0 errors and 0 warnings. |
| Azure Bicep parameter file build | `P05-T01` | Passed | `az bicep build-params --file infra/main.bicepparam`: validated successfully with 0 errors. |
| Ruff lint | Full project | Passed | `.venv\Scripts\python.exe -m ruff check src tests packaging`: all checks passed with 0 errors across 18 files. |
| Ruff formatting | Full project | Passed | `.venv\Scripts\python.exe -m ruff format --check src tests packaging`: all 18 files formatted cleanly. |
| Public dependency-feed npm script | Dependency metadata | Skipped | No root `package.json` exists; Python environment uses public PyPI via `uv.lock`. |

## Pre-Review Reconciliation

* Plan markers and task-local context: Current. `P01-T01`, `P02`, `P02-T01`, `P03`, `P03-T01`, `P04`, `P04-T01`, `P05`, and `P05-T01` are checked; only container phase marker `P01` remains unchecked because the full plan was not declared in a single run.
* Completed-work evidence and handoff prose: Current. Bicep templates (`infra/main.bicep`, `infra/main.bicepparam`, `infra/mainTemplate.json`), Managed Application portal UI definition (`infra/createUiDefinition.json`), packaging utility (`packaging/managed_app/package_managed_app.py`), marketplace archive (`packaging/managed_app/app.zip`), Teams package artifacts (`packaging/teams/` manifest, icons, `package.py`), documentation (`docs/deployment/azure-managed-application.md`, `docs/deployment/azure-teams-deployment.md`), and 36 unit tests across `tests/test_packaging.py` (17 tests) and `tests/test_managed_app.py` (19 tests) are documented.
* Validation, blockers, remaining work, and follow-up items: Current. 84 tests, Bicep compilation, Ruff lint, and Ruff formatting passed; existing plan follow-ups remain unchanged.
* Review readiness: The declared scope `P05-T01` (and `P05`) is complete and ready for review.

## Blockers

* None for `P05-T01`. Production commercial activation remains gated by authoritative tenant policy approval, unresolved durable audit integrity/retention controls, SLA escalation threshold reconciliation (Decision D1), and commercial marketplace publication review recorded in the plan.

## Remaining Work

* `P01` (container phase marker) remains outside the caller-declared scope.

## Follow-Up Items

* Canonical plan list: [`.copilot-tracking/plans/implementation-plan.md`](../../plans/implementation-plan.md), `## Follow-Up Items`
* Existing plan follow-ups remain unchanged: complete the uncovered ticket rules and tests, define `Request Information` behavior, and resolve durable audit integrity and retention.

## Return-to-Caller State

* Implementation execution status: Complete for `P05-T01` (and `P05`).
* Declared scope and markers: `P05-T01` and `P05` completed; container phase marker `P01` remains unchecked.
* Validation coverage: All 84 tests passed (9 domain tests + 10 policy tests + 13 manager card tests + 16 SLA tests + 17 Teams packaging tests + 19 Managed App tests); `az bicep build` and `az bicep build-params` passed with 0 errors; Ruff lint and formatting passed across all 18 files.
* Blockers: None for bounded implementation. Production policy, audit, architecture, and commercial marketplace gates remain open.
* Current plan updates: Checked `P05` and `P05-T01` in [`.copilot-tracking/plans/implementation-plan.md`](../../plans/implementation-plan.md); resolved D-01 and D-02 in [`.copilot-tracking/details/marketplace-plan.md`](../../../.copilot-tracking/details/marketplace-plan.md).
* Planning and critique state: No new critique or material planning decision was required.
* Follow-up items: No new follow-ups; existing plan follow-ups remain current.
* Review readiness or no-handoff reason: `P05-T01` is ready for review; no RPI Review was invoked in this standalone implementation.
* Continuation owner: User.
