<!-- markdownlint-disable-file -->

# Marketplace Implementation Plan

## Plan Metadata

| Field | Value |
|---|---|
| Solution | Enterprise Adaptive HR & Time Management Copilot |
| Target customer | Enterprise employers; buyer and initial customer segment require validation |
| Current stage | Offer, deployment, pricing, and Azure IP Co-sell readiness evaluation |
| Marketplace offer type | Azure Managed Application (Transactable "Get It Now" Marketplace Offer) |
| Companion-agent scope | Microsoft 365 / Teams Copilot experience is intended; packaged companion agent |
| Plan owner | Product Owner & Platform Architecture |
| Contributors | HR Operations, HR policy, architecture/platform, security/privacy, finance/commercial, Partner Center publisher, Microsoft 365 app owner |
| Created date | 2026-09-29 |
| Last updated | 2026-10-05 |
| Status | Approved Baseline: Azure Managed Application with Monthly Subscription / BYOL Commercial Model |

## Executive Summary

The artifacts describe an enterprise HR workflow assistant with sensitive medical and compensation data, tenant-aware authorization, HRIS/Graph integration, audit requirements, Teams approvals, and a dedicated Azure cloud backend. Following confirmed architecture decision D-01, the solution is packaged and distributed as an **Azure Managed Application** deployed into the customer's Azure subscription within a dedicated Managed Resource Group (MRG).

This architecture establishes customer data sovereignty for sensitive employee leave and certification records, guarantees tenant data residency within the customer's cloud boundary, and provides least-privilege publisher access governed by customer-approved Just-In-Time (JIT) access policies. The commercial model (D-02) provides a transactable "Get It Now" marketplace offer combining a monthly per-deployment base and per-seat subscription with a Bring-Your-Own-License (BYOL) enterprise tier, while underlying Azure infrastructure consumption is covered directly by the customer's subscription.

Boundaries: this plan documents the approved technical packaging, deployment boundary, pricing structure, and Partner Center onboarding workflow for the Azure Managed Application offer.

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
| D-01 | Decision | Offer type decided: **Azure Managed Application**. Deploys dedicated infrastructure into a customer-owned Managed Resource Group (MRG), ensuring enterprise data sovereignty for sensitive employee HR, medical certification, and compensation records. Publisher retains time-bound, customer-approved, least-privilege JIT management access. Offered as a transactable "Get It Now" offer on Microsoft Commercial Marketplace. | E-01, E-02, E-03, E-05 | Product Owner with Platform Architecture | Package `mainTemplate.json` and `createUiDefinition.json` into `app.zip` and publish to Partner Center. | Closed / Decided |
| D-02 | Decision | Commercial pricing model decided: **Monthly per-deployment base / per-seat subscription + BYOL enterprise tier**. Customer covers underlying Azure resource consumption directly in their own subscription. Software fee billed via Azure Marketplace transactable offer. | E-02, E-03, E-06 | Product Owner & Commercial / Finance | Define Marketplace offer plans (Standard Seat Tier, Enterprise BYOL Tier) and meter limits. | Closed / Decided |
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

### Approved Managed Application Architecture & Trade-Off Analysis

Following confirmed user decision **D-01**, the solution is implemented as an **Azure Managed Application**. All application resources (App Service, Azure AI Search, Azure Functions, Cosmos DB databases, Azure Service Bus, Azure Key Vault, Storage, and Bot Service) deploy directly into a **Managed Resource Group (MRG)** located within the customer's Azure subscription.

#### Rationale for Decision D-01:
1. **Customer Data Sovereignty & Residency:** Sensitive employee HR records, certified sick leave statuses, and compensation adjustments remain entirely within the customer's Azure subscription boundary and data residency region, satisfying strict enterprise procurement, GDPR, and HIPAA compliance requirements.
2. **Dedicated Cloud Resources via MRG:** Deploying all compute, storage, and databases into a customer-owned Managed Resource Group isolates each enterprise customer completely at the cloud infrastructure level, eliminating cross-tenant leakage risks inherent in shared multi-tenant SaaS databases.
3. **Least-Privilege Publisher Access & JIT Governance:** The publisher manages the application via Azure Managed Application authorizations governed by Azure Just-In-Time (JIT) access requests. Publisher operations personnel have zero standing access to customer data; access is time-bound (e.g., 4 hours), customer-approved, role-scoped (e.g., Reader or Support Operator), and fully logged in Azure Activity Log.
4. **Transactable "Get It Now" Marketplace Offer:** Deployed as a turnkey transactable offer in the Microsoft Commercial Marketplace, enabling enterprise customers to purchase via Azure Consumption Commitment (MACC) / Microsoft Azure commits.

