<!-- markdownlint-disable-file -->
# Task Research: hr-time-leave-agent

| Field              | Value                                     |
|--------------------|-------------------------------------------|
| Date               | 2026-09-24                                |
| Researcher / agent | rpi-research                              |
| Output mode        | research-only                             |

## Executive Summary

* Bottom line: The evidence describes a highly operational HR workflow in which an AI Copilot agent is intended to answer policy questions and orchestrate time-off, overtime, and attendance tickets under strict enterprise RBAC, SLA, and privacy constraints.
* Why this matters: The process is not just a chatbot scenario; it is a workflow system with approval gates, business-rule enforcement, escalation logic, and high-risk data handling that must be designed around role boundaries and auditability.
* Research status: Complete for the supplied workshop evidence; the result is bounded to the synthetic HR scenario rather than production legal policy or real tenant configuration.
* Confidence and uncertainty: High confidence in the documented process rules and failure cases; moderate confidence in business framing because the source set is intentionally synthetic and not live enterprise policy.

## What You May Not Know

The provided evidence is intentionally synthetic workshop material, not a production HR policy baseline or a live tenant contract. It is strong enough to define the operational target and architecture constraints, but it still leaves open the real-world legal, regional, and connector-specific details that an actual deployment would need to confirm.

## Findings

### HR operations are rule-heavy and SLA-driven, not conversational-only

This scenario is built around a formal workforce process: employees submit time and leave tickets; line managers approve or reject within a 48-business-hour window; abandoned approvals escalate to HR after 72 hours; and each lifecycle state is auditable. The design therefore combines policy Q&A with workflow orchestration rather than stand-alone chat.

* Questions: Q1, Q2, Q3
* Evidence state: evidence-backed finding
* Evidence: C1, C2, C4
* Confidence and limits: High confidence in the stated process model; the workshop context does not verify live staffing, jurisdictional policy variance, or actual integration details.

Supporting detail:
- The SOP defines standard work hours, PTO accruals, overtime multipliers, and the 48-hour manager SLA with escalation to an HR queue after 72 hours.
- The ticket spec codifies an explicit state machine and JSON schema for ticket lifecycle and metadata.
- The process is intentionally designed to reduce manual repetitive HR work while still preserving human approval, escalation, and accountability.

### Affected personas are explicitly segmented by authority and data exposure

The scenario clearly distinguishes three operational roles: Employee, Line Manager, and HR Admin. Each role has different visibility and action rights, which means the agent design must enforce role-based behavior instead of treating all users as equivalent.

* Questions: Q2, Q4
* Evidence state: evidence-backed finding
* Evidence: C2, C3
* Confidence and limits: High confidence in the role model; human organizational nuances beyond the synthetic data are not exposed.

Supporting detail:
- Employees can view and edit their own drafts and cancel their own tickets, but cannot see peer balances or departmental aggregates.
- Line managers can approve or reject only tickets for their direct reports in the org tree.
- HR administrators have tenant-wide visibility into escalations, audit logs, and override capabilities.

### Hard business rules define the AI decision boundary and the failure modes it must handle

The business logic is highly structured: working hours, overtime multipliers, accrual rules, blackout periods, and exception thresholds are all explicit. This creates a clear set of must-handle scenarios for the agent and a narrower set of safe automation opportunities.

* Questions: Q3, Q5
* Evidence state: evidence-backed finding
* Evidence: C1, C4
* Confidence and limits: High confidence in the documented rules; legal or local-policy exceptions outside the synthetic scenario remain open.

Supporting detail:
- Full-time standard week is 40 hours across five 8-hour days; overtime is paid at 1.5x, 2.0x, or 2.5x depending on day and holiday conditions.
- PTO accrual is 1.5 business days per month; advance notice varies by leave duration; blackout periods can restrict discretionary leave.
- Tickets can be rejected if they exceed current balance plus borrowing ceiling, and the workflow warns when requests fall in blackout periods.
- Automatic escalation is triggered after 48 hours without manager action and then after 72 hours to HR triage.

### Known failure cases are not edge cases; they are required decision points for the system

