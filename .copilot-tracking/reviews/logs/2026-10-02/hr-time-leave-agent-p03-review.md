<!-- markdownlint-disable-file -->
# Review: HR Time and Leave Agent Implementation (Phase P03)

## Executive Summary

* Assessment: Complete implementation of Phase P03 (Task P03-T01: Build the manager card and protected action handler). The implementation provides Microsoft Teams Adaptive Card 1.5 generation using `Ticket.manager_view()` (AC-008: strict zero-disclosure of sensitive medical notes/diagnoses, employee reasons, or compensation amounts; certification-only display for sick leave and permitted summary for other leave types), a server-side protected manager action handler with direct-report authorization and status precondition checks, idempotent action token handling via a thread-safe in-memory store, APPROVE transition to APPROVED with audit event and employee notification (AC-009), REJECT transition requiring a mandatory non-empty reason with audit event and employee notification (AC-010), raw Teams card payload execution, and 13 unit tests in `tests/test_manager_cards.py`. Acceptance criteria AC-008, AC-009, and AC-010 are fully demonstrated by automated tests, bringing the full test suite to 32 passing tests.
* Why this matters: Protects sensitive employee health and compensation information from exposure to line managers, prevents unauthorized or duplicated manager decisions on leave requests, ensures auditability of all lifecycle changes, and guarantees employees are notified of manager decisions with explicit feedback upon rejection.
* Builder execution: Complete
* Proposed review execution: Complete
* Proposed outcome: Conformant
* Validation coverage: 32/32 unit tests passing (13 manager card tests in `tests/test_manager_cards.py`, 10 policy tests in `tests/test_policy.py`, 9 domain tests in `tests/test_domain.py`), Ruff linter passing (0 errors across 8 files), Ruff code formatter passing (0 changes needed across 8 files).
* Confidence and limitations: High confidence for local prototype card builder, protected action handler, and AC-008/AC-009/AC-010 validation logic. Limitations: The current implementation operates as an in-memory Python component using an in-memory token store and simulated Teams JSON payloads; production Teams app packaging, Bot Framework / cloud adapter hosting, live Entra ID token verification, and durable audit storage remain documented external production gates.

The assessment above is the builder's proposal. Parent Decision Record contains the current final decision and next actions, or states that decisions are pending.

## What You May Not Know

* **Adaptive Card 1.5 Contract vs. Experience Design Wireframe:** The implemented `build_manager_approval_card` generates standard Microsoft Teams Adaptive Card 1.5 JSON with zero-leakage constraints based exclusively on `Ticket.manager_view()`. While the early wireframe in `experience-design.md` sketched a `Request Information` action button, planning decision D3 and risk analysis explicitly established that `Request Information` semantics (state transition, employee response path, deadline, audit event) are not yet specified in the PRD or SOP. P03-T01 properly restricts actions to APPROVE and REJECT without prematurely inventing undefined states.
* **Sick Leave Certification-Only Display:** Per `NFR-008` and `AC-008`, for `SICK_LEAVE` tickets the card exposes only `certification_status="Certified Medical Leave Approved by HR"`, with dates, duration (days/hours), employee reasons, and medical details completely redacted. For other leave types (e.g. `ANNUAL_LEAVE`), permitted summary facts (dates, requested days/hours, employee ID, ticket ID) are included.
* **In-Memory Idempotency Store:** Action tokens use cryptographically secure random entropy (`secrets.token_urlsafe(24)`) and `InMemoryActionTokenStore` with thread locking. While this ensures replay protection and idempotency within the process, production deployment will require backed storage (e.g., Redis or Cosmos DB) as planned in ADR-0001.
* **Scope Isolation and Marker Integrity:** Markers `P03` and `P03-T01` are marked completed in `implementation-plan.md`, with earlier tasks `P01-T01` and `P02`/`P02-T01` remaining complete. Container phase `P01` as well as later phases `P04` (SLA timer engine) and `P05` (packaging and marketplace readiness) remain unchecked and appropriately paused.
* **Downstream Integration Readiness:** `handle_manager_action` emits a structured `ManagerActionResult` containing the updated ticket, executed action, audit event, and `EmployeeNotificationEvent`, ready for integration into the agent conversational pipeline and notification services.

## Findings and Proposed Routes

Order findings by severity and impact. If none are supported, state that no substantive findings were identified within the assessed boundary and retain any coverage limitations. Do not create a placeholder finding.

