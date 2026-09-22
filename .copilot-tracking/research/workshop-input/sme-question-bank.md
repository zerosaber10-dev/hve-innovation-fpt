<!-- markdownlint-disable-file -->

# SME Question Bank for the Resource Allocation Tool

Use this question set to ground the workshop in evidence. Answer as many as possible before the PM, design, and technical roles begin drafting requirements and architecture.

## 1) Business context
- What business problem is this tool trying to solve?
- What is the current process for assigning people to projects or tasks?
- How often does staffing planning happen?
- What is the cost of poor staffing decisions today?
- Which teams are most affected by staffing conflicts or delays?
- What is the biggest operational pain: overload, underutilization, delays, or forecast inaccuracy?

## 2) Stakeholders and users
- Who owns resource allocation today?
- Who decides staffing priorities across teams or projects?
- Who is the main end user of the tool: manager, PMO lead, delivery lead, or executive?
- Which roles will depend on this tool the most?
- Who should have read-only access versus edit access?
- Which stakeholders will resist the change and why?

## 3) Business rules and constraints
- What rules govern how work is assigned today?
- Are there mandatory skill requirements for certain projects?
- Are there travel, location, timezone, or availability constraints?
- Are there compliance or security restrictions on who can access certain work?
- What is the minimum staffing threshold for a project to proceed?
- Are there any labor, union, or policy constraints we need to respect?

## 4) Data and evidence
- What source systems currently hold staffing data?
- Do you have employee skill data today? If yes, where is it stored?
- Do you track project demand, work items, or staffing needs in another system?
- What data is current, and what data is stale or manually maintained?
- Which data fields are considered authoritative?
- What information is missing today and must be collected manually?

## 5) User experience and workflow
- How does the manager currently decide who should take a project?
- What decisions are made manually today that should be automated or supported?
- What does good resource allocation look like in practice?
- What would a user expect to see in the first screen of the tool?
- What is the most frequent scenario the tool must support: weekly planning, project launch, or real-time reassignment?
- What tasks are most painful to do without the tool?

## 6) Success metrics
- How will the business know the tool is working?
- What metrics matter most: utilization, project delivery, cost, quality, or employee experience?
- Do you have target utilization ranges or thresholds?
- What is the current baseline for time spent on staffing decisions?
- What measurable outcome would justify a rollout beyond a pilot?

## 7) Functional requirements
- Should the tool support recommendations only, or should it also allow assignment approval?
- Should the system support scenario planning for future demand?
- Does the product need multi-project balancing, team balancing, or both?
- Should the tool handle skill gaps and recommended training or hiring?
- Do users need to compare multiple staffing options before choosing a final assignment?
- Should the system support recurring or periodic rebalancing?

## 8) Risks and failure cases
- What happens if staffing data is wrong or incomplete?
- What happens when a manager overrides a recommendation?
- How do you handle last-minute changes or urgent demand spikes?
- What is the risk of assigning the wrong person to a critical project?
- How do you prevent bias or unfair distribution across teams or employees?
- What are the key failure cases the tool must surface clearly?

## 9) Responsible AI and trust questions
- Will the tool make recommendations, or will it simply display insights?
- How should the tool explain why a person was suggested or not suggested?
- What information should be visible to users about recommendation logic?
- How should human override and accountability be handled?
- What safeguards are needed to avoid biased assignments or unfair workload distribution?
- Do we need audit trails for staffing decisions and overrides?

## 10) Technical and integration context
- What systems should the tool integrate with?
- Which teams own employee data, project data, and time data?
- What are the expected data update frequencies?
- What is the expected volume of users and projects?
- What enterprise security controls are required?
- What is the acceptable latency for staffing calculations and recommendations?

## 11) Commercial and rollout considerations
- Is this intended for one department or for multiple business units?
- What is the rollout plan: pilot, phased expansion, or broad deployment?
- Who will pay for the solution?
- What part of the business will champion adoption?
- What will be the commercial model: internal platform, SaaS, or managed service?
- What would cause the project to stop being viable?

## 12) Open questions to resolve before design work
- What is the exact unit of planning: employee, team, portfolio, or project?
- Is the tool primarily descriptive or prescriptive?
- Which use case is highest priority for the first release: assignment, forecasting, optimization, or staffing alerts?
- What is the most important decision we need to support in the first MVP?
- What is the smallest dataset and workflow needed to prove value?

## Quick SME answer template
Use this format when you answer one or two questions at a time:

- Question:
- Answer:
- Evidence or source:
- Confidence: High / Medium / Low
- Assumption or open item:

## Suggested first-pass set
If you want the fastest starting set, answer these first:
1. What is the current staffing process and where does it break down?
2. Who owns resource allocation decisions today?
3. What data exists today for skills, availability, and project demand?
4. What are the top three success metrics for the tool?
5. What is the top failure case or staffing risk we must prevent?
6. What should the first release do, and what can wait?