The evidence specifically names operational failure states that the AI and the workflow must handle safely. They are important because they define where the system must block, escalate, or require human intervention rather than guessing.

* Questions: Q5
* Evidence state: evidence-backed finding
* Evidence: C1, C4
* Confidence and limits: High confidence in the listed failure cases; the scenario does not specify all possible enterprise exceptions.

Supporting detail:
- Zero leave balance or an attempt to borrow beyond the three-day ceiling should be rejected.
- Medical leave extending beyond two consecutive business days without certification is not automatically approved and may require proper documentation.
- Manager inactivity beyond the SLA triggers reminder and escalation workflows.
- Unapproved or unauthorized overtime must be prevented or identified as out-of-policy.

### Privacy-preserving RAI and auditability are first-order design constraints

This is a data-sensitive HR workflow with explicit rules for PHI, compensation confidentiality, and immutable audit logging. The AI agent cannot treat these as secondary concerns; they are central to trust and compliance.

* Questions: Q4, Q5
* Evidence state: evidence-backed finding
* Evidence: C2, C3, C5
* Confidence and limits: High confidence in the stated privacy controls; deployment will still require a real security review and policy mapping for actual tenant data and retention requirements.

Supporting detail:
- Medical reasons and uploaded notes must never be exposed to line managers or team channels; only a general approved status may be shown.
- Overtime monetary calculation must not be exposed to unauthorized roles or kept in cleartext LLM transcripts.
- Every ticket lifecycle action must append an immutable audit record containing timestamp, actor identity, action, channel, and state transitions.

### Open assumptions and technical dependencies remain for the Architect

The synthetic evidence gives a strong functional picture, but several technical dependencies must still be confirmed before implementation or production rollout. These are the main design assumptions to validate in the next architecture step.

* Questions: Q6
* Evidence state: partially supported claim
* Evidence: C2, C3, C5
* Confidence and limits: Moderate confidence, because required connector contracts, tenant identity integration, and region-specific policy variations remain unspecified.

Supporting detail:
- Real integrations are assumed with HRIS / ERP systems, Microsoft Graph, Teams notifications, and a time-clocking engine, but their exact APIs and data contracts are not provided.
- The architecture likely needs a secure workflow layer, policy engine, audit store, and guardrail layer; this scenario does not yet specify the deployment topology.
- The results are sufficient to scope a design target, but not enough to finalize a production-ready implementation plan.

## Recommendation and Alternatives

* Recommendation or decision state: Proceed with a policy-constrained, role-aware HR workflow agent that combines conversational guidance with governed ticket orchestration and human approval controls, rather than a fully autonomous leave or overtime decision engine.
* Rationale: The strongest evidence supports a bounded agent design with explicit RBAC, immutable audit logging, escalations, and controlled disclosure. This matches the documented process and reduces risk to both employee experience and compliance.
* What could change this result: A live HRIS contract, legal policy review, specific Microsoft 365 tenant security model, or regional policy variants could narrow or alter the final architecture.

| Option       | Benefits     | Costs and risks     | Evidence  | Disposition                           |
|--------------|--------------|---------------------|-----------|---------------------------------------|
| Constrained workflow agent | Strong governance, lower compliance risk, clear approval paths | Requires integration, policy modeling, and audit design | C1, C2, C3, C4 | selected |
| Fully autonomous policy decisioning | Faster operational throughput | Higher risk of policy violations, privacy leaks, and invalid approvals | C1, C3 | rejected |
| Chat-only policy assistant | Simple user experience | Insufficient for approval, audit, and escalation workflow requirements | C1, C2 | rejected |

## Scope and Questions

* Goal: Synthesize the verified HR scenario into a grounded architecture and product understanding for an enterprise adaptive HR and time-management Copilot agent.
* Audience and use: Architects, product owners, and delivery teams who need the operational constraints, personas, rules, and failure modes before solution design.
* In scope: Employer policy framework, ticket lifecycle, role-based authorization, privacy restrictions, escalation logic, and explicit business rules from the supplied evidence.
* Out of scope: Real employee contracts, legal payroll policy, actual vendor APIs, tenant-specific identity setup, and live production data or claims beyond the synthetic workshop materials.
* Decision and evidence criteria: Use only the supplied workshop evidence and identify any assumption or technical dependency that remains unverified.
* Requested output: research-only synthesis for architecture framing and planning readiness.