No substantive findings were identified within the assessed boundary. All requirements for Phase P03 (Task P03-T01) meet the acceptance criteria (AC-008, AC-009, AC-010, FR-003, NFR-004, NFR-005, NFR-006, NFR-007, NFR-008, NFR-009, NFR-010, NFR-013, NFR-015) without defects or unhandled regressions. Existing architecture, production policy, and SLA timer gates remain tracked as plan-level blockers for future deployment phases.

## Parent Decision Record

<!-- The selected review worker leaves this section unchanged. The primary review parent owns it. -->

### Current Disposition

* Based on events: `RD-001` through `RD-006`
* Review execution: Complete
* Final outcome: Conformant; Phase P03 (Task P03-T01: Build the manager card and protected action handler) satisfies all functional and non-functional requirements, AC-008, AC-009, and AC-010 pass with 32 passing tests, and no open defects exist within the declared scope
* Finding decisions and next actions: No open RV findings or defects identified; all acceptance criteria met; no remediation actions required for P03-T01
* Decisions still needed: None for bounded P03-T01. Production gates for tenant HR policy approval, ADR-0001 baseline adoption (D2), SLA escalation timing resolution (D1), `Request Information` semantics (D3), and packaging contracts (D4) remain tracked for subsequent phases.

This summary is derived from Decision History, not a second decision record. The latest event for each subject governs; refresh this summary after appending decisions and on recovery.

### Decision History

Append events in order. Never rewrite or delete an earlier row. The latest event for a subject is current.

| Event | Subject | Decision source | Status or value | Proposed destination | Final destination | Owner | More information needed | Smallest next action | Rationale |
|---|---|---|---|---|---|---|---|---|---|
| RD-001 | Review decision participation | User context | `user-owned`; standalone review | None | None | Review parent | None | Compare P03-T01 evidence set | Standalone RPI Review uses user-owned decisions. |
| RD-002 | Review walkthrough | Parent | `not-needed-no-findings` | None | None | Review parent | None | Record final execution and outcome | Zero actionable findings or defects identified in assessed P03-T01 boundary. |
| RD-003 | P03-T01 acceptance and AC proof | Parent | Accepted | None | None | Implementation owner | None | None | Teams Adaptive Card generation with zero leakage (AC-008), protected APPROVE transition with audit and notification (AC-009), mandatory REJECT reason requirement and transition (AC-010), direct-report authorization, status checks, and token replay idempotency verified by 13 unit tests. |
| RD-004 | Scope adherence and isolation | Parent | Accepted | None | None | Implementation owner | None | None | P03 and P03-T01 marked complete; P01-T01 and P02/P02-T01 remain complete; unapproved container phase P01, and phases P04 and P05 remain appropriately unchecked and paused. |
| RD-005 | Final Review execution | Parent | Complete | None | None | Review parent | None | Close review record | Standard-depth evidence review completed by review worker; 32/32 tests passed (including 13 manager card tests); Ruff check and format clean. |
| RD-006 | Final Review outcome | Parent | Conformant | None | None | User / project owner | None | Authorize next phase (P04) | Implementation conforms to PRD and plan requirements without defects or regressions in assessed scope. |

## Validation Evidence

| Command | Scope | Status | Summary |
|---|---|---|---|
| `.venv\Scripts\python.exe -m pytest -v` | Full test suite (`test_domain.py`, `test_policy.py`, `test_manager_cards.py`) | Passed | 32/32 tests passed in 0.45s (13 manager card tests + 10 policy retrieval tests + 9 domain ticket lifecycle tests). |
| `.venv\Scripts\python.exe -m pytest -v tests/test_manager_cards.py` | `P03-T01` manager cards & action handler | Passed | 13/13 tests passed in 0.10s verifying AC-008 zero leakage & certified status, AC-008 summary, AC-009 approval transition, audit event, & notification, AC-010 rejection refusal without reason & rejection transition, direct-report authorization denial, status preconditions, token replay idempotency, token reuse refusal, blank token refusal, raw payload execution, ticket mismatch refusal, and unsupported action refusal. |
| `.venv\Scripts\python.exe -m pytest -v tests/test_domain.py` | `P01-T01` domain ticket lifecycle | Passed | 9/9 tests passed in 0.05s verifying ticket state machine, borrowing ceiling, manager projection privacy, and lifecycle audit actions. |
| `.venv\Scripts\python.exe -m pytest -v tests/test_policy.py` | `P02-T01` policy retrieval & Q&A | Passed | 10/10 tests passed in 0.14s verifying chunking, AC-001 notice citations, AC-002 refusal & escalation, AC-003 conflict handling, and hybrid ranking. |
| `.venv\Scripts\python.exe -m ruff check src tests` | Codebase linting | Passed | All checks passed with 0 errors across 8 files. |
| `.venv\Scripts\python.exe -m ruff format --check src tests` | Codebase formatting | Passed | All 8 files formatted cleanly per Ruff standard. |

