<!-- markdownlint-disable-file -->
---
title: "HR Copilot Agent and Store Publishing Plan"
description: "Proposed agent architecture, authentication, distribution, package, and publication-readiness decisions for the HR Copilot"
author: "Architecture Working Draft"
ms.date: 2026-09-29
ms.topic: reference
keywords:
  - HR Copilot
  - Microsoft 365 Copilot
  - Agent Store
  - Teams
  - publishing
---

## Status and decision boundary

**Status: proposed plan; not confirmed.** This recommendation synthesizes draft BRD and PRD requirements, draft experience design, proposed architecture and ADR, and an undecided marketplace plan. None records product, security, privacy, publisher, or architecture approval of the choices below. The workshop policy and ticket evidence are synthetic. Do not treat this plan as a launch authorization, Microsoft eligibility determination, or completed human review.

The named manifest version `v1.16+` is caller-proposed and has **not** been verified as current or as a minimum. Current package rules, icon requirements, custom-engine eligibility, submission routes, certification criteria, and Adaptive Card/SSO behavior are also unverified. Official source URLs below are leads only; they were not retrieved on 2026-09-29.

## Recommendation

For the current proposed system, prefer a **custom-engine Teams agent** backed by the planned Azure runtime, subject to a technical prototype and confirmation of the current supported packaging and publication route. The design calls for LangGraph orchestration, Azure AI Foundry model and moderation services, hybrid Azure AI Search, persistent ticket workflow, internal MCP tools, HRIS and Microsoft Graph connectors, and explicit human decision boundaries. A declarative agent is not a like-for-like replacement for that architecture: it would simplify delivery only if the product accepts Microsoft 365 Copilot's model and orchestration and reduces the backend to narrowly scoped API actions.

For an initial controlled pilot, prefer an **organizational catalog / private line-of-business distribution route**, only after the M365 app owner verifies that the eventual custom-engine package can use that route in the target tenant. Defer a public Agent Store listing until eligibility and package rules are verified, the product and controls are mature, and required product, legal, security, privacy, support, accessibility, publisher, and tenant approvals are complete. Do not confuse either agent distribution route with Azure Marketplace deployment or procurement of the Azure backend.

Use Entra authentication and evaluate delegated OBO for user-scoped Graph or HRIS operations only after the API audience, token validation, tenant consent, least-privilege scopes, and downstream system delegation support are confirmed. OBO is not the Adaptive Card security mechanism. Treat every card action as untrusted input and authorize it again on the server against the authenticated actor, tenant, current ticket state, manager relationship, expiry/freshness, and idempotency requirements.

## Option comparison

| Decision | Option | Fit with current evidence | Recommendation and conditions |
|---|---|---|---|
| Agent shape | Custom-engine agent with Azure Bot Service and Teams app surface | Closest to the planned LangGraph, Foundry, Search, MCP, stateful ticket, connector, and human-decision design. The runtime, package, and publication eligibility are not verified. | Preferred proposed fit. Prototype the Teams-to-backend interaction and confirm the current supported app/package route before committing. |
| Agent shape | Declarative agent with API actions | Could reduce custom orchestration/model ownership if the product moves workflow logic to bounded APIs and accepts the Microsoft 365 Copilot execution model. It does not preserve the current design unchanged. | Reconsider only after explicit scope and architecture change, plus validation of API actions, identity, sensitive-data handling, and workflow requirements. |
| Pilot distribution | Private organizational catalog / line-of-business deployment | Fits a controlled named-tenant pilot better than an unvalidated public listing. Support for the eventual custom-engine package is not established here. | Preferred proposed pilot route, conditional on tenant and package verification. |
| Broad distribution | Public Microsoft 365 Copilot Agent Store listing | Offers public discovery but requires current route-specific eligibility, package, review, listing, publisher, and operational evidence that is not present. | Defer until the gates in this plan are closed and the accountable publisher approves submission. |
| Backend commercial route | Azure Marketplace SaaS or Managed Application | Marketplace plan says undecided; architecture ownership, deployment boundary, pricing, and operations are open. | Separate decision. Do not infer either offer type from an Agent Store choice. |

## Authentication and card-action controls

### Identity proposal

1. Authenticate the signed-in user and validate token issuer, audience, tenant, and actor at the service boundary.
2. Use delegated OBO only where a user-scoped downstream operation requires it and the downstream API/vendor supports the intended delegation. Confirm consent and minimum scopes for each operation.
3. Keep background reminders and escalation jobs on a separate least-privileged service identity. Record the responsible system actor and job identity; do not misattribute an automated event to a manager.
4. Do not send bearer, refresh, or OBO access tokens to the model, store them in conversation memory, or place them in card JSON or action payloads.
5. Document permission purpose, data accessed, consent owner, failure behavior, token audience, and revocation/rotation responsibilities for customer administrators.

