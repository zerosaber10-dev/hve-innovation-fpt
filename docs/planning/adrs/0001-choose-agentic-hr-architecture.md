---
id: "0001"
title: "Choose the Agentic HR Architecture"
status: proposed
proposed_date: 2026-09-28
accepted_date: null
deciders:
  - "Architecture/design authority"
consulted:
  - "Security/privacy"
  - "Platform engineering"
informed:
  - "HR"
  - "Product leadership"
  - "Engineering leadership"
tags:
  - architecture
  - hr
  - agentic-system
supersedes: null
superseded-by: null
related: []
asr_triggers:
  - kind: security
    evidence: "SOP-HR-042 sections 6.1-6.2; PRD NFR-005 through NFR-010"
    note: "The architecture determines authentication, authorization, trust boundaries, and handling of confidential medical and compensation data."
  - kind: compliance
    evidence: "SOP-HR-042 section 7.2; PRD NFR-013"
    note: "Internal policy requires attributable lifecycle auditing and constrained handling of sensitive HR information; actual jurisdictional obligations remain unverified."
  - kind: performance
    evidence: "PRD NFR-001"
    note: "The selected orchestration, model, and retrieval path must meet p95 under 3 seconds at nominal load, excluding unavailable external-system waits."
  - kind: availability
    evidence: "PRD NFR-002 through NFR-004"
    note: "The architecture affects monthly availability and timely, duplicate-safe processing of reminder and escalation jobs."
success_criteria:
  - metric: "Unauthorized access or sensitive-field disclosure in the pre-production security and privacy test suite"
    target: "0 successful unauthorized accesses or disclosures"
    measurement_window: "Each release candidate before production"
    source: "SOP-HR-042 sections 6.1-6.2; PRD NFR-005 through NFR-010"
  - metric: "Ticket lifecycle events with required actor, action, channel, and state-transition audit data"
    target: "100% of lifecycle events"
    measurement_window: "All lifecycle events in the pre-production end-to-end test suite"
    source: "SOP-HR-042 section 7.2; PRD NFR-013"
  - metric: "User-visible policy and ticket-interaction response latency at p95 under nominal load"
    target: "Under 3 seconds, excluding unavailable external-system waits"
    measurement_window: "Nominal-load performance test for each release candidate"
    source: "PRD NFR-001"
  - metric: "Production service availability"
    target: "99.9% monthly, excluding approved maintenance"
    measurement_window: "Monthly production reporting period"
    source: "PRD NFR-003"
affected_components:
  - "Microsoft Teams and Azure Bot Service"
  - "Microsoft Entra ID delegated authentication"
  - "Azure App Service hosting LangGraph and internal MCP"
  - "Azure AI Foundry model deployments and content moderation"
  - "Azure AI Search and Azure Storage policy indexing"
  - "Cosmos DB ticket/audit and conversation-memory stores"
  - "Enterprise HRIS and Microsoft Graph MCP connectors"
  - "Azure Service Bus and Azure Functions SLA processing"
---

## Context

The enterprise HR Copilot combines policy-grounded answers with a controlled time-and-leave ticket lifecycle. The supplied architecture blueprint proposes Azure services and integration boundaries, but no infrastructure code, production workload measurements, or live tenant contracts were supplied. The selected stack is a planned baseline for review, not evidence of a deployed or production-approved system.

> "Line Managers must take action (`APPROVE`, `REJECT`, or `REQUEST_INFO`) within **48 business hours** of ticket creation."
>
> Source: SOP-HR-042, section 5.2, `.copilot-tracking/research/workshop-input/policies/sop-hr-time-and-leave.md`.

> "Diagnostic details, doctor notes, and medical justifications are strictly confidential."
>
> Source: SOP-HR-042, section 6.2, `.copilot-tracking/research/workshop-input/policies/sop-hr-time-and-leave.md`.

> "Policy answers and ticket interaction responses shall complete at p95 within 3 seconds under nominal load, excluding time waiting for unavailable external systems."
>
> Source: PRD-HR-TIME-001, NFR-001, `.copilot-tracking/prd-sessions/requirements.md`.

