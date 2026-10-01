<!-- markdownlint-disable-file -->
# Review: HR Time and Leave Agent Implementation

## Executive Summary

Standard-depth review of bounded task `P01-T01` is complete. The ticket-domain boundary is appropriately limited to the authorized foundation work: it models all four ticket types, validates its schema, permits the intended draft-to-pending path, enforces the three-day annual-leave ceiling, and tests both rejection outcomes. Parent-provided independent validation passed all seven tests.

Two substantive gaps prevent the builder from proposing a conformant outcome: the lifecycle event lacks the explicit action required by `NFR-013`, and the reusable manager projection exposes sick-leave request details without representing or enforcing the PRD's certification-only manager disclosure constraint. Proposed builder execution is `Complete`; proposed outcome is `Defects found`. The unchecked `P01` phase, Teams integration, authorization, durable audit storage, and production gates remain outside this invocation and are not accepted by this assessment.

## What You May Not Know

The pass result demonstrates the seven supplied domain tests, not authenticated conversational submission, Teams delivery, direct-report authorization, idempotent action tokens, persistence, or an immutable/tamper-evident audit store. The plan deliberately leaves those concerns to later work or recorded production gates.

## Findings and Proposed Routes

### RV-001 — High: Lifecycle audit event omits the required action field

* **Binding requirement:** `P01-T01` requires the lifecycle audit fields from `NFR-013`; `NFR-013` requires an actor ID, action, client channel, UTC timestamp, previous state, and new state for every lifecycle event.
* **Expected behavior:** Each transition has an explicit recorded action in addition to the state change, so the audit record satisfies the declared contract without inference.
* **Observed behavior and evidence:** `src/hr_time_leave/domain.py` creates `LifecycleEvent` with `actor_id`, `channel`, UTC-normalized `occurred_at`, `previous_status`, `new_status`, and an optional rejection reason. It has no action field or action value. `tests/test_domain.py` asserts selected state/audit fields but does not assert an action. The task correctly makes no claim that the in-memory tuple is immutable.
* **Impact:** A consumer cannot reliably meet the explicit `NFR-013` action-record requirement from this event alone; future audit storage or integrations would need to infer an action from the target state.
* **Checkable resolution condition:** The domain audit contract records an explicit action for every accepted transition, and focused tests assert it for submission and manager decision transitions. Durable immutability/tamper evidence remains a separately scoped production gate.
* **Proposed route:** `rpi-implement` for a later bounded remediation of the `P01-T01` audit contract.

### RV-002 — High: Manager projection does not enforce the certification-only sick-leave disclosure boundary

* **Binding requirement:** `NFR-008` and the RAI guardrail require managers and team channels to receive only permitted certification status for PHI-sensitive medical leave; the supplied SOP says managers only see “Certified Medical Leave Approved by HR.” `P01-T01` requires manager-facing projections to keep medical details and restricted compensation out.
* **Expected behavior:** A manager projection for medical/sick leave is limited to the approved certification status and does not expose additional sick-leave request details unless an approved policy expressly permits them.
* **Observed behavior and evidence:** `Ticket.manager_view()` in `src/hr_time_leave/domain.py` returns the same allowlist for every ticket type: `ticket_type`, `status`, start/end dates, requested leave days, and requested hours. It has no certification-status field or ticket-type-specific disclosure rule. `tests/test_domain.py` proves that diagnosis, notes, employee reason, compensation amount, and the nested sensitive object are omitted, but it exercises an annual-leave ticket only.
* **Impact:** The allowlist prevents the tested direct leaks but does not satisfy the precise medical-leave disclosure constraint; a future manager card that reuses the documented `P03-T01` guidance would expose sick-leave category and timing/quantity details without a certification gate.
* **Checkable resolution condition:** The manager-facing contract explicitly represents approved certification status and prevents a sick-leave projection from emitting non-permitted details; focused sick-leave negative-leakage tests verify that behavior. Any approved exception is documented by the accountable privacy/policy owner.
* **Proposed route:** `rpi-implement` for a later bounded privacy-projection remediation, with `rpi-research` only if the policy owner cannot determine the permitted field set.

## Parent Decision Record

### Current Disposition