| ID | Question                | Source                   | Status                    |
|----|-------------------------|--------------------------|---------------------------|
| Q1 | What are the core business facts and operational realities? | synthetic workshop evidence | answered |
| Q2 | Which personas and role boundaries matter? | synthetic workshop evidence | answered |
| Q3 | What business rules and hard constraints govern the process? | synthetic workshop evidence | answered |
| Q4 | What are the known failure cases and privacy constraints? | synthetic workshop evidence | answered |
| Q5 | What RAI and audit requirements must the design satisfy? | synthetic workshop evidence | answered |
| Q6 | What assumptions and dependencies remain for the Architect? | synthetic workshop evidence | answered |

## Decisions and Feedback

| Group  | Decision or feedback item | Status                                                     | Owner                                         | Rationale or input needed          | Evidence  | Impact of answer                  |
|--------|---------------------------|------------------------------------------------------------|-----------------------------------------------|------------------------------------|-----------|-----------------------------------|
| D1 | Use a bounded workflow agent rather than fully autonomous approval logic. | confirmed | agent | Human approval gates and auditability are embedded in the SOP and lifecycle model. | C1, C2, C3 | High; it preserves policy compliance and trust. |
| D2 | Treat PHI and compensation data as high-sensitivity design inputs. | confirmed | agent | Privacy and compensation rules are explicitly stated and must not be treated as optional. | C3 | High; it drives the security model and log design. |
| D3 | Keep the architecture assumption-driven until real tenant and connector contracts are validated. | confirmed | agent | The synthetic evidence supports scope; the actual implementation depends on APIs and org hierarchy details. | C2, C3, C5 | Medium; it sets the architecture readiness gate. |

## Risks and Open Questions

| Priority  | Type                                    | Risk, question, or research item | Impact     | Smallest action or evidence needed | Owner                        |
|-----------|-----------------------------------------|----------------------------------|------------|------------------------------------|------------------------------|
| High | risk | Regional or local HR policy variance may supersede the synthetic rules. | High | Confirm actual local policy mappings and exceptions before deployment. | downstream |
| High | risk | Real HRIS / ERP connector contracts and org hierarchy APIs are not yet defined. | High | Validate Workday/SAP/BambooHR and Microsoft Graph integration contracts. | downstream |
| High | open question | How will medical-note redaction and compensation masking be enforced in the AI platform and logs? | High | Validate LLM and telemetry controls, document retention, and redaction rules. | downstream |
| Medium | risk | Manager and HR notification flows may miss the required SLA or queue routing in production. | Medium | Define Teams/webhook routing, retries, and escalation logic with SLA monitoring. | downstream |
| Medium | further research | The real enterprise architecture topology and security boundaries are still unspecified. | Medium | Confirm Azure hosting pattern, identity model, and data flow boundaries. | downstream |

## Planning Readiness and Next Step

| Field                            | Record                                                                                          |
|----------------------------------|-------------------------------------------------------------------------------------------------|
| Research disposition             | executed                                                                                       |
| Decision participation           | agent-owned; research-only synthesis based on the supplied synthetic evidence and no user decision gate was required |
| Planning Readiness               | Not ready for implementation; enough to scope the solution and architecture risks, but not enough to finalize production design |
| Research depth and lanes         | Single focused cycle completed across business rules, personas, failure states, and RAI constraints |
| Blockers                         | None in the supplied evidence; real-world connector and policy validation remain external prerequisites |
| Output mode and planning support | research-only; supports architecture framing and early solution scoping, but not execution-ready implementation |
| Continuation owner               | manual RPI Agent or downstream architect                                                       |
| Required gates or confirmations  | Pending validation of real HRIS, Graph, Teams, and security requirements before implementation |
| Next action                      | Use this artifact as the authoritative evidence base for architecture design and confirm connector, policy, and tenant assumptions before implementation |
| Primary evidence file            | .copilot-tracking/research/2026-09-24/hr-time-leave-agent-research.md                             |