The evidence is synthetic workshop material, not verified production policy or legal advice. The architecture group’s comparison of alternatives and its stated rejection rationales were reported by the requester on 2026-09-28; they have not been independently validated by benchmark, security assessment, or operational evidence. The research artifact records the underlying operational constraints as C1-C5 and identifies live HRIS, tenant, regional-policy, and retention details as unresolved.

## Decision Drivers

* D1, privacy and authorization: Enforce tenant, role, ownership, and direct-report boundaries; protect medical and compensation data. Source: SOP-HR-042 sections 6.1-6.2 and PRD NFR-005 through NFR-010.
* D2, controlled workflow: Preserve explicit ticket states, human-attributed decisions, SLA processing, and attributable audit events. Source: SOP-HR-042 sections 5.2 and 7.2, SPEC-HRIS-014, and PRD FR-003/FR-004.
* D3, service qualities: Meet the stated response-time, availability, and duplicate-safe asynchronous processing targets. Source: PRD NFR-001 through NFR-004.
* D4, integration and economics: Ground policy responses in versioned sources, keep HRIS integration replaceable, and manage model, retrieval, compute, and data costs. Source: supplied architecture blueprint, PRD NFR-011/NFR-015, and the Marketplace Lean Canvas.

## Constraints

* C1, synthetic evidence: SOP-HR-042 and SPEC-HRIS-014 are synthetic workshop materials. Validate them against each target tenant’s approved policy and regional requirements before production.
* C2, human authority: Managers and authorized HR administrators make approval, rejection, and proxy decisions. The agent cannot self-approve, self-reject, or impersonate a user.
* C3, confidential data: Minimize medical and compensation data. Do not expose it to unauthorized roles, Teams cards, model transcripts, or general-purpose logs.
* C4, auditability: Record lifecycle actions with actor, action, channel, timestamp, and state transition in an append-only or tamper-evident audit path.
* C5, supplied Azure baseline: The planned topology uses Teams, Entra ID OBO, App Service with LangGraph and internal MCP, Foundry, hybrid Azure AI Search, Storage, separate Cosmos DB stores, HRIS/Graph connectors, Service Bus, and Functions.
* C6, inconsistent SLA evidence: SOP-HR-042 specifies a reminder at 48 business hours and escalation after 72 hours; SPEC-HRIS-014 instead shows escalation after a 48-hour SLA. HR must resolve the policy and define timezone, business calendar, and timer semantics before implementation.

## Considered Options

The architecture group’s reported choices and rejected alternatives are listed below. Pros and cons are captured as reported or as explicit design analysis; they are not benchmark results.

### Orchestration and Tool Execution

* LangGraph state machine and MCP tools in Azure App Service, selected.
* Stateless prompt chaining or OpenAI Assistants API, rejected per requester-reported evaluation.
* Proprietary custom REST connector per HRIS, rejected per requester-reported evaluation.

### Retrieval and Models

* Azure AI Foundry with `gpt-6-luna` (version `2026-preview`) as core synthesis model, paired with hybrid BM25/vector Azure AI Search and semantic reranking, selected.
* Dense vector-only search, rejected per requester-reported evaluation.
* Full-context policy window stuffing, rejected per requester-reported evaluation.

### Persistence and Storage

* Separate Cosmos DB stores for ticket/audit data and conversation memory, selected.
* One unified Azure SQL database, rejected per requester-reported evaluation.
* Tickets stored directly as Azure Blob files, rejected per requester-reported evaluation.

## Decision Outcome

Chosen baseline: **LangGraph with MCP tool execution in Azure App Service; Azure AI Foundry with `gpt-6-luna` (version `2026-preview`) model deployment and hybrid BM25/vector Azure AI Search with semantic reranking; and separate Cosmos DB stores for ticket/audit data and conversation memory.** Treat these as three named sub-decisions so each can be revisited independently. Keep the overall ADR in `proposed` status until the named architecture/design authority adopts it.

### Driver-by-Option Assessment