* Based on events: `RD-001` through `RD-005`
* Review execution: Complete
* Final outcome: Defects found; two accepted High-severity findings remain for later work
* Finding decisions and next actions: `RV-001` accepted for later `/rpi-implement`; `RV-002` accepted for later `/rpi-implement`, with `/rpi-research` first only if policy owners cannot clarify permitted fields
* Decisions still needed: None

### Decision History

| Event | Subject | Decision source | Status or value | Proposed destination | Final destination | Owner | More information needed | Smallest next action | Rationale |
|---|---|---|---|---|---|---|---|---|---|
| RD-001 | Review decision participation | User context | `user-owned`; standalone review | None | None | Review parent | None | Compare the bounded evidence set | Standalone RPI Review uses user-owned decisions. |
| RD-002 | `RV-001` route disposition | User | Accepted | `rpi-implement` | Later `rpi-implement` | User / implementation owner | None | Carry explicit action-field gap into a later implementation task | The user accepted the builder's route; no source change is authorized by this review. |
| RD-003 | `RV-002` route disposition | User | Accepted | `rpi-implement`; conditional `rpi-research` | Later `rpi-implement`; use `rpi-research` first only if policy owners cannot clarify allowed fields | HR/privacy policy owners and implementation owner | Clarify permitted medical-leave fields only if existing policy is insufficient | Track certification-only projection gap for a later implementation task | The user accepted the suggested route while preserving a research gate only if the policy boundary is unclear. |
| RD-004 | Final Review execution | Parent | Complete | None | None | Review parent | None | Close bounded `P01-T01` evidence review | The reserved builder completed one standard-depth comparison and parent resolved every actionable finding route. |
| RD-005 | Final Review outcome | Parent | Defects found | None | None | User / implementation owner | None | Carry accepted `RV-001` and `RV-002` routes to later work | Two High findings remain in the implemented task boundary, so the result is not conformant. |

## Validation Evidence

| Command | Scope | Status | Summary |
|---|---|---|---|
| `uv run --frozen --python C:\Users\ADMIN\AppData\Local\Programs\Python\Python311\python.exe pytest -q` | Root package and `tests/test_domain.py` | Passed | Independently rerun using temporary `.venv-review` synced from `uv.lock`; 7 tests passed. |

## Risks, Blockers, and Residual Work

* **Blockers:** None for completing this evidence review. The two findings require parent route decisions; neither authorizes continuation into another plan marker.
* **Unassessed production integration:** Authentication, Entra/direct-report authorization, transient-retry behavior, time-bounded/idempotent Teams actions, notifications, persistence, and immutable/tamper-evident storage are not implemented or tested at this `P01-T01` domain boundary. This is a scope limit, not a demonstrated defect in the bounded code.
* **Residual work retained separately:** The plan's existing follow-ups remain: authoritative overtime/attendance/remaining leave and certification rules and tests; `Request Information` semantics; audit tamper-evidence, retention, and operational metric ownership. Production-policy, SLA/calendar, architecture, deployment, and package gates remain with their named owners.
* **Phase status:** `P01` remains unchecked and is outside this task invocation; no phase completion is proposed.

## Review Record

### Scope and Evidence

* Task ID: `hr-time-leave-agent-implementation`
* Review date: 2026-09-29
* Review scope: Bounded task `P01-T01`
* Assessed boundary: Task requirements, cited PRD requirements and acceptance criteria, implementation evidence, and the corresponding domain, schema, and test files.
* Review depth and provenance: Standard; default for RPI Review.
* Review worker: RPI Review Builder; selected because its role constructs one complete RPI review record from bounded planning and implementation evidence.
* Builder candidate identity: `hr-time-leave-agent-implementation`, `P01-T01`, implementation evidence dated 2026-09-29.
* Builder execution: `Complete`; evidence comparison finalized by the reserved builder.
* Plan: `.copilot-tracking/plans/implementation-plan.md`
* Plan critique: No task-specific plan critique artifact exists.
* Changes: `.copilot-tracking/changes/2026-09-29/hr-time-leave-agent-implementation-changes.md`
* Other evidence considered: `.copilot-tracking/prd-sessions/requirements.md`; `src/hr_time_leave/domain.py`; `src/hr_time_leave/schemas/ticket.schema.json`; `tests/test_domain.py`; `pyproject.toml`; `uv.lock`.