### Adaptive Card decision boundary

The card and its payload are untrusted, even when displayed in an authenticated Teams client. On **every** action, the backend must:

* Authenticate the actor and validate tenant context independently of card-supplied identity fields.
* Load current ticket state and verify it is still pending and eligible for the requested transition.
* Re-check that the actor is the authorized direct manager, or an explicitly authorized HR administrator for a permitted HR action.
* Validate an expiring, action-bound nonce or equivalent server-verifiable freshness mechanism and enforce idempotency under replay and concurrency.
* Require and validate a rejection reason; define safe handling, visibility, and retention for free-text reason content.
* Record actor, action, timestamp, channel, prior and new state, and outcome without copying PHI or restricted compensation content into general logs.
* Return a safe stale, unauthorized, duplicate, or unavailable response without applying a second transition.

The platform-specific SSO, OBO, card action, and token-exchange sequence is **unverified**. Validate it with a minimal end-to-end prototype in the intended tenant and document host/version limitations and a secure fallback before product implementation. Approval/security depends on backend authorization, not on a token or hidden field embedded in a card.

## Distribution and deployment boundaries

The Agent Store or organizational catalog is a discovery/installation surface for an agent experience. Azure Marketplace SaaS or Managed Application is a separate backend offer/deployment and procurement decision. Neither surface establishes HRIS connectivity, grants tenant consent, proves backend isolation, or automatically publishes the other surface.

For the pilot, keep distribution tenant-controlled and limited to named test users, after confirming the route supports the actual custom-engine package. Before any public listing, validate the applicable current route and target markets, supported agent type, publisher requirements, tenant enablement/consent, listing accuracy, support and privacy obligations, and customer onboarding. Keep the public store decision open until those checks are evidenced. Maintain the separate SaaS-versus-Managed-Application decision in the marketplace plan.

## Package and publication readiness checklist

This is a preparation checklist, not a statement of current Microsoft requirements. All unchecked items require evidence and an accountable reviewer.

### Package identity and assets

* [ ] Select and preserve a stable application ID; define versioning and release ownership.
* [ ] Verify the current manifest schema against official guidance and validate the complete package with current tooling. `v1.16+` is an unverified proposal, not a confirmed minimum or recommendation.
* [ ] Confirm the manifest shape and required declarations for the selected agent type, capabilities, valid domains, permissions, and any API/plugin components.
* [ ] Produce color and outline icons only after obtaining the exact current size, format, transparency, and visual rules. The often-cited 192 × 192 color and 32 × 32 outline sizes are **not verified here**.
* [ ] Remove placeholders, internal hostnames, unused domains, sample identities, and unsupported product claims from the package and listing.
* [ ] Verify package installation, update behavior, removal, and rollback in a clean representative test tenant.

### Legal, support, and administrator materials

* [ ] Publish public, HTTPS Privacy Policy and Terms of Use URLs, then test resolution without authentication. Legal/privacy owners must approve the content and ensure it describes actual backend data flows, use, retention, and deletion.
* [ ] Supply a working support URL and monitored contact, support scope, incident path, and customer offboarding/data-deletion guidance.
* [ ] Prepare an administrator consent and rollout guide. For every permission/scope, identify purpose, data accessed, user impact, consent authority, least-privilege alternative, and behavior when not granted.
* [ ] Document data flow, service locations, HRIS/Graph dependencies, retention, deletion, encryption and support access boundaries without claiming residency or isolation that has not been demonstrated.
* [ ] State product prerequisites, supported workflows, limitations, account/licensing needs, and required customer configuration in accurate customer-facing language.
* [ ] Prepare pilot instructions, troubleshooting, accessibility limitations, escalation contacts, and a tested rollback/uninstall path.

### Behavioral and tenant validation

* [ ] Validate every starter and primary workflow in a clean tenant, including policy citations, all four ticket types, rejection reason, Request Info, stale actions, and connector failure.
* [ ] Verify each required permission and consent flow with a tenant administrator; test revocation and missing-consent behavior.
* [ ] Prove employee ownership, manager direct-report, HR role, and cross-tenant boundaries with negative tests.
* [ ] Verify data minimization and absence of medical diagnosis/notes and unauthorized compensation data in model inputs/outputs, cards, notifications, memory, audit, telemetry, and logs.
* [ ] Test card actions for replay, expiry, duplicate delivery, stale state, concurrent decisions, idempotency, and safe retry.
* [ ] Verify supported screen-reader, keyboard, focus, high-contrast, zoom/reflow, and fallback behavior on the actual host; obtain qualified accessibility review.
* [ ] Capture listing images and examples from the tested shipping experience, not mockups or unimplemented behavior.
* [ ] Obtain written product, HR policy, architecture, security, privacy/legal, accessibility, publisher, and tenant-admin approvals before submission or pilot expansion.