## Research Record

### Method and Boundaries

| Field                            | Record                                                                 |
|----------------------------------|------------------------------------------------------------------------|
| Research posture and provenance  | focused; task-supplied evidence and repository tracking conventions |
| Completion basis                 | The task was bounded to the provided workshop evidence and did not require external verification beyond the stated artifacts. |
| Explicit limits or deadline      | No external legal, HR, or tenant validation was requested or available; the result is bounded to the workshop scenario. |
| Codebase and external scope      | Internal workspace research only; no external web or live-system validation performed. |
| Initial candidate areas          | HR SOP, ticket lifecycle specification, product/market lean canvas, workflow design assumptions |
| Evidence root                    | .copilot-tracking/research/workshop-input |
| Constraints and excluded sources | no live HR systems, no tenant-specific security review, no production payroll or policy sources |
| Prior knowledge                  | The research builds directly from the supplied SOP, ticket spec, and lean canvas without broad external sourcing. |

### Extensions and Participation

#### Extension Registry

| Kind                             | Candidate        | Provenance and scoped contract | Selected or skipped reason     |
|----------------------------------|------------------|--------------------------------|--------------------------------|
| instruction | .github/instructions/hve-core/copilot-tracking.instructions.md | tracking and write-boundary conventions for .copilot-tracking artifacts | selected |
| instruction | .github/skills/rpi/rpi-research/references/research.md | three-wave evidence and artifact protocol for rpi-research | selected |
| instruction | .github/skills/rpi/rpi-research/templates/research.md | primary-artifact structure and required sections | selected |
| skill | rpi-research | research synthesis across bounded evidence set | selected |

#### Direction and Participation Log

| Checkpoint or change          | Question, direction, or rationale | Answer or no-interaction reason | Result and revalidation effect |
|-------------------------------|-----------------------------------|---------------------------------|--------------------------------|
| intake | Define the task boundary and evidence set. | The user supplied the specific HR SOP, ticketing spec, and lean canvas files. | Research proceeded along the supplied evidence path and remained bounded to it. |
| no-interaction | No user decision gate was required; the task was to synthesize evidence. | No additional clarification was necessary for a bounded research artifact. | The output remains in research-only mode and does not imply implementation direction beyond the evidence. |

### Research Cycle Log

#### Cycle 1

* Active posture, controls, and limits: focused posture; evidence is tightly bounded to the workshop materials and no external validation was used.

##### Wave 1: Wider

* Focus and lanes: Business facts, process flow, and role boundaries from the SOP and ticketing specification.
* Evidence or worker pointers: internal read of the supplied SOP and ticket spec; no subagent used.
* Reflection: The evidence strongly supports a workflow-driven scenario with clear approval and escalation rules.

##### Wave 2: Deeper

* Focus and lanes: Hard constraints, failure modes, privacy rules, and architecture assumptions.
* Evidence or worker pointers: internal read of SOP sections on overtime, PTO, RBAC, privacy, and audit requirements; no subagent used.
* Reflection: The process rules are specific and safety-critical; the main uncertainty is the missing real connectors and tenant settings.

##### Wave 3: Contrarian

* Focus and lanes: Challenge assumptions around autonomy, stressful edge cases, and what the synthetic evidence does not establish.
* Evidence or worker pointers: internal review of the same materials with emphasis on missing real-world dependencies and open technical assumptions.
* Reflection: The process is robust enough for scenario framing, but not enough for a production implementation commitment.

##### Parent Synthesis and Re-entry

| Material or claim | Evidence or worker pointers | Disposition                    | Rationale     | User-facing effect          |
|-------------------|-----------------------------|--------------------------------|---------------|-----------------------------|
| The scenario is workflow-controlled and governed by policy rules. | C1, C2, C4 | accepted | The evidence consistently defines formal workflow stages, service levels, and decision conditions. | High-confidence business and operational grounding. |
| Privacy and compensation restrictions are core design constraints. | C3, C5 | accepted | Explicit PHI and compensation guardrails are provided in the SOP and lean canvas. | Prevents unsafe AI disclosure and design shortcuts. |
| Real HRIS/ERP and tenant dependencies remain unverified. | C2, C3, C5 | deferred | The synthetic evidence provides the target workflow but not the actual production data contracts or platform configuration. | Architect must validate before implementation. |