### Opening Review State

* Interpreted review goal: Independently verify the bounded implementation scope, evidence and tests for AC-004, AC-005, and AC-010, and privacy minimization of the manager projection.
* Review scope: `P01-T01` only; the containing phase and subsequent tasks are not under review.
* Evidence readiness: Plan, changes record, PRD, implementation, schema, and tests are available. The changes record reports seven passing tests, and an independent test run also passed all seven.
* Acceptance basis: `P01-T01` Requirements in the plan; PRD `FR-002`, `FR-003`, `NFR-008` through `NFR-010`, `NFR-013`, `AC-004`, `AC-005`, and `AC-010`.
* First comparison boundary: Compare the scoped task requirements to the implementation and tests; verify the reported test result. Production persistence, Teams integration, identity authorization, telemetry, and other phases are outside this task's implemented boundary.
* Active read-only boundaries: Compare supplied plan, PRD, changes evidence, domain, schema, tests, and validation only. The review worker may edit this review record except `## Parent Decision Record`; no source, plan, critique, research, changes, or state files may be changed.
* Authority split: Builder owns review evidence and proposed routes; parent owns final outcome, route dispositions, and continuation.
* Initial blockers: None.

### Acceptance and Change Coverage

| Contract or marker | Evidence compared | Assessment |
|---|---|---|
| `P01-T01` scope marker and task goal | Plan task marker; changes record; `domain.py`; package/test files | Met as a bounded ticket-domain and test implementation. Only `P01-T01` is checked; the changes record consistently leaves `P01` and later markers outside scope. |
| Four ticket categories and deterministic lifecycle | `TicketType`, `TicketStatus`, `_ALLOWED_TRANSITIONS`, schema | Met for representation and transition boundary. `DRAFT` can become `PENDING_APPROVAL`; pending tickets can be approved, rejected, escalated, or cancelled; terminal transitions are refused. Unsupported overtime/attendance rules were not invented. |
| `FR-002` / AC-004 | `submit_ticket`, schema, valid annual-leave test | Domain evidence supports valid annual leave becoming `PENDING_APPROVAL` and preserving its ticket ID/required schema fields. Authenticated conversational collection, notice validation, and external balance identity are outside this task boundary. |
| `FR-002` / AC-005 | borrowing-ceiling rule and over-ceiling test | Met for the scoped annual-leave rule: a request beyond accrued balance plus three days raises a descriptive rule violation before a transition, leaving the input immutable. |
| `FR-003` / AC-010 | `transition_ticket` and the two rejection tests | Met for the scoped transition contract: blank/missing reasons are refused; a non-empty supplied reason produces `REJECTED` and is retained in the audit event. Teams action/authentication/notification remain P03 work. |
| Malformed payloads and invalid transitions | schema validation; unknown-field and terminal-transition tests | Met locally. JSON Schema rejects unknown top-level fields, and invalid terminal changes raise before an updated ticket is returned. |
| `NFR-004` through `NFR-007` | task allocation, code, plan boundaries | Only the local invalid-transition boundary is evidenced. Safe external retries, user-visible status, Entra authentication, direct-report authorization, and idempotent action tokens are unassessed later-phase/integration work, not claimed as passed. |
| `NFR-008` through `NFR-010` manager/privacy boundary | schema, `manager_view`, privacy test, PRD and supplied SOP | Directly sensitive fields are omitted and unknown fields are rejected, supporting minimization. `RV-002` records the unsupported certification-only medical-leave projection. |
| `NFR-013` audit boundary | `LifecycleEvent`, transition code, tests | Actor, channel, UTC normalization, previous and new status are present. `RV-001` records the missing explicit action. In-memory events are not represented as immutable/tamper-evident storage, consistent with the plan's retained production gate. |
| `P03-T01` implementation-time Guidance | P03 Guidance block and current public domain interfaces | Concrete and accurate as a dependency handoff: it names `Ticket`, `manager_view()`, `transition_ticket()`, and `TicketStatus`, and describes the provided audit metadata. It does not prematurely claim P03 authorization, Teams host validation, or production privacy compliance. `RV-001` and `RV-002` should be resolved before relying on that guidance for an approved production-facing manager card. |
| Dependency metadata | `pyproject.toml`, `uv.lock` | Consistent: Python 3.11 package uses bounded `jsonschema`, `pytest`, and `ruff` dependencies; lockfile includes the editable project and resolved packages. |

