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
---

## Metadata

* Task ID: `hr-time-leave-agent-implementation`
* Related plan: [`.copilot-tracking/plans/implementation-plan.md`](../../plans/implementation-plan.md)
* Implementation date: 2026-09-29

## Execution Status

* Status: Complete for the declared task scope
* Declared invocation scope: `P01-T01`
* Completed scope markers: `P01-T01`
* All remaining active-plan markers: `P01`, `P02`, `P02-T01`, `P03`, `P03-T01`, `P04`, `P04-T01`, `P05`, and `P05-T01`
* Status basis: The ticket model, schema, deterministic transitions, required validation, manager projection, and scoped tests are implemented and validated. The containing phase and all later work remain outside this invocation.

## Execution Summary

Implemented the caller-authorized Python package for ticket foundation behavior. The package validates tickets against JSON Schema, enforces the annual-leave borrowing ceiling, records attributable lifecycle transitions, and exposes a privacy-minimized manager projection. The implementation uses synthetic test data only and does not claim production policy approval or durable immutable audit storage.

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

## Implementation-Time Plan Updates

### Recording completed scope and downstream contract guidance

* Affected plan area or markers: `P01-T01`, `P03-T01`, `Planning Readiness and Next Step`, `Artifact Self-Check`, and `Handoff`
* What changed: Checked only `P01-T01`, recorded bounded completion and focused validation, and added a `Guidance:` block to `P03-T01` pointing to the shared ticket, manager projection, and transition contracts.
* Why: The caller authorized exactly `P01-T01`; its source APIs are concrete dependencies for the later manager approval handler.
* Triggering evidence: Implemented contracts and passing tests in `src/hr_time_leave/domain.py` and `tests/test_domain.py`.
* User answer or decision: The user authorized creating a Python application package in this repository and limited this invocation to `P01-T01`.
* Reconciliation performed: The plan now distinguishes bounded task completion from the unchecked `P01` phase and later work. Production SLA, architecture, policy, deployment, and publication gates remain unchanged.
* Planning and critique state: No new planning decision or critique was needed; the update preserves the approved scope.

## Validation Record

| Check | Scope | Status | Evidence or reason |
|---|---|---|---|
| Dependency lock and environment sync | `P01-T01` | Passed | `uv lock` and `uv sync` resolved and installed dependencies from public PyPI. A separate `.venv-validation` using Windows CPython 3.11.2 was used because the pre-existing `.venv` interpreter reports a MINGW OS identifier that native Windows `uv` cannot consume; the pre-existing environment was left unchanged. |
| Ticket domain tests | `P01-T01` | Passed | `uv run pytest -q`: seven tests passed. |
| Ruff lint | `P01-T01` | Passed | `uv run ruff check src/hr_time_leave tests/test_domain.py`: all checks passed. |
| Ruff formatting | `P01-T01` | Passed | `uv run ruff format --check src/hr_time_leave tests/test_domain.py`: all files formatted. |
| Public dependency-feed npm script | Dependency metadata | Skipped | No root `package.json` or applicable root npm script exists. The generated `uv.lock` uses `https://pypi.org/simple` and `https://files.pythonhosted.org` sources. |

## Pre-Review Reconciliation

* Plan markers and task-local context: Current. `P01-T01` is checked; `P01` remains unchecked because this was a task-bounded invocation.
* Completed-work evidence and handoff prose: Current. The implementation is limited to the authorized ticket foundation.
* Validation, blockers, remaining work, and follow-up items: Current. Tests, lint, and formatting passed; the plan's existing follow-ups remain unchanged.
* Review readiness: The bounded implementation is ready for review. No broader phase, production, or publication readiness is claimed.

## Blockers

* None for `P01-T01`. Production use remains gated by the synthetic policy and draft requirements, plus unresolved durable audit integrity and retention controls recorded in the plan.

## Remaining Work

* `P01` and all markers for `P02` through `P05` remain outside the caller-declared scope. Do not begin them without authorization; production SLA activation, deployment, and publication remain subject to their recorded owner decisions and gates.

## Follow-Up Items

* Canonical plan list: [`.copilot-tracking/plans/implementation-plan.md`](../../plans/implementation-plan.md), `## Follow-Up Items`
* Existing plan follow-ups remain unchanged: complete the uncovered ticket rules and tests, define `Request Information` behavior, and resolve durable audit integrity and retention.

## Return-to-Caller State

* Implementation execution status: Complete for `P01-T01` only.
* Declared scope and markers: `P01-T01` completed; `P01`, `P02`, `P02-T01`, `P03`, `P03-T01`, `P04`, `P04-T01`, `P05`, and `P05-T01` remain unchecked and outside scope.
* Validation coverage: Seven tests passed; Ruff lint and formatting passed; dependency lock and sync completed.
* Blockers: None for bounded implementation. Production policy, audit, architecture, deployment, and publication gates remain open.
* Current plan updates: Marked the task complete, added downstream API guidance for `P03-T01`, and reconciled readiness and handoff language.
* Planning and critique state: No new critique or material planning decision was required.
* Follow-up items: No new follow-ups; existing plan follow-ups remain current.
* Review readiness or no-handoff reason: `P01-T01` is ready for review; no RPI Review was invoked in this standalone implementation.
* Continuation owner: User.