Qualitative assessment based on the supplied workflow constraints and the requester-reported comparison. “Strong,” “Partial,” and “Weak” are design judgments, not measured results.

#### Orchestration Options

| Driver | LangGraph + MCP | Stateless prompt chaining / Assistants | Proprietary HRIS REST connectors |
|---|---|---|---|
| D1 privacy and authorization | Strong: enables an explicit server-side tool boundary; controls still require implementation. | Weak: orchestration alone does not establish a deterministic authorization boundary. | Partial: can authorize per connector but repeats vendor-specific controls. |
| D2 controlled workflow | Strong: explicit state and pause/resume support the approval lifecycle. | Weak: reported not to provide the required inspectable lifecycle and approval pause/resume. | Partial: integration protocol does not itself define workflow state. |
| D3 service qualities | Partial: target needs load and latency testing for the hosted graph and MCP calls. | Partial: fewer custom components may help simple paths but does not meet workflow requirements. | Partial: external API latency and retry behavior remain vendor-dependent. |
| D4 integration and economics | Strong: MCP provides a standardized tool contract; hosting and connector costs remain to be measured. | Partial: potentially lower orchestration overhead but does not satisfy workflow requirements. | Weak: vendor coupling works against pluggable HRIS integration. |

#### Retrieval and Model Options

| Driver | Foundry (gpt-6-luna) + hybrid Search + reranking | Dense vector-only | Full-context window stuffing |
|---|---|---|---|
| D1 privacy and authorization | Partial: supports filtered retrieval and strict prompt grounding with gpt-6-luna; authorization and PHI redaction remain application responsibilities. | Partial: same field and tenant controls are still required. | Weak: sends broader policy context to the model and increases minimization burden. |
| D2 controlled workflow | Partial: grounded answers from gpt-6-luna support policy explanation but do not make approval decisions. | Partial: retrieval quality does not govern ticket transitions. | Partial: model context does not govern ticket transitions. |
| D3 service qualities | Partial: gpt-6-luna provides superior reasoning and optimized latency, though reranking adds a stage that must be measured against p95. | Partial: may reduce retrieval stages but risks exact-clause misses. | Weak: requester reports rising token cost and latency as the policy set grows. |
| D4 integration and economics | Strong: exact-term and semantic retrieval support citations as policy libraries grow; gpt-6-luna token economics and capacity need measurement. | Partial: less retrieval complexity, with reported risk of numeric and policy-code false matches. | Weak: token usage grows with context size and library expansion. |

#### Persistence Options

| Driver | Separate Cosmos DB stores | Unified Azure SQL | Blob-only tickets |
|---|---|---|---|
| D1 privacy and authorization | Strong: permits distinct access and retention boundaries; does not itself make audit events immutable. | Partial: can apply table-level controls, while the reported choice seeks stronger workload separation. | Weak: object separation alone does not provide ticket-level authorization. |
| D2 controlled workflow | Strong: supports a structured ticket store separate from conversation-memory lifecycle; audit immutability needs an additional control. | Strong: relational transactions and constraints are viable for structured tickets. | Weak: lacks the transactional query and concurrency characteristics required for pending-approval operations. |
| D3 service qualities | Partial: consistency, partitioning, recovery, and latency need workload validation. | Partial: performance depends on schema, indexing, and workload sizing. | Weak: requires additional services to meet workflow-query needs. |
| D4 integration and economics | Partial: operational separation is useful but adds stores and cross-store recovery work. | Partial: fewer database technologies, but schema/retention coupling was a reported concern. | Partial: can be economical for archival objects, but not as the ticket system of record. |

### Constraint Disposition

| Constraint | Disposition |
|---|---|
| C1, synthetic evidence | Satisfied as a scope limitation: the architecture remains proposed and requires real-policy validation. |
| C2, human authority | Satisfied by the intended state-machine and server-side tool design; acceptance and authorization tests remain required. |
| C3, confidential data | Partially satisfied by separate data boundaries; deterministic minimization, redaction, authorization, and leakage tests remain implementation requirements. |
| C4, auditability | Deferred in part: Cosmos DB is a store, not an immutable ledger. An append-only write path and a validated tamper-evidence/retention mechanism must be selected before production. |
| C5, supplied Azure baseline | Satisfied as the proposed topology, subject to tenant ownership, region, identity, and connector validation. |
| C6, inconsistent SLA evidence | Deferred and blocking: HR must resolve the 48-hour versus 72-hour interpretation and calendar semantics before SLA timers are implemented. |