### Critique and Follow-Up Assessment

* Latest critique dispositions: No task-specific critique was run; the plan records that it is partial and not production-ready.
* Material revisions: The changes record marks only `P01-T01` complete and adds `P03-T01` reuse guidance. This is a descriptive, evidence-backed handoff update, not a new planning decision or phase expansion.
* Dependent-work pause assessment: Appropriate. P03, P04, P05, and the unchecked P01 phase remain paused and separately authorized; the changes record does not claim production readiness.
* Justification assessment: The update links later manager work to concrete domain interfaces and retains the plan's synthetic-policy, privacy, audit, SLA, architecture, and deployment gates. The two defects above qualify the manager-projection and audit aspects of that reuse guidance.

| Follow-up item | Why outside immediate scope | Owner or next action | Assessment and route |
|---|---|---|---|
| Overtime, attendance, remaining leave, certification, and HR-admin rules/tests | Authoritative rules were deliberately unavailable to this domain task; the task must not invent them. | HR policy and product owners define approved rules and tests. | Retained distinct plan follow-up; not converted into a P01-T01 defect. |
| `Request Information` workflow | Its state, response path, deadline, and audit contract are unspecified. | Product and HR policy owners before P03 enables it. | Retained distinct P03 follow-up; no finding against the present transition API. |
| Audit tamper evidence, retention, and operations ownership | The task expressly excludes a production immutable store. | Security/privacy and platform owners select and verify controls. | Retained production gate; separate from `RV-001`, which concerns the local explicit-action field. |

### Builder Self-Check

* Read boundary completed once: plan `P01`/`P01-T01`, P03 guidance, readiness, risks, critique, follow-ups, and handoff; the cited PRD contracts and guardrails; the changes record; domain, schema, tests, dependency files; and the supplied SOP privacy/audit constraint needed to interpret the PRD.
* AC-004, AC-005, and AC-010 are separately identifiable in the acceptance table; both rejection paths are assessed.
* Findings are limited to two observed, requirement-bound gaps. Missing external/integration evidence is recorded as a scope limit rather than treated as proof of a defect.
* Proposed execution status: `Complete`.
* Proposed outcome: `Defects found`.
* Proposed routes: `RV-001` → later `rpi-implement`; `RV-002` → later `rpi-implement` (or `rpi-research` only if the policy owner cannot supply a permitted medical-leave field set).
* Limitation: Parent-provided test validation was recorded without rerunning it. The builder did not execute validation, edit source artifacts, or choose final decisions.
* Parent decisions needed: disposition and destination of `RV-001` and `RV-002`; no decision is requested for separately retained production gates or the unchecked phase.

### Builder Execution

Review worker reservation was persisted before dispatch. Candidate: `hr-time-leave-agent-implementation`, scope `P01-T01`, implementation evidence dated 2026-09-29. Depth: standard, default. Dispatch availability: available.

Terminal builder execution: `Complete`.

* Proposed execution status: `Complete`.
* Proposed outcome: `Defects found`.
* Validation coverage: Parent-provided independent command `uv run --frozen --python C:\Users\ADMIN\AppData\Local\Programs\Python\Python311\python.exe pytest -q` passed all seven tests using temporary `.venv-review` synchronized from the public-source `uv.lock`. Code and test evidence were also inspected for the claimed acceptance behavior; Ruff results are recorded only as changes-record evidence.
* Findings: 2 High (`RV-001`, `RV-002`).
* Proposed routes: `RV-001` → later `rpi-implement`; `RV-002` → later `rpi-implement`, conditionally `rpi-research` if policy interpretation is needed.
* Evidence gaps and limitations: no task-specific critique exists; no production integration, persistence, or durable audit-control validation was supplied, and those boundaries were not expanded.
* Boundary confirmation: this review record was the only written artifact.