## Internal security and RAI publication gate

This is an **internal readiness review**, not a claim of Microsoft certification or a completed official Responsible AI review.

* [ ] Approve a data inventory and flow map covering HRIS, Graph, prompts, retrieval, model/moderation, ticket state, memory, cards, notifications, audit, telemetry, backups, and support access.
* [ ] Complete threat modeling for identity/token exchange, card-action spoofing and replay, tenant isolation, MCP tools, connector credentials, prompt injection, data exfiltration, and privileged support.
* [ ] Demonstrate least privilege and server-side authorization for every read and mutation; verify tenant, owner, manager hierarchy, HR scope, revocation, and fail-closed behavior.
* [ ] Define field-level handling for medical and compensation data. Minimize before model invocation, enforce role-specific projections, and verify with adversarial negative leakage tests.
* [ ] Resolve audit integrity, actor attribution, retention, privileged-access separation, recovery, and evidence requirements. Cosmos DB by itself is not proof of immutability or tamper evidence.
* [ ] Define human accountability, human override/escalation, refusal behavior, policy conflict handling, and limits that prevent autonomous approval/rejection or impersonation.
* [ ] Establish model, prompt, moderation, retrieval, and policy-version governance; test grounded citations, unsupported questions, conflicting policy, unsafe inputs/outputs, and safe failure.
* [ ] Complete privacy/legal review of purpose, minimization, retention, deletion, user notice, data subject handling, and applicable regional policy before production use.
* [ ] Complete security, reliability, operational, incident-response, accessibility, and customer-administrator readiness reviews; retain evidence and named approvers.

## Current blockers from source artifacts

| Blocker | Evidence and required closure |
|---|---|
| Draft and synthetic authority | BRD and PRD are drafts based on synthetic workshop evidence; experience design is draft and its qualified-human-review checkbox remains unchecked. HR/product owners must approve real policy, scope, outcomes, and applicable regional rules. |
| Proposed architecture | Architecture notes describe an intended system, not deployed infrastructure. ADR-0001 is proposed, not adopted. Architecture/design authority must approve or revise it before implementation commitments. |
| SLA conflict | PRD/SOP indicate 48 business hours for reminder and escalation after 72 hours; SPEC-HRIS-014 state diagram indicates escalation after a 48-hour SLA. HR policy owner must publish one rule, including timezone, business calendar, and timer start/pause/reopen semantics. |
| Sensitive data and audit | PHI and compensation exposure paths need field-level controls and negative tests. Audit immutability/tamper evidence is not selected; a Cosmos DB choice alone is insufficient. |
| External dependencies | Production HRIS, Graph hierarchy, time-clock, notifications, and HR Operations queue contracts, delegated-auth support, freshness, failure behavior, and owners are unverified or unmapped. |
| Product and accessibility evidence | Acceptance coverage is incomplete for privacy, role denial, overtime, timers, audit completeness, connector failures, and accessibility. No qualified accessibility review or pilot evidence is present. |
| Publication package and route | No manifest/package, permission register, public legal URLs, listing assets, IaC/deployment artifact, or confirmed publication route is supplied. Current public/private custom-engine route support is unverified. |
| Commercial and publisher ownership | Marketplace plan states offer type and pricing are undecided; accountable publisher and target customer requirements remain unconfirmed. |

## Proposed next-step sequence and owners

1. **Product owner and HR policy owner:** Confirm pilot scope and authoritative policy; resolve the 48/72-hour conflict and synthetic-policy status.
2. **M365 app owner and identity/security architect:** Prototype the custom-engine Teams interaction, card action, token validation, OBO/delegation, consent, and current supported package route.
3. **HRIS, Graph, and integration owners:** Confirm actual APIs, delegated-auth support, directory authority, time-clock and notification contracts, queue ownership, and degraded behavior.
4. **Security, privacy, and data owners:** Approve field classification, minimization, identity boundaries, audit integrity/retention, and sensitive-data negative tests.
5. **Architecture/design authority and platform owner:** Adopt or revise ADR-0001; decide subscription/data boundaries and backend offer separately.
6. **Publisher and Partner Center owner:** Retrieve current authoritative submission requirements; verify schema, assets, route eligibility, publisher account, and any applicable official review criteria.
7. **Product, legal/privacy, accessibility, and tenant administrators:** Approve public-facing content and administrator materials; complete the controlled pilot and record findings.
8. **Accountable product sponsor and publisher:** Decide whether evidence supports a public Agent Store submission; keep it deferred until approvals and route-specific checks pass.