### Consequences

* Good, because explicit LangGraph state supports inspectable, human-controlled ticket transitions rather than delegating approvals to generated model output.
* Good, because MCP boundaries and separate data stores can isolate tools and data lifecycles, subject to server-side enforcement and operational configuration.
* Good, because hybrid exact-term and semantic retrieval can support policy-code matching and natural-language discovery with citations.
* Bad, because the service introduces operational responsibility for the App Service, graph state, MCP allowlists, connectors, retries, and on-call support.
* Bad, because semantic reranking and model calls add cost and latency that must be measured against the PRD targets.
* Bad, because separate Cosmos DB stores increase cross-store recovery and consistency work and do not, by themselves, provide immutable audit records.
* Neutral, because the Microsoft 365 Agent Store and Azure Marketplace Managed Application remain separate distribution and deployment tracks; the runtime architecture does not decide the commercial ownership model.
* Record cross-service operations with OpenTelemetry-aligned server/client/producer/consumer spans and required service resource attributes. Use HTTP, database, messaging, and GenAI semantic conventions where they apply. Measure durations with histograms in seconds and bounded dimensions; keep user identifiers, medical content, compensation values, tokens, and raw prompts out of metric attributes and general logs. Use approved redaction before any permitted identifier is retained. See the telemetry vocabulary in `.github/skills/shared/telemetry-foundations/SKILL.md`; the SDK, exporter, and backend remain implementation choices.

## Enterprise HR Copilot Architecture

```mermaid
flowchart TB
    teams["Microsoft Teams"]
    bot["Azure Bot Service"]
    app["Azure App Service: LangGraph + internal MCP"]
    entra["Microsoft Entra ID: OBO"]
    foundry["Azure AI Foundry: gpt-6-luna + moderation"]
    search["Azure AI Search: BM25 + vector + semantic reranker"]
    storage[("Azure Storage: approved policy sources")]
    ticketdb[("Cosmos DB: ticket state + audit events")]
    memorydb[("Cosmos DB: conversation memory")]
    bus["Azure Service Bus: delayed SLA messages"]
    functions["Azure Functions: reminders + escalation"]
    hris["Enterprise HRIS via MCP"]
    graph["Microsoft Graph via MCP"]

    teams <--> bot
    bot <--> app
    entra --> app
    app --> foundry
    app --> search
    storage --> search
    app --> ticketdb
    app --> memorydb
    app --> bus
    bus --> functions
    functions --> ticketdb
    app --> hris
    app --> graph
```

### Legend

Arrows denote planned data, request, or control flow. The diagram is a view of the user-supplied intended topology, not a deployment topology or infrastructure-source rendering.

### Key Relationships

* Teams and Bot Service carry employee conversations and manager approval actions to and from the application.
* App Service performs orchestration, identity-aware tool execution, model/retrieval calls, and persistence operations.
* Azure AI Search retrieves policy evidence from Storage-backed sources; Azure AI Foundry provides gpt-6-luna model and moderation capabilities.
* Service Bus and Functions process due reminders and escalations; Functions re-check ticket state before writing audit events.
* HRIS and Graph are external dependencies accessed through bounded MCP connectors.

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| SOP and ticket specification disagree on the escalation threshold and timer semantics. | High | High | HR policy owner reconciles the rule, calendar, timezone, and pause/reopen behavior before timer implementation. | HR policy owner |
| Cosmos DB audit data is represented as immutable without an actual immutability or tamper-evidence control. | Medium | High | Deny update/delete to application identities, separate audit administration, and approve a governed immutable archive or equivalent control with retention and legal-hold review. | Security/privacy and platform engineering |
| Medical or compensation data leaks through prompts, cards, traces, logs, or memory. | Medium | Critical | Minimize and redact before model calls; filter outputs; exclude sensitive values from telemetry; add adversarial leakage and role-isolation tests. | Security/privacy |
| HRIS delegated access, APIs, or hierarchy data do not match the assumed connector model. | Medium | High | Validate a real tenant contract and identity flow; use a fail-closed draft/HR escalation path when authoritative data is unavailable. | Platform engineering and HRIS owner |
| The p95, availability, or cost targets cannot be met by the selected service configuration. | Medium | High | Establish a representative workload, instrument each boundary, run load/failure tests, and size or revise components before production. | Platform engineering |
| Marketplace packaging and tenant ownership imply unsupported support or cross-tenant access assumptions. | Medium | High | Decide SaaS versus customer-managed ownership, tenant isolation, support, and consent boundaries before publishing either offer. | Product and platform leadership |

