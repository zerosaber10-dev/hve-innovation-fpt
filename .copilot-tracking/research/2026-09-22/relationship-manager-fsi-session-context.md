<!-- markdownlint-disable-file -->

# Session Context: Relationship Manager Intelligence Assistant for FSI

Status: Draft for human review

## Session metadata
- Session name: relationship-manager-fsi
- Topic: Relationship Manager Intelligence Assistant for FSI
- Date: 2026-09-22
- Evidence location: ./copilot-tracking/research/workshop-input
- Scenario type: Workshop-only synthetic/public evidence

## Purpose
This session is the shared context for the HVE partner workshop. It defines the problem, evidence boundary, and expected artifact outputs for the multi-role exercises.

## Scenario summary
A financial services partner wants to offer a Relationship Manager Intelligence Experience to enterprise customers. Relationship managers ask questions in Microsoft 365 Copilot and receive consolidated account insights, risk indicators, growth opportunities, and recommended next actions from CRM systems, email, transaction history, and internal knowledge sources.

The solution must preserve source citations, respect user access controls per account, avoid using customer data for model training, and provide operational audit evidence.

## Evidence boundary
- Approved evidence source: local workshop materials under ./copilot-tracking/research/workshop-input
- Do not use production customer data, personal data, credentials, or confidential data in prompts or files unless explicitly approved by the workshop facilitator.
- Keep source material synthetic or public for this workshop scenario.

## Output roots
- Research: .copilot-tracking/research/
- BRD: .copilot-tracking/brd-sessions/
- PRD: .copilot-tracking/prd-sessions/
- Design artifacts: .copilot-tracking/dt/
- Backlog: .copilot-tracking/github-issues/
- ADRs: docs/planning/adrs/

## Shared assumptions to review
- The primary user is a relationship manager at a financial services firm.
- The workflow should support fast retrieval and synthesis of account and portfolio context.
- A Microsoft 365 Copilot experience is the frontend, with Azure-backed supporting services.
- Security, governance, and citations are first-class requirements, not afterthoughts.

## Open questions for the team
- What exact customer data sources are in scope?
- Which account actions require approval workflows or human-in-the-loop review?
- What controls are required for role-based access and model usage restrictions?
- What metrics will define success for adoption, trust, and operational safety?

## Required usage
This artifact is the source of truth for the topic and evidence location for any later agent work. Before any later agent acts, the agent should read this session context and use it as the required context for the workshop exercise.
