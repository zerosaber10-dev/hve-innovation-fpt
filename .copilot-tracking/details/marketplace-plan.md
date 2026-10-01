<!-- markdownlint-disable-file -->

# Marketplace Implementation Plan

## Plan Metadata

| Field | Value |
|---|---|
| Solution | Enterprise Adaptive HR & Time Management Copilot |
| Target customer | Enterprise employers; buyer and initial customer segment require validation |
| Current stage | Offer, deployment, pricing, and Azure IP Co-sell readiness evaluation |
| Marketplace offer type | Undecided: multi-tenant SaaS versus Azure Managed Application |
| Companion-agent scope | Microsoft 365 / Teams Copilot experience is intended; exact agent type and publication package need confirmation |
| Plan owner | Product owner / accountable sponsor to be named |
| Contributors | HR Operations, HR policy, architecture/platform, security/privacy, finance/commercial, Partner Center publisher, Microsoft 365 app owner |
| Created date | 2026-09-29 |
| Last updated | 2026-09-29 |
| Status | Draft; recommendations pending current Microsoft program-source verification and user decisions |

## Executive Summary

The artifacts describe an enterprise HR workflow assistant with sensitive medical and compensation data, tenant-aware authorization, HRIS/Graph integration, audit requirements, Teams approvals, and a proposed Azure backend. The current architecture and ADR do not decide whether the customer or publisher owns the Azure subscription and data plane. No marketplace offer, deployment boundary, pricing, or Azure IP Co-sell eligibility is confirmed.

The planning comparison is between a vendor-operated, multi-tenant SaaS and a customer-subscription Azure Managed Application. The former may reduce per-customer deployment and operations work; the latter may better match customer requirements for subscription ownership and control of data placement, at the cost of deployment, upgrade, support, and tenant-variation work. These are architecture hypotheses to test against validated buyer requirements, not confirmed legal or data-residency outcomes or a verified description of current Microsoft offer mechanics.

The product must not be represented as production-ready or Co-sell eligible on the current record. The policy and ticket evidence are synthetic, the PRD and BRD are drafts, ADR-0001 is proposed, real HRIS and identity contracts are unresolved, audit immutability is not selected, and an SLA conflict blocks workflow implementation. An attempted current Microsoft Learn/Partner Center lookup could not retrieve the official pages. Azure IP Co-sell criteria, MRG/JIT mechanics, qualifying offer types, technical validation, customer-evidence thresholds, and certification steps are therefore not verified here; no current-program claim is made.

Boundaries: this plan is advisory and does not create or submit an offer, configure Partner Center, deploy resources, enroll the publisher in a program, provide tax/legal advice, or claim certification or Co-sell approval.

## Source Evidence