## Risks, Blockers, and Residual Work

* Blockers: None for P03-T01 prototype implementation. Production blockers remain documented in the plan: HR policy owner sign-off on authoritative tenant policy and SLA calendar/escalation rules (D1), ADR-0001 architecture adoption (D2), `Request Information` card action definition (D3), and deployment/packaging contracts (D4).
* Remaining active work: Unchecked plan phases: P01 (container phase), P04 (asynchronous SLA timer engine, P04-T01), and P05 (packaging and marketplace readiness, P05-T01).
* Residual work: End-to-end integration with live Microsoft Teams Bot Framework / Cloud Adapter; backing store for action tokens (e.g. Cosmos DB / Redis); formal definition and implementation of `Request Information` workflow when specified by PO.

## Review Record

### Scope and Evidence

* Task ID: hr-time-leave-agent-implementation
* Review date: 2026-10-02
* Review scope: Phase P03 (Task P03-T01: Build the manager card and protected action handler)
* Assessed boundary: P03-T01 sanitized Microsoft Teams Adaptive Card 1.5 generation, protected action handler, direct-report authorization, status preconditions, action token idempotency, APPROVE transition and notification (AC-009), REJECT transition requiring mandatory reason (AC-010), raw Teams payload parsing, and 32 unit tests across domain, policy, and manager cards
* Review depth and provenance: standard; default for RPI Review
* Review worker: general-purpose (RPI Review Builder); selected because no dedicated review subagent is available in workspace
* Builder candidate identity: hr-time-leave-agent-implementation, P03-T01, evidence dated 2026-09-29 / 2026-10-02
* Builder execution: Complete
* Plan: .copilot-tracking/plans/implementation-plan.md
* Plan critique: none
* Changes: .copilot-tracking/changes/2026-09-29/hr-time-leave-agent-implementation-changes.md
* Other evidence considered: .copilot-tracking/prd-sessions/requirements.md (FR-003, NFR-004 through NFR-010, NFR-013, NFR-015, AC-008, AC-009, AC-010); src/hr_time_leave/manager_cards.py; tests/test_manager_cards.py; src/hr_time_leave/domain.py; tests/test_domain.py; src/hr_time_leave/policy.py; tests/test_policy.py

### Opening Review State

* Interpreted review goal: Review the implementation evidence in .copilot-tracking/changes/2026-09-29/hr-time-leave-agent-implementation-changes.md against the plan at .copilot-tracking/plans/implementation-plan.md and the PRD at .copilot-tracking/prd-sessions/requirements.md for Phase P03 (Task P03-T01: Build the manager card and protected action handler). Verify scope adherence, test results (32 passing tests), and proof that AC-008, AC-009, and AC-010 pass.
* Review scope: Phase P03 (Task P03-T01: Build the manager card and protected action handler)
* Evidence readiness: Plan, PRD, changes record, manager cards and action handler (src/hr_time_leave/manager_cards.py), and 32 passing tests in test_domain.py, test_policy.py, and test_manager_cards.py are ready.
* Acceptance basis: PRD FR-003, NFR-004 through NFR-010, NFR-013, NFR-015, AC-008, AC-009, AC-010; Plan P03 and P03-T01 Requirements, Details, and Guidance.
* First comparison boundary: Verify Teams Adaptive Card sanitization and zero-leakage (AC-008); verify direct-report authorization and status checks; verify action token idempotency; verify APPROVE transition with audit and notification (AC-009); verify REJECT refusal without reason and transition with reason (AC-010); verify 32 tests pass; verify scope adherence and isolation from unstarted phases P04-P05.
* Active read-only boundaries: Review worker write authority is limited to the review record except ## Parent Decision Record; no source, plan, critique, research, changes, or state files may be edited
* Authority split: builder owns review evidence and proposed routes; parent owns final outcome, route dispositions, and continuation
* Initial blockers: none

### Acceptance and Change Coverage