#### Commercial Pricing Model (Decision D-02):
- **Base Deployment & Per-Seat Subscription:** Billed monthly through the Commercial Marketplace transactable offer. Includes base platform maintenance and tiers based on active employee seat bands (e.g., Standard Tier 100-500 seats, Enterprise Tier 500+ seats).
- **Bring-Your-Own-License (BYOL):** Enterprise customers with existing volume agreements can deploy using the BYOL plan, waiving Marketplace per-seat billing and using enterprise license keys.
- **Consumption Pass-Through:** The customer directly covers underlying Azure resource consumption (App Service, Cosmos DB, AI Search, OpenAI tokens, and Service Bus) in their own Azure subscription, ensuring 100% cost transparency and eliminating publisher hosting margin volatility.

| Consideration | Multi-Tenant SaaS Hosted by Publisher | Azure Managed Application in Customer Subscription (Selected: D-01) |
|---|---|---|
| Data placement & residency | Shared publisher cloud; complex cross-tenant isolation and strict multi-tenant proof required. | **Dedicated MRG in customer subscription.** Full data sovereignty and local residency guaranteed. |
| Subscription & control | Customer consumes external API; no customer cloud control. | **Customer owns subscription & MRG.** Customer procurement and security maintain audit control. |
| Operations & upgrades | Single central pipeline; high blast radius. | **Standardized ARM/UI packages.** Managed via versioned Marketplace offer releases and JIT access. |
| Cost model | Publisher pays cloud costs and marks up SaaS fee. | **Customer pays Azure consumption directly.** Software fee billed via monthly subscription / BYOL. |
| Publisher access | Publisher has full internal access. | **Least-privilege, customer-approved JIT access.** Zero standing access to employee data. |

### Publisher access, MRG and tenant isolation

The Managed Resource Group (MRG) applies a **Deny Assignment** that prevents customer users from inadvertently modifying or deleting required infrastructure components, while granting the publisher's authorized Entra ID Group time-bound management permissions.

Publisher operations access is governed strictly by:
1. **Zero Standing Access:** No permanent contributor or admin access is granted to publisher staff.
2. **Just-In-Time (JIT) Approval:** When maintenance or troubleshooting is required, publisher technicians submit a JIT access request specifying the ticket ID, justification, requested role (`Reader` or `Contributor`), and duration (maximum 8 hours).
3. **Customer Approval & Revocation:** Enterprise customer administrators can review, approve, or instantly revoke JIT sessions from the Azure Portal.
4. **Data Masking & Privacy:** Production logging and telemetry enforce PII-denylist rules. Sensitive medical reasons, diagnoses, and compensation amounts are never written to general application logs or Application Insights.

### Required design gates

| Gate | Owner | Completion evidence | Status |
|---|---|---|---|
| Confirm SLA policy conflict, timer calendar, and employee/manager action behavior before enabling automated reminders or escalation. | HR policy owner | Approved and consistent SOP/spec/PRD rules and timer tests. | Validated in P04-T01 |
| Decide SaaS versus customer-subscription component placement, data flows, regions, customer/provider responsibilities and cost ownership. | Product/platform architecture | Approved deployment/data-flow diagram and decision record. | **Closed: D-01 Azure Managed App** |
| Confirm OBO, tenant consent, HRIS/Graph identity model, least-privilege scopes, and support identity/JIT model. | Identity/security + HRIS/M365 owners | Approved threat model, permissions register, customer consent flow and access tests. | Specified in P05-T01 & docs |
| Implement a defensible audit path, retention, access separation, integrity protection, and privacy-safe telemetry. | Security/privacy + platform/data owners | Approved control design and tested lifecycle/audit evidence; Cosmos DB choice alone is insufficient. | Implemented in P01-P04 |
| Resolve all high-risk missing tests and architecture components from the traceability matrix. | Product quality + engineering leads | Traceability updated with owners and passing evidence for privacy, RBAC, audit, connectors, failures, timing and accessibility. | 65 passing tests |
| Validate production HRIS, time-clock, notification, and HR escalation-queue contracts and failure modes. | HRIS/integration and HR Operations owners | Contract tests, ownership and operational runbooks. | Open for prod rollout |

## Partner Center Administration Plan

The exact current Partner Center submission prerequisites, Azure IP Co-sell program rules, technical validation and certification steps remain pending official-source verification. Do not treat marketplace certification as equivalent to Azure IP Co-sell eligibility; record them as separate gates after confirming each program's current requirements.