| ID | Source | Date / provenance | Owner | Supports |
|---|---|---|---|---|
| E-01 | .copilot-tracking/brd-sessions/brd-draft.md | Draft, 2026-09-25; synthetic workshop basis | HR Operations Product Owner (listed; approval pending) | Business problem, stakeholder roles, four ticket types, draft outcomes, sensitive-data and human-decision boundaries; states business case and policies need validation. |
| E-02 | .copilot-tracking/prd-sessions/requirements.md | Draft v0.1.0, 2026-09-25 | HR Operations Product Owner (listed; approval pending) | FR-001 to FR-004, NFR-001 to NFR-015, privacy guardrails, draft metrics, and open tenant/HRIS/retention dependencies. |
| E-03 | .copilot-tracking/details/architecture-notes.md | Planned architecture, 2026-09-28 | Architecture Working Draft | Azure component topology; open SaaS versus customer-subscription ownership, tenant isolation, OBO, audit, and Marketplace boundaries. |
| E-04 | .copilot-tracking/details/traceability-matrix.md | Review artifact, 2026-09-29 | Architecture Working Draft | Missing publication gates, unmapped components, unverified claims, and owners needed before readiness. |
| E-05 | docs/planning/adrs/0001-choose-agentic-hr-architecture.md | Proposed ADR, 2026-09-28 | Architecture/design authority (decider role; adoption pending) | Proposed LangGraph/MCP, Foundry/Search, and separate Cosmos choices; records tenant ownership, audit, SLA, and other unresolved constraints. |
| E-06 | .copilot-tracking/research/workshop-input/leancanvas.md | Synthetic workshop framing | Product workshop | Candidate distribution channels, seat-based/volume pricing hypotheses, and cost drivers; not validated customer demand or unit economics. |
| E-07 | Microsoft Learn / Partner Center source leads: Marketplace overview (https://learn.microsoft.com/en-us/azure/marketplace/overview); publisher guide (https://learn.microsoft.com/en-us/azure/marketplace/publisher-guide); Marketplace certification policies (https://learn.microsoft.com/en-us/partner-center/marketplace-certification-policies); SaaS offer creation (https://learn.microsoft.com/en-us/azure/marketplace/partner-center-portal/create-new-saas-offer); co-sell requirements (https://learn.microsoft.com/en-us/partner-center/co-sell-requirements) | Lookup attempted 2026-09-29 but pages were not retrieved. Links are official-source leads only, not verified current evidence. | Marketplace/Partner Center owner | Offer eligibility, MRG and publisher-access mechanics, certification, qualifying offers and current Azure IP Co-sell requirements remain unverified. |

## Decisions and Assumptions

| ID | Type | Statement | Evidence IDs | Owner | Validation action | Status |
|---|---|---|---|---|---|---|
| D-01 | Decision | No Marketplace offer type has been selected. Evaluate multi-tenant SaaS and Azure Managed Application against data placement, subscription ownership, customer requirements, commercial readiness, and operating cost before deciding. | E-03, E-04, E-05 | Product owner with platform and commercial leads | Complete the comparison, obtain buyer/tenant evidence, and record an accountable decision. | Open |
| D-02 | Decision | No pricing or billing model has been approved. Compare a per-user/seat subscription with infrastructure consumption pass-through and a clearly bounded hybrid only if buyers and unit economics support it. | E-02, E-03, E-06 | Product and finance/commercial owners | Validate willingness to pay, seat assignment/entitlement handling, cloud cost variability, billing operations, and current Marketplace mechanics. | Open |
| D-03 | Decision | No Azure IP Co-sell status or Partner Center certification status is claimed. | E-01 through E-05 | Publisher program owner | Verify current official criteria, distinguish listing certification from IP Co-sell eligibility, and gather required evidence. | Open |
| A-01 | Assumption | Sensitive HR data, regional policy and tenant-specific controls may lead some enterprise buyers to prefer a customer-subscription deployment. | E-01 through E-05 | Product owner / enterprise sales | Confirm with target-buyer interviews and security/procurement questionnaires; do not treat as universal. | Unvalidated |
| A-02 | Assumption | A publisher-operated SaaS could offer a repeatable, centrally managed service if tenant isolation, policy scope, data residency, delegated access, support and deletion controls are acceptable to target customers. | E-02, E-03, E-05 | Platform and security/privacy leads | Produce a tenant-boundary design and validate regional, retention, identity and support constraints. | Unvalidated |
| A-03 | Assumption | The intended Microsoft 365 front door may be a custom-engine agent because the proposed solution owns orchestration, retrieval and model calls. | E-03, E-05 | Microsoft 365 app owner | Confirm agent type and the matching current publication path; distinguish M365 publication from Azure backend offer deployment. | Unvalidated |
| A-04 | Assumption | Seat pricing may be easier to explain for workforce access; pass-through may better reflect variable Azure usage but could make total customer cost less predictable. | E-02, E-06 | Product and finance/commercial owners | Model representative tenant sizes and workloads; test billing preferences with buyers. | Unvalidated |
| A-05 | Assumption | Publisher JIT support access, if offered, must be customer-authorized, least-privileged, time-bound, attributable, revocable and restricted from unnecessary HR content. | E-01, E-02, E-03 | Security/privacy and platform leads | Define and threat-model operator support access; validate applicable Managed Application access controls against current Microsoft documentation. | Unvalidated |

## Product and Listing Plan

| Topic | Current plan or gap |
|---|---|
| Target buyer and user | Candidate economic buyers: HR Directors, Chief People Officers, and HR Operations leaders. Users: employees/frontline workers, line managers, and HR administrators. Buyer priority and purchasing authority are not validated. |
| Supported outcomes | Proposed: policy answers with citations; conversational Annual Leave, Sick Leave, Overtime, and Attendance Adjustment tickets; authenticated manager actions in Teams; overdue-ticket routing; role-scoped auditability. These are requirements, not implemented capabilities. |
| Claims | Do not publish “zero-friction,” “turnkey,” “verified audit trail,” multi-tenant isolation, compliance, or quantified savings as proven outcomes without pilot and independent control evidence. |
| Release scope and limitations | PRD MVP includes FR-001 through FR-004 and NFR-001 through NFR-015. It excludes payroll execution, autonomous HR decisions, and general HR case management. HR/business approval of final scope is pending. |
| Listing content | Draft truthful product description, supported workflow, prerequisites, connector dependencies, data-flow/residency statement, privacy and retention disclosures, support route, accessibility limits, and cancellation/data-deletion behavior after product decisions. No listing assets or approved copy supplied. |
| Markets and regions | Undecided. Do not infer global availability from synthetic SOP wording. Identify target countries and validate each applicable HR policy, data placement, offer availability, localization, privacy, and support requirements. |
| Pricing approach | Undecided. Model a per-seat monthly plan against customer-facing consumption billing/pass-through and validate entitlement, trial/overage, unit economics, payment and support operations. |
| Legal and support content | Privacy notice, terms, support commitments, data processing/retention language, and customer offboarding/delete process are not supplied or approved. Legal and privacy review required. |
| Owners and dependencies | Product/HR approve outcomes and claims; platform owns deployment and operations; HRIS and M365 owners approve integrations; security/privacy/legal review data controls; publisher/Partner Center owner handles offer readiness. Depends on D-01 through D-03 and the critical blockers in Risks. |
| Completion evidence | Approved product claims and scope, tested production-equivalent experience, supported-country matrix, pricing approval, published legal/support URLs, and applicable route-specific marketplace evidence. None is complete. |

## Managed Application Technical Plan

### Current baseline and trade-off

The proposed technical baseline is Teams/Bot Service, Entra ID OBO, Azure App Service hosting LangGraph and internal MCP, Azure AI Foundry, Azure AI Search with policy documents in Storage, separate Cosmos DB workloads for tickets/audit and conversation memory, HRIS/Graph connectors, Service Bus, and Functions. It is documented as an intended architecture, not deployed infrastructure or a final hosting decision.

| Consideration | Multi-tenant SaaS hosted by publisher | Azure Managed Application in a customer subscription |
|---|---|---|
| Data placement and residency | Publisher operates a shared service and must prove tenant isolation, region-specific placement/processing, backup/telemetry boundaries, retention and deletion. “Customer data stays in a customer subscription” cannot be claimed. | Azure application resources can be deployed within an agreed customer/provider-managed subscription boundary, but actual data flows may still call publisher services, external models, telemetry or connectors. Validate every flow and region; customer subscription placement alone is not proof of residency. |
| Subscription and customer control | Customer consumes the service; publisher controls hosting lifecycle. Procurement and security must accept the service's hosting, operator and data-processing model. | Customer owns/controls the subscription/resource boundary to the extent agreed by the offer and deployment design. Publisher may still need delegated operational access and manages the application lifecycle according to the offer. |
| Operations and upgrades | One central service and release train can reduce per-customer deployment variance, but requires robust multi-tenant isolation, capacity management, customer-specific policy configuration, SRE and incident response. | Per-customer deployment, configuration, upgrade/rollback, version drift, support and resource-health work increase operational overhead. Standardized templates and support runbooks are essential. |
| Fit for this HR workload | Candidate if customers accept publisher-hosted sensitive data and the product proves data isolation, residency, minimization, deletion, support boundaries and predictable service levels. | Candidate if enterprise procurement requires customer-subscription placement/control and will accept the managed application operations/support model; does not automatically solve consent, cross-service data movement or publisher access concerns. |
| Current recommendation | Keep as the lower-deployment-overhead comparison baseline, not a final selection. | Keep as a customer-control alternative; do not select merely because the data is sensitive. Validate real customer requirements and full data paths first. |

### Publisher access, MRG and tenant isolation

No publisher access or deployment permissions are confirmed. For any Managed Application path, verify the current Managed Applications access model and use the least privilege that permits the explicitly contracted support tasks. Prefer customer-controlled, approved, time-limited JIT elevation over standing broad access where the supported model permits it. Require request purpose, approver, scope, expiry, audit trail, revocation and review. Separate support identity from application runtime identity. Do not expose medical reasons, doctor notes, compensation data or unrelated employee records to support personnel by default.

Define application and support isolation separately: per-customer resource boundary, tenant-to-resource mapping, Entra tenant/consent relationship, HRIS/Graph app identity and scopes, storage/search filters, Cosmos partition/access controls, encryption/key ownership, backup and recovery, monitoring, and offboarding/deletion. Cross-tenant requests must fail closed. Prove isolation with negative tests; do not treat “multi-tenant” as evidence of isolation.

For SaaS, document the publisher subscription/resource boundary and tenant data-plane partitioning. For Managed Application, determine exactly which components deploy into customer resources and which remain publisher-hosted. Verify whether each offer model supports the proposed operator/JIT approach before asserting it.

### Required design gates

| Gate | Owner | Completion evidence |
|---|---|---|
| Confirm SLA policy conflict, timer calendar, and employee/manager action behavior before enabling automated reminders or escalation. | HR policy owner | Approved and consistent SOP/spec/PRD rules and timer tests. |
| Decide SaaS versus customer-subscription component placement, data flows, regions, customer/provider responsibilities and cost ownership. | Product/platform architecture | Approved deployment/data-flow diagram and decision record. |
| Confirm OBO, tenant consent, HRIS/Graph identity model, least-privilege scopes, and support identity/JIT model. | Identity/security + HRIS/M365 owners | Approved threat model, permissions register, customer consent flow and access tests. |
| Implement a defensible audit path, retention, access separation, integrity protection, and privacy-safe telemetry. | Security/privacy + platform/data owners | Approved control design and tested lifecycle/audit evidence; Cosmos DB choice alone is insufficient. |
| Resolve all high-risk missing tests and architecture components from the traceability matrix. | Product quality + engineering leads | Traceability updated with owners and passing evidence for privacy, RBAC, audit, connectors, failures, timing and accessibility. |
| Validate production HRIS, time-clock, notification, and HR escalation-queue contracts and failure modes. | HRIS/integration and HR Operations owners | Contract tests, ownership and operational runbooks. |

## Partner Center Administration Plan

The exact current Partner Center submission prerequisites, Azure IP Co-sell program rules, technical validation and certification steps remain pending official-source verification. Do not treat marketplace certification as equivalent to Azure IP Co-sell eligibility; record them as separate gates after confirming each program's current requirements.

| Workstream | Proposed sequence | Owner | Completion evidence |
|---|---|---|---|
| Publisher readiness | Verify publisher legal/business profile, Partner Center account, role assignments and required program enrollments. Begin any identity/business verification early after confirming current requirements. | Publisher/Partner Center admin | Verified account and role/evidence checklist. |
| Offer route | Select SaaS transactable offer, Azure Managed Application, or justified staged/dual route only after product/deployment decision. | Product/commercial + platform owners | Approved offer and deployment decision; route-specific plan. |
| Technical validation/certification | Map current technical certification requirements to package, runtime, customer onboarding, security/privacy/data handling, support, and test evidence. Submit only after critical product and architecture blockers close. | Technical lead + publisher owner | Completed route-specific checklist, validation evidence, disposition of review findings. |
| Preview/pilot | Use a controlled tenant/customer preview with representative users and approved data; validate installation/deployment, consent, entitlement, connector setup, policy answers, workflows, support, removal and data deletion. | Product, HR Operations, M365 admin, customer security owner | Pilot acceptance, issue log, customer/admin approval and documented rollback/offboarding. |
| Azure IP Co-sell readiness | After current Microsoft eligibility criteria are verified, build the required technical/business evidence, customer references or deployments if required, solution profile and field-enablement assets; request program/partner-manager review rather than self-declaring eligible. | Co-sell program owner + sales/product | Evidence matched line-by-line to current criteria and written status from the authoritative Partner Center/program channel. |
| Publication and post-launch | Submit the approved listing/package, respond to validation/certification feedback, and operate versioning, incident response, SLA, customer support, privacy requests, billing and data offboarding. | Publisher owner + service/product operations | Accepted offer status, launch decision, monitored support and operations. |

## Companion Agent Plan

**Provisional scope:** The architecture notes assume a custom-engine Microsoft 365/Teams agent experience backed by the Azure service. This remains an assumption pending confirmation of the actual agent type and current publication requirements.

* Listing relationship: the agent surface and Azure offer/backend are separate. A published agent surface does not deploy, certify or guarantee access to the HR backend.
* API contract: use a versioned, documented agent-to-service contract with explicit operation scopes; HR ticket mutations must be authorized and idempotent.
* Authentication: validate signed-in user/tenant identity and delegated OBO behavior for user-scoped data. Background processing needs a separate least-privilege service identity and audit attribution.
* Permissions and tenant approval: enumerate every Graph, HRIS and app permission; document reason, data, user impact, consent owner and failure behavior.
* Validation evidence: prove employee/manager/HR role boundaries, tenant isolation, PHI/compensation minimization, card schema/host support, action replay protection, accessibility and approved fallback.
* Conflicts: no agent package, manifest, permission list, API spec, privacy notice, support URL, onboarding or tenant consent evidence is in the supplied artifacts.
* Role owners: M365 app owner, identity/security owner, HRIS owner and customer tenant administrator.

## Implementation Work Plan

Dates remain unset because accountable owners have not supplied a delivery schedule.

| ID | Work item | Responsible role | Dependencies | Expected artifact or evidence | Success criterion | Due date | Status |
|---|---|---|---|---|---|---|---|
| MP-01 | Verify current Azure IP Co-sell, Managed Application, SaaS offer and certification facts against official Microsoft sources. | Marketplace/Partner Center owner | None | Dated source register with official URLs and criterion-to-evidence map | Each version-sensitive requirement is source-cited and publication/certification/Co-sell statuses are separated. | TBD by owner | Blocked: official sources not retrievable in this session |
| MP-02 | Confirm target buyer requirements for data residency, customer subscription ownership, support access and accepted deployment models. | Product owner / enterprise sales | MP-01 | Interview or procurement/security evidence summary | Buyer needs and any non-negotiable deployment constraints have named sources and decision owners. | TBD by owner | Not started |
| MP-03 | Decide SaaS, Managed Application or phased approach, including component placement and tenant/operator boundary. | Product sponsor + platform architecture | MP-02, ADR-0001 governance, HR/privacy input | Approved deployment decision and data-flow diagram | Every data store, model, integration and support path has a customer/publisher owner, region and isolation control. | TBD by owner | Not started |
| MP-04 | Design pricing and entitlement options and validate unit economics. | Product + finance/commercial | MP-01, MP-03 | Seat versus consumption model, cost assumptions and entitlement specification | Approved buyer-tested model has measurable unit economics, clear customer cost and entitlement-denial behavior. | TBD by owner | Not started |
| MP-05 | Close production blockers in the traceability matrix, including SLA, audit, PHI/compensation, identity and connector gaps. | HR policy, security/privacy, platform and QA owners | MP-02, MP-03 | Updated requirements, approved policy rules, threat model and passing tests | No critical unresolved policy/security/audit blocker; relevant acceptance evidence is recorded. | TBD by owners | Not started |
| MP-06 | Prepare route-specific technical validation, deployment, support, privacy, legal and accessibility evidence. | Technical lead + publisher owner | MP-01, MP-03, MP-05 | Certification evidence pack and pilot plan | Checklist is complete against current official requirements; unresolved exceptions are approved or release-blocking. | TBD by owner | Not started |
| MP-07 | Run a controlled customer/tenant pilot and collect outcome evidence. | Product + HR Operations + customer admin | MP-04, MP-05, MP-06 | Pilot results, metric baselines, support and incident log | Product behavior, buyer value, security controls and customer onboarding pass agreed pilot criteria. | TBD by owners | Not started |
| MP-08 | Validate Azure IP Co-sell eligibility and submit/readiness review when evidence supports it. | Named Co-sell program owner | MP-01, MP-03, MP-05, MP-07 | Current criteria checklist, qualified customer/solution evidence, Partner Center status | Every criterion has required evidence and program status is confirmed by the authoritative Microsoft channel. | TBD by owner | Not started |
| MP-09 | Complete publication preview, final certification submission and launch approval. | Publisher/Partner Center owner | MP-06, MP-07, MP-08 as required by verified program sequence | Preview sign-off, submission record and operational launch checklist | Route-specific certification and human launch approvals are complete; support, rollback, billing and offboarding are ready. | TBD by owner | Not started |

## Risks, Blockers, and Open Questions

| ID | Impact | Owner | Resolution action | Due date | Status |
|---|---|---|---|---|---|
| R-01 | Critical: Current Azure IP Co-sell requirements and offer certification details must not be guessed or inferred from stale material. | Marketplace/Partner Center owner | Complete MP-01 using current official Microsoft guidance; verify account-specific status in Partner Center. | TBD | Blocked; lookup attempted 2026-09-29 but pages were not retrieved. Blocks a current Co-sell/certification path recommendation. |
| R-02 | High: There is no confirmed deployment model or customer requirement for residency/subscription ownership. | Product owner and platform architecture | Complete MP-02 and MP-03 with actual buyer evidence and full data-flow placement. | TBD | Open; blocks offer choice. |
| R-03 | Critical: SOP, PRD and ticket-spec escalation semantics conflict; timer implementation and metrics are unsafe until reconciled. | HR policy owner | Publish one authoritative reminder/escalation rule and calendar semantics; update linked artifacts and tests. | TBD | Open; blocks production workflow. |
| R-04 | Critical: PHI and compensation fields may cross model, card, memory, telemetry, logs, or publisher support boundaries. | Privacy/security lead | Define data classification, minimization, role projection, retention and negative tests across all surfaces. | TBD | Open. |
| R-05 | High: “Immutable/verified” audit claims exceed the selected Cosmos DB design; no tamper-evidence mechanism is selected. | Security/privacy and platform/data owners | Select and prove append-only/tamper-evident storage, privileged-access separation, retention and recovery. | TBD | Open; blocks audit claim and launch gate. |
| R-06 | High: Proposed multi-tenant operation, publisher JIT support access and data residency are not supported by a deployment design. | Platform/security and product owners | Decide per-tenant isolation and support access model, obtain customer consent requirements, and test cross-tenant denial. | TBD | Open. |
| R-07 | High: Pricing has no customer research, model/infra cost baseline, entitlement design or finance approval. | Product and finance/commercial owners | Complete MP-04 with representative usage and sensitivity analysis. | TBD | Open. |
| R-08 | High: HRIS, Microsoft Graph, time-clock, email/notification and HR escalation queue contracts are unverified or unmapped. | HRIS/M365 integration owners and HR Operations | Validate production contracts, credentials/consent model, freshness, outages, retries and queue ownership. | TBD | Open. |
| R-09 | Medium: Marketing statements and outcome targets are not evidenced; publication risks overclaiming capability or customer value. | Product marketing and product owner | Treat as hypotheses until pilot and control evidence substantiate them. | TBD | Open. |
| Q-01 | Which customer segment and buying authority should anchor the offer decision: regulated customers requiring customer-subscription control, or buyers willing to use publisher-hosted SaaS? | Product owner | Gather buyer/security/procurement evidence. | TBD | Open |
| Q-02 | Which data must remain in a customer-controlled subscription or region, and may any data transit publisher-hosted Foundry, Search, telemetry or support paths? | Privacy/legal and customer security owner | Approve data-flow and residency requirements by target market. | TBD | Open |
| Q-03 | Should pricing be per assigned user, per active user, per tenant, or usage-based, and who pays unpredictable Azure consumption? | Product and finance | Buyer testing and cost model. | TBD | Open |
| Q-04 | Who is the accountable publisher and Azure IP Co-sell program owner, and what current program criteria apply to this product/offer? | Executive sponsor / Partner Center owner | Name owner and verify official rules/status. | TBD | Open |

## Readiness Assessment

| Gate | Status | Evidence | Rationale |
|---|---|---|---|
| Product | Partial | E-01, E-02, E-06 | Draft business and product scope exists, but target customer buying criteria, commercial claims, approved policy and outcomes remain unvalidated. |
| Technical | Not ready | E-02, E-03, E-04, E-05 | Architecture is proposed; tenant isolation, deployment boundary, identity/contracts, audit immutability, SLA conflict, production tests and operations are open. |
| Partner Center | Not ready | E-03, E-04, E-07 | Offer route, verified publisher/roles, technical package, account status and current route-specific certification evidence are not confirmed; current official sources were not retrievable. |
| Governance | Not ready | E-01, E-02, E-04, E-05 | BRD/PRD are drafts, ADR-0001 is proposed, human approvals are pending, and synthetic rules are not legal or regional policy approval. |
| Companion Agent | Partial | E-03, E-04 | Teams/Copilot surface is planned, but agent type, package, API/permission contract, tenant consent and publication tests are unresolved. |
| Overall | Not ready | E-01 through E-07 | No offer selection, current program-source verification, customer deployment/data boundary, resolved critical risks, or human approval. Azure IP Co-sell eligibility and Partner Center certification are not established. |

## Implementation Handoff

* Approved first implementation slice: None. Do not start marketplace packaging or declare an offer/Co-sell path selected from this draft.
* Prerequisites: finish MP-01 and identify the accountable product, publisher, HR policy, privacy/security and platform decision owners; resolve R-02 through R-06 before production-oriented offer decisions.
* Execution order: verify program facts; validate buyer requirements; decide deployment/data ownership; decide pricing/entitlement; close critical product/security/audit/policy gaps; prepare route-specific evidence and pilot; verify Co-sell eligibility; then submit for publication/certification according to current official requirements.
* Validation methods: source-dated official Microsoft documentation and Partner Center checks; customer security/procurement validation; tenant isolation and sensitive-data tests; real connector contract tests; pilot outcome measurement; documented human review.
* Review checkpoints: product sponsor decision on offer and pricing; HR policy approval of SLA and policy corpus; architecture/design authority adoption of ADR; security/privacy approval of data and publisher access; Partner Center certification review; customer tenant admin consent/pilot acceptance.
* Deferred scope: actual Partner Center account changes, offer creation/submission, resource deployment, tax/payout setup, public claims, customer data processing and Azure IP Co-sell application.
* Next responsible owner: Product owner to name the accountable Marketplace/Partner Center and Azure IP Co-sell owner; that owner must retrieve current Microsoft sources or supply authoritative excerpts before the program-path review resumes.

## Human Review

Named review roles: Product/HR sponsor, HR policy owner, technical/platform lead, Security and Privacy lead, legal/compliance reviewer, finance/commercial owner, Microsoft 365 app owner, Partner Center publisher, and customer tenant administrator. Individual reviewers, decisions, and review dates remain unassigned.

- [ ] Reviewed and approved for implementation by the accountable human owners