| Requirement or scope | Implementation and validation evidence | Assessment | Finding or rationale |
|---|---|---|---|
| Scope Adherence: Phase `P03` / `P03-T01` | Marked `[x] P03` and `[x] P03-T01` in `implementation-plan.md`. `P01-T01` and `P02`/`P02-T01` remain completed. Container phase `P01`, and phases `P04`, `P05` (with their tasks) remain unchecked. | Satisfied | Scope bounded exactly to P03-T01. No unapproved phase execution or out-of-scope code changes. |
| Task `P03-T01`: Sanitized Teams Adaptive Card generation | Implemented `build_manager_approval_card` in `src/hr_time_leave/manager_cards.py`. Generates Adaptive Card 1.5 JSON consuming `Ticket.manager_view()` exclusively. Verified by `test_given_sick_leave_when_card_built_then_zero_leakage_and_certified` and `test_given_annual_leave_when_card_built_then_shows_summary_and_actions`. | Satisfied | Full Adaptive Card structure with permitted facts, privacy notice, Approve action, and Reject action with reason input. |
| `AC-008`: Zero leakage & permitted summary | When manager opens Teams card, shows permitted request summary. For sick leave, displays `CERTIFIED_MEDICAL_LEAVE_STATUS` while withholding timing, duration, medical notes/diagnoses, and employee reasons. For annual leave, displays dates and requested days while omitting reasons and compensation. Verified by `test_given_sick_leave_when_card_built_then_zero_leakage_and_certified` and `test_given_annual_leave_when_card_built_then_shows_summary_and_actions`. | Satisfied | Strict negative leakage verification confirms zero PHI or sensitive compensation details in card payload. |
| `AC-009`: Approve transition, audit, and notification | When manager selects Approve on a pending ticket, transitions to `APPROVED`, records attributable audit event with manager ID and timestamp, and creates `EmployeeNotificationEvent`. Verified by `test_given_manager_when_approving_then_transitions_and_notifies`. | Satisfied | Deterministic transition to APPROVED with full audit attribution and employee notification. |
| `AC-010`: Rejection reason requirement and transition | When manager selects Reject without a reason (empty or whitespace), decision is refused with `RejectionReasonRequiredError` and ticket remains pending. With reason, transitions to `REJECTED`, records reason in ticket and audit event, and notifies employee. Verified by `test_given_manager_rejection_without_reason_then_refuses_decision` and `test_given_rejection_with_reason_then_transitions_and_records`. | Satisfied | Both branches of AC-010 verified: refusal without reason preserves pending state; valid reason executes transition and stores reason. |
| `NFR-005` & `NFR-006`: Server-side direct-report authorization | `handle_manager_action` checks `caller_id == ticket.manager_id`; unauthorized callers are rejected with `ManagerAuthorizationError`. Verified by `test_given_unauthorized_caller_when_action_attempted_then_denies_access`. | Satisfied | Direct-report authorization enforced server-side before any ticket inspection or mutation. |
| `NFR-007`: Ticket status preconditions | Actions on non-`PENDING_APPROVAL` tickets are refused with `TicketNotPendingError`. Verified by `test_given_non_pending_ticket_when_action_attempted_then_rejects`. | Satisfied | Prevents modifying tickets that are already approved, rejected, escalated, or draft. |
| `NFR-004` & `NFR-007`: Idempotent action tokens | `generate_action_token` creates cryptographically random tokens. `InMemoryActionTokenStore` returns cached result on replay (`is_idempotent_replay=True`) without duplicate audit records, notifications, or transitions. Token reuse across tickets is refused with `DuplicateActionTokenError`. Verified by `test_given_identical_token_replayed_then_returns_cached_result_safely`, `test_given_token_reused_for_different_ticket_then_raises_duplicate_error`, and `test_given_blank_action_token_then_rejected`. | Satisfied | Complete idempotency and replay safety preventing duplicate actions or token misuse. |
| `FR-003` & `NFR-015`: Raw card payload handling | `handle_card_action_payload` extracts and validates ticket ID, action token, action, and rejection reason from Microsoft Teams submission payload. Verified by `test_given_raw_card_payload_when_approve_then_succeeds`, `test_given_raw_card_payload_with_mismatched_ticket_then_fails`, and `test_given_unsupported_action_string_then_raises_error`. | Satisfied | Translates untrusted Teams submission payloads safely into validated domain actions. |
| `NFR-008`, `NFR-009`, `NFR-010`: Privacy & data minimization | Manager view explicitly excludes medical details, notes, compensation calculations, and employee reasons. Certification status is shown only when applicable. | Satisfied | Data minimization enforced at both domain projection and card generation layers. |
| `NFR-013`: Auditability | Audit events capture UTC timestamp, actor ID, action (`LifecycleAction.APPROVE` / `LifecycleAction.REJECT`), channel (`msteams`), previous status, and new status. | Satisfied | Attributable lifecycle events recorded for every manager decision. |
| Plan updates & marker hygiene | `implementation-plan.md` checked `[x] P03` and `[x] P03-T01`, added downstream guidance to `P04-T01`, updated Confirmed User Direction, and Planning Readiness. No unapproved changes made to other phases. | Satisfied | Plan reflects actual execution scope and preserves active-phase gates. |
| Code quality & test hygiene | Ruff check (0 errors) and Ruff format (clean) pass. 32/32 tests pass without warnings or regressions. | Satisfied | High codebase hygiene and type adherence across domain, policy, and manager card modules. |