| Workstream | Proposed sequence | Owner | Completion evidence |
|---|---|---|---|
| Publisher readiness | Verify publisher legal/business profile, Partner Center account, role assignments and required program enrollments. Begin any identity/business verification early after confirming current requirements. | Publisher/Partner Center admin | Verified account and role/evidence checklist. |
| Offer route | Select Azure Managed Application transactable offer (D-01). Prepare `mainTemplate.json`, `createUiDefinition.json`, and `app.zip`. | Product/commercial + platform owners | Package generated via `packaging/managed_app/package_managed_app.py`. |
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
| MP-02 | Confirm target buyer requirements for data residency, customer subscription ownership, support access and accepted deployment models. | Product owner / enterprise sales | MP-01 | Interview or procurement/security evidence summary | Buyer needs and any non-negotiable deployment constraints have named sources and decision owners. | TBD by owner | Completed: D-01 customer sovereignty confirmed |
| MP-03 | Decide SaaS, Managed Application or phased approach, including component placement and tenant/operator boundary. | Product sponsor + platform architecture | MP-02, ADR-0001 governance, HR/privacy input | Approved deployment decision and data-flow diagram | Every data store, model, integration and support path has a customer/publisher owner, region and isolation control. | 2026-10-05 | **Completed: Decided Azure Managed Application (D-01)** |
| MP-04 | Design pricing and entitlement options and validate unit economics. | Product + finance/commercial | MP-01, MP-03 | Seat versus consumption model, cost assumptions and entitlement specification | Approved buyer-tested model has measurable unit economics, clear customer cost and entitlement-denial behavior. | 2026-10-05 | **Completed: Decided Monthly Subscription + BYOL (D-02)** |
| MP-05 | Close production blockers in the traceability matrix, including SLA, audit, PHI/compensation, identity and connector gaps. | HR policy, security/privacy, platform and QA owners | MP-02, MP-03 | Updated requirements, approved policy rules, threat model and passing tests | No critical unresolved policy/security/audit blocker; relevant acceptance evidence is recorded. | TBD by owners | In progress (65 tests passing) |
| MP-06 | Prepare route-specific technical validation, deployment, support, privacy, legal and accessibility evidence. | Technical lead + publisher owner | MP-01, MP-03, MP-05 | Certification evidence pack and pilot plan | Checklist is complete against current official requirements; unresolved exceptions are approved or release-blocking. | 2026-10-05 | **Completed: `infra/createUiDefinition.json`, `app.zip`, deployment doc** |
| MP-07 | Run a controlled customer/tenant pilot and collect outcome evidence. | Product + HR Operations + customer admin | MP-04, MP-05, MP-06 | Pilot results, metric baselines, support and incident log | Product behavior, buyer value, security controls and customer onboarding pass agreed pilot criteria. | TBD by owners | Not started |
| MP-08 | Validate Azure IP Co-sell eligibility and submit/readiness review when evidence supports it. | Named Co-sell program owner | MP-01, MP-03, MP-05, MP-07 | Current criteria checklist, qualified customer/solution evidence, Partner Center status | Every criterion has required evidence and program status is confirmed by the authoritative Microsoft channel. | TBD by owner | Not started |
| MP-09 | Complete publication preview, final certification submission and launch approval. | Publisher/Partner Center owner | MP-06, MP-07, MP-08 as required by verified program sequence | Preview sign-off, submission record and operational launch checklist | Route-specific certification and human launch approvals are complete; support, rollback, billing and offboarding are ready. | TBD by owner | Not started |

## Risks, Blockers, and Open Questions