* Another complete three-wave cycle needed: no
* Trigger or stop basis: The bounded evidence set is sufficient for the stated research objective; remaining gaps are architectural validation items rather than missing scenario facts.
* Readiness or revalidation effect: Planning readiness is limited to design scoping, not production implementation.

### Evidence Log

* Delegation: inline: no research subagent was required; the task was directly answerable from the supplied scenario and tracking files.

| ID | Claim or finding | Source or location                                | Retrieved and version      | Tool                   | Confidence       | Notes       |
|----|------------------|---------------------------------------------------|----------------------------|------------------------|------------------|-------------|
| C1 | HR workflow is governed by explicit manager SLA and escalation logic. | .copilot-tracking/research/workshop-input/policies/sop-hr-time-and-leave.md#5.1 Ticket Submission Workflow and #5.2 Service Level Agreements for Managers | not applicable | read | high | This is the core service-level operational fact set. |
| C2 | Ticket lifecycle and schema define the process model and data contract. | .copilot-tracking/research/workshop-input/sops/ticketing-process-spec.md#1. Ticket Lifecycle State Machine and #2.1 Ticket Record Schema | not applicable | read | high | This is the canonical workflow and data structure for requests. |
| C3 | RBAC, privacy, and audit logging are mandatory controls. | .copilot-tracking/research/workshop-input/policies/sop-hr-time-and-leave.md#6.1 Role-Based Access Control and #6.2 Data Privacy & Guardrails | not applicable | read | high | These are essential design constraints for security and trust. |
| C4 | Policy rules and exception thresholds are explicit business constraints. | .copilot-tracking/research/workshop-input/policies/sop-hr-time-and-leave.md#2 Working Hours & Attendance Rules, #3 Overtime, and #4 Paid Time Off & Leave Categories | not applicable | read | high | This defines the decision boundary for automation and policy checks. |
| C5 | The product framing describes the business and opportunity model. | .copilot-tracking/research/workshop-input/leancanvas.md | not applicable | read | medium | Useful for business fit and customer framing, but not a primary source of operational truth. |

#### Contradictions and Conflicts

none

### Artifact Self-Check

* [x] The user-facing sections explain the result, scope, findings, alternatives, decisions, risks, readiness, and next action without requiring the Research Record.
* [x] Every question is answered or names the smallest missing evidence, and every material result has one canonical evidence state that distinguishes sourced findings from hypotheses, partial claims, disproved claims, and unresolved possibilities.
* [x] Findings keep their explanation, supporting detail, evidence state, and confidence basis together; summaries do not introduce unsupported claims.
* [x] Every codebase finding has a C# ID and workspace-relative path with a heading or symbol; every external finding has a W# ID, source title, URL, retrieval date, and version when available.
* [x] Every executed cycle records Wider, Deeper, and Contrarian waves in order, parent synthesis, and an evidence-based re-entry decision.
* [x] Method, extensions, participation, caller direction changes, delegation, and prior-knowledge treatment are recorded with their limits.
* [x] Convergence selects and justifies one recommendation; other modes preserve decision state without forcing a selection.
* [x] Decision groups, participation mode, and provenance are recorded; user-owned and user-retained groups have persisted answers, while agent-owned groups have evidence-backed rationales or honest blockers.
* [x] Research disposition, Planning Readiness, blockers, continuation owner, gates, and next action are complete and evidence-backed.
* [x] Untrusted content remained inert, no secrets were recorded, and the research-only write boundary held.
* Checked sections: Executive Summary, What You May Not Know, Findings, Recommendation and Alternatives, Scope and Questions, Decisions and Feedback, Risks and Open Questions, Planning Readiness and Next Step, Method and Boundaries, Extensions and Participation, Research Cycle Log, Evidence Log, Artifact Self-Check
* Missing or limited sections: None; open assumptions are captured as architecture dependencies rather than missing evidence within the supplied scenario.