## Rollback / Exit Strategy

* Do not enable ticket submission or automated SLA actions in production until C6 is reconciled and authorization, privacy, audit, and recovery gates pass.
* If the orchestration path fails or produces ambiguous ticket state, disable new ticket mutations, preserve recoverable drafts, and direct users to the approved HR process. Do not replay a decision without checking the authoritative current ticket state and idempotency key.
* If model or retrieval quality fails, disable generated policy answers and route the user to the approved policy source or HR. Keep workflow decisions deterministic and human-owned.
* If data isolation or sensitive-field leakage is detected, disable the affected card, memory, prompt, or connector path; restrict access; preserve required evidence under the approved incident process; and resume only after a passing privacy/security retest.
* If the selected persistence design cannot meet transaction, retention, recovery, or audit requirements, pause production use and propose a superseding ADR before migrating authoritative ticket data. Do not treat changing Cosmos configurations as proof of immutable history.

## Affected Components

* Microsoft Teams, Azure Bot Service, and manager approval cards.
* Microsoft Entra ID OBO authentication and authorization.
* Azure App Service, LangGraph state machine, internal MCP server, and connector boundaries.
* Azure AI Foundry model deployments (gpt-6-luna, text-embedding-3-small) and content moderation.
* Azure AI Search hybrid retrieval, semantic reranking, and Storage-backed policy indexing.
* Cosmos DB ticket/audit store and separate conversation-memory store.
* HRIS and Microsoft Graph integrations.
* Azure Service Bus and Azure Functions for reminders and escalations.
* Operational telemetry, audit retention, deployment, recovery, and Marketplace packaging.

## Confirmation

Confirm the design through implementation review and release-candidate evidence: role and tenant-isolation tests; medical/compensation leakage tests across prompts, cards, memory, and telemetry; ticket transition and duplicate-action tests; audit completeness and tamper-evidence verification; policy retrieval/citation evaluations for exact numbers and policy codes; p95 latency and monthly availability measurement; and delayed-message retry, dead-letter, and reconciliation tests.

The success criteria in frontmatter are testable targets, not claims of achieved results. Review baselines and reporting ownership with the PRD owners before production.

## More Information

* Decision scope: the orchestration/tool, retrieval/model, and persistence axes. The architecture group’s alternative evaluations are recorded from the requester’s report on 2026-09-28 and require independent technical verification.
* Research findings: C1 through C5 in `.copilot-tracking/research/2026-09-24/hr-time-leave-agent-research.md`.
* Product requirements: `.copilot-tracking/prd-sessions/requirements.md`.
* Architecture notes: `.copilot-tracking/details/architecture-notes.md`.
* Ticket state machine: `.copilot-tracking/research/workshop-input/sops/ticketing-process-spec.md`.
* Policy rules and privacy boundaries: `.copilot-tracking/research/workshop-input/policies/sop-hr-time-and-leave.md`.
* Related ADRs: none exist in this project at the time of authoring; this record starts the project’s ADR series.
* Review this proposal at least annually and when the HRIS contract, tenant isolation/deployment ownership, regional policy, audit retention, availability/recovery targets, cost envelope, or workload profile changes. Until then, do not treat this ADR as architecture approval.