Do not mark any human review item complete in this plan. Product/security/publisher decisions are required before treating any proposed choice as confirmed.

## Decision record

| Choice | Status | Proposed disposition | Human approver role | Approval required |
|---|---|---|---|---|
| Agent shape | Proposed; open pending prototype | Prefer custom-engine Teams app for current LangGraph/Foundry/Search/MCP workflow. Declarative agent remains an alternative only with an explicit architecture/scope change. | Product sponsor, M365 app owner, architecture/design authority | Approve agent type, API boundary, capability scope, and supported route after prototype and current documentation check. |
| User authentication and downstream access | Proposed; open/unverified | Entra sign-in; delegated OBO only for verified user-scoped operations with minimum scopes and supported downstream delegation. Separate least-privileged service identity for background jobs. | Identity/security architect, HRIS/Graph owners, customer tenant administrator | Approve token audience/validation, scopes, consent, downstream support, service identity, and revocation model. |
| Adaptive Card approvals | Proposed; open/unverified | Treat card input as untrusted; enforce server-side identity, tenant, relationship, state, freshness, reason, replay, concurrency, and idempotency checks. | Security lead, Teams/M365 app owner, HR policy owner | Approve target-host behavior and decision-control tests; confirm the card is only an interaction surface, not an authorization proof. |
| Pilot distribution | Proposed; route unverified | Prefer private organizational catalog/LOB for a named-tenant pilot, conditional on current custom-engine package support. | M365 app owner, publisher, customer tenant administrator | Confirm route, package type, tenant enablement/consent, review requirements, and pilot approvals. |
| Public Agent Store listing | Deferred; eligibility unverified | Do not submit until product, package, legal/privacy, security/RAI, support, accessibility, and publisher gates pass. | Product sponsor, publisher, security/privacy/legal, accessibility lead | Approve public claims and submit only after current official eligibility and review steps are verified. |
| Manifest and assets | Open/unverified | Verify the current schema, package file set, icon dimensions/formats, and validation tooling. Treat `v1.16+` and example icon dimensions as unverified. | M365 app owner, publisher | Approve an evidence-backed manifest version and assets against retrieved current official specifications. |
| Privacy, Terms, and admin-consent documentation | Open | Publish approved HTTPS Privacy Policy and Terms; provide permission justification, data-flow and rollout/consent guides, support, retention, and deletion details. | Legal/privacy, identity/security, product, publisher | Approve actual URLs, permission set, data statements, support commitments, and admin guide. |
| Backend Marketplace offer | Open; undecided | Decide SaaS versus Managed Application separately from agent distribution. | Product/commercial sponsor, platform architecture, publisher | Approve deployment ownership, data boundaries, support/operations, pricing, and route-specific current requirements. |
| Security and RAI readiness | Open; not certified | Complete internal threat, privacy, data-leakage, audit, human-accountability, and operational review. Do not describe it as official Microsoft certification. | Security, privacy/RAI, HR policy, architecture authority | Approve evidence and closure of critical blockers; retain qualified human reviews. |

## Official source leads, not fetched

The following Microsoft URLs were identified as source leads for a later verification pass. They were **not fetched or verified on 2026-09-29**; no current requirement or eligibility claim in this plan relies on them.

* Microsoft 365 Copilot agent publishing: <https://learn.microsoft.com/microsoft-365/copilot/extensibility/publish>
* Teams Developer Portal: <https://learn.microsoft.com/en-us/microsoftteams/platform/concepts/build-and-test/teams-developer-portal>
* Teams bot SSO overview: <https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/authentication/bot-sso-overview>
* Microsoft identity platform OBO flow: <https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-on-behalf-of-flow>
* Teams Adaptive Card actions: <https://learn.microsoft.com/en-us/microsoftteams/platform/task-modules-and-cards/cards/cards-actions?tabs=json>
* Teams app publish overview: <https://learn.microsoft.com/en-us/microsoftteams/platform/concepts/deploy-and-publish/apps-publish-overview>

Retrieve the applicable current Microsoft Learn and Partner Center requirements before selecting a public submission route or declaring schema, icon, eligibility, certification, consent, or review criteria. Confirm every item in the actual target tenant and package-validation workflow.