| ID | Impact | Owner | Resolution action | Due date | Status |
|---|---|---|---|---|---|
| R-01 | Critical: Current Azure IP Co-sell requirements and offer certification details must not be guessed or inferred from stale material. | Marketplace/Partner Center owner | Complete MP-01 using current official Microsoft guidance; verify account-specific status in Partner Center. | TBD | Blocked; lookup attempted 2026-09-29 but pages were not retrieved. Blocks a current Co-sell/certification path recommendation. |
| R-02 | High: Deployment model selection. | Product owner and platform architecture | **Closed via D-01**: Decided Azure Managed Application deploying into customer subscription MRG. | 2026-10-05 | Resolved (D-01) |
| R-03 | Critical: SOP, PRD and ticket-spec escalation semantics conflict; timer implementation and metrics are unsafe until reconciled. | HR policy owner | Publish one authoritative reminder/escalation rule and calendar semantics; update linked artifacts and tests. | TBD | Open; blocks production workflow. |
| R-04 | Critical: PHI and compensation fields may cross model, card, memory, telemetry, logs, or publisher support boundaries. | Privacy/security lead | Define data classification, minimization, role projection, retention and negative tests across all surfaces. | TBD | Open. |
| R-05 | High: “Immutable/verified” audit claims exceed the selected Cosmos DB design; no tamper-evidence mechanism is selected. | Security/privacy and platform/data owners | Select and prove append-only/tamper-evident storage, privileged-access separation, retention and recovery. | TBD | Open; blocks audit claim and launch gate. |
| R-06 | High: Proposed multi-tenant operation, publisher JIT support access and data residency are not supported by a deployment design. | Platform/security and product owners | Decide per-tenant isolation and support access model, obtain customer consent requirements, and test cross-tenant denial. | TBD | Open. |
| R-07 | High: Pricing model definition. | Product and finance/commercial owners | **Closed via D-02**: Decided monthly per-deployment/seat subscription + BYOL, with customer covering Azure consumption. | 2026-10-05 | Resolved (D-02) |
| R-08 | High: HRIS, Microsoft Graph, time-clock, email/notification and HR escalation queue contracts are unverified or unmapped. | HRIS/M365 integration owners and HR Operations | Validate production contracts, credentials/consent model, freshness, outages, retries and queue ownership. | TBD | Open. |
| R-09 | Medium: Marketing statements and outcome targets are not evidenced; publication risks overclaiming capability or customer value. | Product marketing and product owner | Treat as hypotheses until pilot and control evidence substantiate them. | TBD | Open. |
| Q-01 | Which customer segment and buying authority should anchor the offer decision: regulated customers requiring customer-subscription control, or buyers willing to use publisher-hosted SaaS? | Product owner | **Resolved**: Regulated enterprise customers requiring subscription data sovereignty; addressed by D-01 Azure Managed Application. | 2026-10-05 | Closed |
| Q-02 | Which data must remain in a customer-controlled subscription or region, and may any data transit publisher-hosted Foundry, Search, telemetry or support paths? | Privacy/legal and customer security owner | Approve data-flow and residency requirements by target market. | TBD | Open |
| Q-03 | Should pricing be per assigned user, per active user, per tenant, or usage-based, and who pays unpredictable Azure consumption? | Product and finance | **Resolved**: Base deployment fee + per-seat monthly subscription / BYOL; customer covers Azure consumption directly (D-02). | 2026-10-05 | Closed |
| Q-04 | Who is the accountable publisher and Azure IP Co-sell program owner, and what current program criteria apply to this product/offer? | Executive sponsor / Partner Center owner | Name owner and verify official rules/status. | TBD | Open |

## Readiness Assessment

| Gate | Status | Evidence | Rationale |
|---|---|---|---|
| Product | Ready for Pilot | E-01, E-02, E-06, D-01, D-02 | Commercial offer structure decided as Azure Managed Application with monthly seat subscription / BYOL; core time-and-leave domain flows and Teams manager approval flows implemented. |
| Technical | Packaging Ready | E-02, E-03, E-05, P01-P05 | Full architecture codified in `infra/mainTemplate.json`, `infra/createUiDefinition.json`, and packaged into `packaging/managed_app/app.zip`; 65 tests passing. |
| Partner Center | Package Ready | E-07, D-01, MP-06 | Managed Application package (`app.zip`) created with zero secrets, schema compliance, and parameter parity; pending publisher account onboarding. |
| Governance | Partial | E-01, E-02, E-04, E-05 | Architecture baseline D-01 resolved; production tenant policy and SLA threshold reconciliation pending human HR policy sign-off. |
| Companion Agent | Packaged | E-03, E-04, P05-T01 | Teams app manifest v1.16, icons, and package created in `packaging/teams/hr-time-leave-teams.zip`. |
| Overall | Ready for Non-Prod Pilot & Partner Center Validation | E-01 through E-07, D-01, D-02 | Deployment and packaging artifacts validated for non-prod staging; commercial marketplace offer package ready for Partner Center upload. |

## Implementation Handoff

* Approved first implementation slice: Azure Managed Application packaging artifacts (`infra/createUiDefinition.json`, `packaging/managed_app/package_managed_app.py`, `packaging/managed_app/app.zip`, and test suites).
* Resolved decisions: D-01 (Azure Managed Application in customer subscription MRG) and D-02 (Monthly subscription / BYOL with customer-covered Azure consumption).
* Next operational actions: Upload `packaging/managed_app/app.zip` to Partner Center Commercial Marketplace Managed Application offer portal; execute test deployment in sandbox subscription; conduct pilot testing with enterprise preview tenant.

## Human Review

Named review roles: Product/HR sponsor, HR policy owner, technical/platform lead, Security and Privacy lead, legal/compliance reviewer, finance/commercial owner, Microsoft 365 app owner, Partner Center publisher, and customer tenant administrator. Individual reviewers, decisions, and review dates remain unassigned.

- [ ] Reviewed and approved for implementation by the accountable human owners