### Critique and Follow-Up Assessment

* Latest critique dispositions: No critique run for the current plan (plan explicitly notes critique is deferred until readiness blockers for production are resolved).
* Material revisions: Plan was updated at implementation time to record the completion of `P03-T01` (and containing phase `P03`), reflect user authorization, and provide guidance for `P04-T01` on consuming transition contracts and manager card states. The scope remained strictly confined to manager card generation and action handling.
* Dependent-work pause assessment: Dependent phases P04 (asynchronous SLA timer) and P05 (packaging & readiness) remain properly paused in `[ ]` uncompleted state. Container phase P01 remains unchecked.
* Justification assessment: Marking P03 and P03-T01 complete is fully justified by the implementation in `src/hr_time_leave/manager_cards.py` and 13 passing unit tests in `tests/test_manager_cards.py`.

| Follow-up item | Why outside immediate scope | Owner or next action | Assessment and route |
|---|---|---|---|
| Complete uncovered ticket rules and tests (overtime, attendance adjustments) | P03 scope is manager approval cards and actions (FR-003, AC-008-010); domain rules belong to P01 extension or production hardening | HR policy owner & product owner | Route to `rpi-plan` / subsequent phase planning before production |
| Define `Request Information` card behavior | Specification does not define ticket state effect, response path, deadline, or audit contract; properly deferred to avoid undefined state | Product owner & HR policy owner | Route to `rpi-plan` prior to enabling `Request Information` in card |
| Resolve durable audit integrity and retention | Cross-cutting production compliance control; outside local unit prototype | Security/privacy & platform owners | Route to `rpi-plan` before P05 deployment |
| Backing store for action token idempotency (Redis/Cosmos DB) | P03 prototype uses thread-safe in-memory store; production multi-instance requires distributed cache/database | Architecture authority & platform owner | Route to `rpi-plan` / P05 cloud deployment preparation |

### Builder Self-Check

* [x] Every supplied requirement, acceptance criterion, in-scope marker, material update, critique disposition, validation result, blocker, remaining item, and plan follow-up has an assessment or explicit gap.
* [x] Findings are substantive, evidence-grounded, severity-graded, and use stable `RV-xxx` IDs with expected and observed behavior, a resolution condition, and one proposed route each.
* [x] Execution status, proposed outcome, validation coverage, limitations, and proposed routes are complete and internally consistent.
* [x] The summary is scoped and advisory, findings keep their supporting context together, and acceptance coverage distinguishes demonstrated gaps from unassessed behavior.
* [x] Standard review completely assessed the material boundary while omitting restatement, cosmetic feedback, exhaustive strengths, low-impact suggestions, and continual narration; deep review remained inside the supplied boundary.
* [x] The selected review worker did not edit Parent Decision Record, ask the user, mutate source or parent state, dispatch another worker, execute validation, or invoke a destination.
* Checked boundary: Scope limited to Phase P03 (Task P03-T01: Build the manager card and protected action handler) in `src/hr_time_leave/manager_cards.py`, `tests/test_manager_cards.py`, and regression validation across `tests/test_domain.py` and `tests/test_policy.py`.
* Missing or limited evidence: Live Microsoft Teams Bot Framework hosting, cloud adapter deployment, Entra ID token verification, and durable distributed token storage are not available in local test environment; validated against Microsoft Teams Adaptive Card 1.5 JSON schema and simulated payload fixtures per plan.

### Builder Execution

* Status: Complete
* Proposed review execution: Complete
* Proposed outcome: Conformant
* Summary: The implementation for Phase P03 (Task P03-T01: Build the manager card and protected action handler) conforms to all functional and non-functional requirements in PRD (`FR-003`, `NFR-004` through `NFR-010`, `NFR-013`, `NFR-015`) and satisfies acceptance criteria `AC-008`, `AC-009`, and `AC-010`. All 32 unit tests pass (13 manager card tests, 10 policy tests, 9 domain tests), Ruff lint and formatting pass with zero defects.
