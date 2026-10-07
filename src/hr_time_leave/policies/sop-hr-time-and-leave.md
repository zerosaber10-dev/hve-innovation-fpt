# Standard Operating Procedure (SOP): Workforce Time, Attendance & Leave Management
**Document ID:** SOP-HR-042  
**Effective Date:** January 1, 2026  
**Version:** 3.2  
**Organization:** NovaTech Global Solutions  
**Applies To:** All Full-Time, Part-Time, and Contractor Employees Worldwide  
**Classification:** Internal Business Use (Synthetic Workshop Context)

---

## 1. Purpose & Scope
This Standard Operating Procedure establishes uniform standards and operational workflows for time recording, overtime compensation, paid time off (PTO), sick leave, and manager approval escalations across all enterprise business units. 

This document serves as the regulatory and policy foundation for human resources operations and AI-assisted workforce automation agents.

---

## 2. Working Hours & Attendance Rules

### 2.1 Standard Work Hours
* The standard full-time work week consists of **40 hours**, distributed across five consecutive 8-hour days (Monday through Friday).
* Core business hours are **09:00 to 18:00** in the employee's designated local timezone, with a mandatory 1-hour unpaid meal break.
* Core collaboration hours are **10:00 to 16:00**, during which synchronous team communication and meeting availability are expected.

### 2.2 Time Tracking & Adjustments
* Hourly, non-exempt, and frontline personnel must record daily clock-in, clock-out, and break intervals via the enterprise time management system.
* **Retroactive Time Adjustments:** If an employee misses a clock-in or clock-out timestamp, they may submit an Attendance Adjustment Ticket within **48 hours** of the shift occurrence, providing a valid justification (e.g., system outage, offsite client emergency).

---

## 3. Overtime (OT) Policy & Calculation

### 3.1 Eligibility & Pre-Authorization
* Overtime is restricted to non-exempt employees and pre-authorized technical personnel responding to critical incidents.
* **Pre-Approval Requirement:** Planned overtime in excess of 2 hours per shift must be pre-approved by the employee’s direct Line Manager.
* **Submission Window:** Unplanned overtime worked during emergencies must be formally logged as an Overtime Ticket within **24 hours** of shift conclusion.

### 3.2 Overtime Pay Multipliers
* **Standard Weekday Overtime (Beyond 8 hours/day or 40 hours/week):** Compensated at **1.5x** the employee's regular hourly base rate.
* **Weekend Overtime (Saturdays & Sundays):** Compensated at **2.0x** regular hourly base rate.
* **Declared Public Holidays:** Compensated at **2.5x** regular hourly base rate plus regular holiday base pay.
* **Maximum Allowable Overtime:** No employee may work more than **12 hours in a single 24-hour cycle** or exceed **16 hours of overtime in any single calendar week**, in compliance with workforce safety mandates.

---

## 4. Paid Time Off (PTO) & Leave Categories

### 4.1 Annual Leave (Paid Vacation)
* **Accrual Rate:** Full-time permanent employees accrue **1.5 business days per month of service** (18 business days per calendar year).
* **Advance Notice Requirements:**
  * Requests for **1 to 2 consecutive business days**: Must be submitted at least **48 hours** in advance.
  * Requests for **3 to 10 consecutive business days**: Must be submitted at least **5 business days** in advance.
  * Requests exceeding **10 consecutive business days**: Requires advance submission of **15 business days** and secondary approval from the Department Director.
* **Blackout Periods:** Operational units subject to quarterly fiscal close (Finance) or peak launch seasons (Release cycles) may enforce blackout periods where discretionary PTO is restricted.

### 4.2 Medical & Sick Leave
* **Self-Certified Sick Leave:** Employees may take up to **2 consecutive business days** without external medical documentation.
* **Certified Medical Leave:** Any absence lasting **3 or more consecutive business days** mandates the upload of a signed medical practitioner's certificate within 5 business days of return to work.
* **Emergency Medical / Hospitalization:** Family emergency or acute medical leave may be logged retroactively up to **72 hours** after the event begins.

### 4.3 Parental, Bereavement, and Special Leaves
* **Bereavement Leave:** Up to 5 consecutive paid days for immediate family members; 3 days for extended family.
* **Unpaid Personal Leave:** Discretionary unpaid leave (up to 30 calendar days) requires HR Operations Lead and Department Vice President sign-off.

---

## 5. Ticketing Lifecycle & Approval SLAs

### 5.1 Ticket Submission Workflow
1. The employee initiates a request (Annual Leave, Sick Leave, Overtime Claim, Attendance Adjustment) via portal, mobile app, or conversational Copilot agent.
2. The system checks real-time leave balances and business rules:
   * Rejection occurs if requested hours exceed the current accrued balance plus allowed borrowing ceiling (max 3 days advance borrowing).
   * Validation warning occurs if the request falls during declared departmental blackout periods.
3. The ticket transitions to `PENDING_APPROVAL` status and notifies the direct Line Manager.

### 5.2 Service Level Agreements (SLAs) for Managers
* **Standard SLA:** Line Managers must take action (`APPROVE`, `REJECT`, or `REQUEST_INFO`) within **48 business hours** of ticket creation.
* **Auto-Escalation:** If a ticket remains unaddressed at the 48-hour threshold:
  1. An urgent reminder is dispatched via Teams / Copilot proactive notification to the manager.
  2. If unreviewed after **72 hours**, the ticket auto-escalates to the **HR Operations Administrator Queue** for triage and proxy action.
* **Rejection Justification:** Any ticket rejection mandates an explicit, documented explanation by the manager.

---

## 6. Access Control, Privacy & Responsible AI (RAI) Rules

### 6.1 Role-Based Access Control (RBAC)
* **Employee Role:** Can view, edit drafts, and cancel their own tickets. Cannot view peer tickets, balances, or departmental aggregate metrics.
* **Line Manager Role:** Can view, approve, or reject tickets only for direct reports in their org tree (via Microsoft Graph / HRIS reporting hierarchy).
* **HR Administrator Role:** Global tenant-wide visibility into all tickets, escalation queues, audit logs, and policy overrides.

### 6.2 Data Privacy & Guardrails
* **Protected Health Information (PHI):** Diagnostic details, doctor notes, and medical justifications are strictly confidential. The conversational agent must NEVER disclose specific medical reasons or uploaded medical notes to line managers or team channels; managers only see "Certified Medical Leave Approved by HR".
* **Salary & Compensation Confidentiality:** Overtime monetary calculations must never be exposed to unauthorized roles or logged in cleartext LLM chat transcripts.

---

## 7. Auditability & System Integrations

### 7.1 Integration Interfaces
* **HRIS / Core ERP:** Master record of employee balances, job profiles, and manager relationships (Workday / SAP / BambooHR REST API).
* **Time Clocking Engine:** Sub-system recording physical badge swipes and mobile geofenced check-ins.
* **Notification Dispatcher:** Microsoft 365 Copilot Actionable Messages, Microsoft Teams Webhooks, and automated email notifications.

### 7.2 Audit Trail Standards
Every ticket lifecycle event must append an immutable audit record containing:
* `timestamp` (UTC ISO-8601)
* `actor_id` (Microsoft Entra Object ID)
* `action_performed` (`CREATED`, `MODIFIED`, `APPROVED`, `REJECTED`, `ESCALATED`)
* `client_channel` (`WEB_PORTAL`, `COPILOT_CONVERSATION`, `API_SYSTEM`)
* `previous_state` and `new_state`
