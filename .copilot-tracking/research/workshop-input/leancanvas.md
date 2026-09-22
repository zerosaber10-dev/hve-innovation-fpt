<!-- markdownlint-disable-file -->

# Lean Canvas for Resource Allocation Tool

Status: Draft for human review

## Business problem or pain
The current staffing process is slow and manual. After a bid is won, the PM creates a project brief and ops code, then collects CVs from relevant BULs or manually curates candidate lists. Those CVs are checked for availability, approval, and fit before the team is confirmed in an internal tool. Only after income is confirmed does the project begin onboarding and kickoff.

This causes several business problems:
- slow staffing decisions
- too many CVs reviewed before a suitable match is found
- manual coordination between PMs and BULs
- over-allocation and double-booking of team members
- delayed project kickoff and higher operational overhead

The cost of doing nothing is higher delivery risk, lower utilization, missed project start dates, and avoidable rework.

## Target customer or user
Target customer:
- project-driven organizations with multiple concurrent initiatives
- PMO and delivery teams
- business unit leaders responsible for resource approvals

Primary users:
- project managers, who own staffing decisions
- BULs, who confirm capacity and approval
- resource managers or team leads, who review fit and allocation at operational level

The primary decision maker is the PM, while BULs serve as the validation authority for capacity and feasibility.

## Unique value proposition
A resource allocation tool that helps PMs make faster and safer staffing decisions by combining current allocation levels, candidate CV data, and role fit. It does not just show who is available; it identifies strong matches, partial matches, and over-allocation risk before kickoff.

The product makes staffing decisions more transparent, less manual, and less error-prone.

## Solution or core offering
A decision-support tool for project staffing that:
- stores candidate profiles and CVs
- tracks current allocation levels from 0 to 2
- identifies candidates with 0 = unassigned, 1 = fully allocated, and 2 = doubly allocated
- recommends people based on role fit and skill match
- detects partial matches where a person is close but not an ideal fit
- highlights over-allocation and staffing risk before assignment
- supports PM-led assignment with BUL confirmation

Minimum viable version:
- project role requirements
- candidate pool with skill and role data
- current allocation state
- partial-match detection
- risk flags for over-allocation
- PM assignment flow with BUL approval

## Distribution or channels
- roll out first to PMO and operational delivery teams
- pilot with one or two business units or delivery groups
- internal adoption through project leadership and resource managers
- scale from local team allocation to portfolio-level staffing over time

## Revenue model or value capture
Likely value capture includes:
- internal productivity platform for staffing operations
- SaaS or enterprise subscription model for resource management teams
- implementation and onboarding fees
- premium features for portfolio planning, forecasting, and workload optimization

## Cost structure
Major cost drivers:
- data ingestion and integration with internal staffing systems
- candidate and skill matching logic
- UI and workflow development
- approval and access controls
- support, training, and rollout management

## Key metrics and success measures
1. Reduction in time to staff a project
2. Reduction in the number of CVs processed per position
3. Reduction in over-allocation and improvement in staffing fit

Supporting indicators:
- fewer last-minute staffing changes
- fewer rework cycles before kickoff
- better first-pass staffing accuracy
- lower PM and BUL coordination overhead

## Competitive advantage or unfair edge
The strongest advantage is not simply resource tracking. It is early partial-match detection and capacity-aware staffing intelligence. The tool helps PMs distinguish between:
- strong fit
- partial fit
- capacity risk
- over-allocation cases

This helps reduce manual review, improve staffing confidence, and avoid double-booking in a way that spreadsheets and email-driven processes do not.

## Facts vs assumptions vs unknowns

### Facts
- The current process is manual and fragmented across Jira, BUL outreach, CV collection, and internal tools.
- Current allocation data already exists and is an important signal.
- PMs and BULs both participate in staffing, but PMs should own the decision while BULs confirm availability.
- Partial-fit detection is an important use case and should be emphasized.

### Assumptions
- PMs should own the staffing decision and assignment process.
- BULs should confirm capacity and feasibility rather than lead the full process.
- The first release should focus on staffing decisions and risk signals rather than full workforce forecasting.
- The most valuable business outcome is reducing staffing delays and overload risk.

### Unknowns to resolve
- What data fields are actually available in the CVs and staffing systems?
- Are skills and experiences already structured or primarily in free-text CVs?
- What is the project demand pattern across teams and roles?
- What approval workflow must be enforced before a team is formally onboarded?
- What is the minimum viable workflow needed to prove business value?

## Follow-up questions for the project team
- What exact staffing inputs exist today beyond CVs and allocation levels?
- Which project roles most often suffer from staffing delays?
- What level of partial fit is acceptable for a project?
- Which team should own the final staffing approval workflow?
- What is the minimum viable feature set for the pilot release?

## One-line summary
A project staffing platform that helps PMs match the right people to the right work faster, detect partial-fit opportunities earlier, and prevent over-allocation before kickoff.
