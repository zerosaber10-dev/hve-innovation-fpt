"""Comprehensive unit tests for Asynchronous SLA Timer Engine."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

import pytest

from hr_time_leave.domain import (
    LifecycleAction,
    SensitiveTicketData,
    Ticket,
    TicketStatus,
    TicketType,
    submit_ticket,
    transition_ticket,
)
from hr_time_leave.sla import (
    BusinessCalendar,
    HREscalationEvent,
    ManagerReminderEvent,
    SLAAuditEvent,
    SLAConfiguration,
    SLAJob,
    SLAJobStatus,
    SLAJobType,
    create_default_sla_engine,
)


def _make_pending_ticket(
    ticket_id: str = "TCK-SLA-001",
    submitted_at: datetime | None = None,
    ticket_type: TicketType = TicketType.ANNUAL_LEAVE,
    sensitive_data: SensitiveTicketData | None = None,
) -> Ticket:
    """Helper to create a validated pending ticket."""
    sub_time = submitted_at or datetime(
        2026, 10, 5, 9, 0, tzinfo=UTC
    )  # Monday 09:00 UTC
    draft = Ticket(
        ticket_id=ticket_id,
        employee_id="EMP-100",
        manager_id="MGR-200",
        ticket_type=ticket_type,
        created_at=sub_time,
        start_date=date(2026, 10, 20),
        end_date=date(2026, 10, 22),
        requested_leave_days=Decimal("3"),
        accrued_leave_days=Decimal("15"),
        sensitive_data=sensitive_data or SensitiveTicketData(),
    )
    return submit_ticket(
        draft,
        actor_id="EMP-100",
        channel="web",
        occurred_at=sub_time,
    )


def test_business_calendar_basic_add_hours() -> None:
    """Test standard business hours addition within a single day and across days."""
    calendar = BusinessCalendar()  # Mon-Fri 09:00 to 17:00 (8h/day)

    # Monday 09:00 + 4 hours -> Monday 13:00
    mon_9am = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
    result = calendar.add_business_hours(mon_9am, 4)
    assert result == datetime(2026, 10, 5, 13, 0, tzinfo=UTC)

    # Monday 09:00 + 8 hours -> Monday 17:00
    result_8h = calendar.add_business_hours(mon_9am, 8)
    assert result_8h == datetime(2026, 10, 5, 17, 0, tzinfo=UTC)

    # Monday 09:00 + 16 business hours -> Tuesday 17:00
    result_16h = calendar.add_business_hours(mon_9am, 16)
    assert result_16h == datetime(2026, 10, 6, 17, 0, tzinfo=UTC)


def test_business_calendar_skips_weekends_and_holidays() -> None:
    """Test business calendar correctly skips weekends and configured holidays."""
    holiday_monday = date(2026, 10, 12)
    calendar = BusinessCalendar(holidays=frozenset({holiday_monday}))

    # Friday 15:00: 2 hours left on Friday.
    # Adding 6 business hours:
    # - 2h on Friday (15:00 to 17:00)
    # - Saturday (10/10) & Sunday (10/11) skipped
    # - Monday (10/12) is holiday, skipped
    # - Tuesday (10/13): starts 09:00, remaining 4h -> Tuesday 13:00
    fri_3pm = datetime(2026, 10, 9, 15, 0, tzinfo=UTC)
    result = calendar.add_business_hours(fri_3pm, 6)
    assert result == datetime(2026, 10, 13, 13, 0, tzinfo=UTC)


def test_business_calendar_normalize_outside_hours() -> None:
    """Test normalizing timestamps during off-hours, weekends, or holidays."""
    calendar = BusinessCalendar()

    # Saturday noon -> advances to Monday 09:00
    sat_noon = datetime(2026, 10, 10, 12, 0, tzinfo=UTC)
    norm = calendar.normalize_to_business_time(sat_noon)
    assert norm == datetime(2026, 10, 12, 9, 0, tzinfo=UTC)

    # Weekday evening (Tuesday 20:00) -> advances to Wednesday 09:00
    tue_8pm = datetime(2026, 10, 6, 20, 0, tzinfo=UTC)
    norm_tue = calendar.normalize_to_business_time(tue_8pm)
    assert norm_tue == datetime(2026, 10, 7, 9, 0, tzinfo=UTC)


def test_business_calendar_invalid_parameters() -> None:
    """Test validation of invalid calendar configuration."""
    with pytest.raises(
        ValueError, match="Work start time .* must be earlier than end time"
    ):
        BusinessCalendar(work_start_time=time(17, 0), work_end_time=time(9, 0))

    with pytest.raises(ValueError, match="must have at least one work day"):
        BusinessCalendar(work_days=frozenset())

    calendar = BusinessCalendar()
    with pytest.raises(ValueError, match="cannot be negative"):
        calendar.add_business_hours(datetime(2026, 10, 5, 9, 0, tzinfo=UTC), -1)


def test_given_pending_ticket_when_48h_elapse_then_urgent_reminder_and_audited() -> (
    None
):
    """AC-011: 48 business hours elapsed triggers reminder and audit."""
    sub_time = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)  # Monday 09:00
    ticket = _make_pending_ticket(submitted_at=sub_time)

    engine = create_default_sla_engine(tickets={ticket.ticket_id: ticket})
    rem_job, esc_job = engine.schedule_sla_jobs(ticket)

    # 48 business hours = 6 full business days (Mon, Tue, Wed, Thu, Fri, next Mon)
    # Ends on Monday 2026-10-12 at 17:00 UTC
    expected_deadline = datetime(2026, 10, 12, 17, 0, tzinfo=UTC)
    assert rem_job.scheduled_at == expected_deadline

    # Clock reaches the 48-business-hour reminder deadline
    clock = expected_deadline
    result = engine.process_job(rem_job, clock)

    assert result.action_taken is True
    assert result.status == SLAJobStatus.EXECUTED
    assert result.ticket_status_before == TicketStatus.PENDING_APPROVAL
    assert result.ticket_status_after == TicketStatus.PENDING_APPROVAL
    assert result.reminder_event is not None
    assert isinstance(result.reminder_event, ManagerReminderEvent)
    assert result.reminder_event.ticket_id == ticket.ticket_id
    assert result.reminder_event.manager_id == ticket.manager_id
    assert result.reminder_event.urgency == "URGENT"
    assert result.reminder_event.channel == "teams"

    # Verify auditable event
    assert result.audit_event is not None
    assert isinstance(result.audit_event, SLAAuditEvent)
    assert result.audit_event.action == "SLA_REMINDER"
    assert result.audit_event.ticket_id == ticket.ticket_id
    assert result.audit_event.actor_id == "SYSTEM_SLA_ENGINE"
    assert result.audit_event.occurred_at == clock

    # Verify ticket state remains PENDING_APPROVAL
    persisted = engine.ticket_store.get_ticket(ticket.ticket_id)
    assert persisted is not None
    assert persisted.status == TicketStatus.PENDING_APPROVAL

    # Verify stored in engine lists
    assert len(engine.reminder_events) == 1
    assert len(engine.audit_records) == 1


def test_given_unreviewed_ticket_when_72h_elapse_then_escalated_to_hr_queue() -> None:
    """AC-012: 72 hours elapsed transitions ticket to ESCALATED."""
    sub_time = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
    ticket = _make_pending_ticket(submitted_at=sub_time)

    engine = create_default_sla_engine(tickets={ticket.ticket_id: ticket})
    rem_job, esc_job = engine.schedule_sla_jobs(ticket)

    # Default 72 elapsed hours: sub_time + 72 hours = Thursday 2026-10-08 09:00 UTC
    expected_esc_deadline = sub_time + timedelta(hours=72)
    assert esc_job.scheduled_at == expected_esc_deadline

    # Clock reaches 72 hours
    clock = expected_esc_deadline
    result = engine.process_job(esc_job, clock)

    assert result.action_taken is True
    assert result.status == SLAJobStatus.EXECUTED
    assert result.ticket_status_before == TicketStatus.PENDING_APPROVAL
    assert result.ticket_status_after == TicketStatus.ESCALATED
    assert result.escalation_event is not None
    assert isinstance(result.escalation_event, HREscalationEvent)
    assert result.escalation_event.queue_name == "HR_OPERATIONS"
    assert result.escalation_event.ticket_id == ticket.ticket_id

    # Verify ticket transitioned to ESCALATED with LifecycleAction.ESCALATE
    persisted = engine.ticket_store.get_ticket(ticket.ticket_id)
    assert persisted is not None
    assert persisted.status == TicketStatus.ESCALATED

    # Verify audit event on ticket
    latest_event = persisted.audit_events[-1]
    assert latest_event.action == LifecycleAction.ESCALATE
    assert latest_event.previous_status == TicketStatus.PENDING_APPROVAL
    assert latest_event.new_status == TicketStatus.ESCALATED
    assert latest_event.actor_id == "SYSTEM_SLA_ENGINE"


def test_given_decided_ticket_approved_when_jobs_run_then_safe_noop() -> None:
    """AC-013: When ticket is APPROVED, reminder and escalation safely no-op."""
    sub_time = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
    ticket = _make_pending_ticket(submitted_at=sub_time)

    engine = create_default_sla_engine(tickets={ticket.ticket_id: ticket})
    rem_job, esc_job = engine.schedule_sla_jobs(ticket)

    # Manager approves ticket before SLA fires
    approved_time = datetime(2026, 10, 5, 14, 0, tzinfo=UTC)
    approved_ticket = transition_ticket(
        ticket,
        TicketStatus.APPROVED,
        actor_id="MGR-200",
        channel="teams",
        occurred_at=approved_time,
        action=LifecycleAction.APPROVE,
    )
    engine.ticket_store.save_ticket(approved_ticket)
    initial_audit_count = len(approved_ticket.audit_events)

    # Clock reaches reminder deadline -> run reminder job
    clock_rem = rem_job.scheduled_at
    rem_result = engine.process_job(rem_job, clock_rem)

    assert rem_result.action_taken is False
    assert rem_result.status == SLAJobStatus.SKIPPED
    assert rem_result.ticket_status_before == TicketStatus.APPROVED
    assert rem_result.ticket_status_after == TicketStatus.APPROVED
    assert len(engine.reminder_events) == 0
    assert len(engine.audit_records) == 0

    # Clock reaches escalation deadline -> run escalation job
    clock_esc = esc_job.scheduled_at
    esc_result = engine.process_job(esc_job, clock_esc)

    assert esc_result.action_taken is False
    assert esc_result.status == SLAJobStatus.SKIPPED
    assert esc_result.ticket_status_before == TicketStatus.APPROVED
    assert esc_result.ticket_status_after == TicketStatus.APPROVED
    assert len(engine.escalation_events) == 0

    # Ticket state must remain APPROVED without new audit events
    persisted = engine.ticket_store.get_ticket(ticket.ticket_id)
    assert persisted is not None
    assert persisted.status == TicketStatus.APPROVED
    assert len(persisted.audit_events) == initial_audit_count


def test_given_decided_ticket_rejected_when_jobs_run_then_safe_noop() -> None:
    """AC-013: When a ticket is REJECTED, reminder and escalation jobs safely no-op."""
    sub_time = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
    ticket = _make_pending_ticket(submitted_at=sub_time)

    engine = create_default_sla_engine(tickets={ticket.ticket_id: ticket})
    rem_job, esc_job = engine.schedule_sla_jobs(ticket)

    # Manager rejects ticket
    rej_time = datetime(2026, 10, 5, 15, 0, tzinfo=UTC)
    rejected_ticket = transition_ticket(
        ticket,
        TicketStatus.REJECTED,
        actor_id="MGR-200",
        channel="teams",
        occurred_at=rej_time,
        action=LifecycleAction.REJECT,
        rejection_reason="Staffing coverage is insufficient.",
    )
    engine.ticket_store.save_ticket(rejected_ticket)

    # Reminder and escalation jobs run
    rem_result = engine.process_job(rem_job, rem_job.scheduled_at)
    esc_result = engine.process_job(esc_job, esc_job.scheduled_at)

    assert rem_result.action_taken is False
    assert rem_result.status == SLAJobStatus.SKIPPED
    assert esc_result.action_taken is False
    assert esc_result.status == SLAJobStatus.SKIPPED

    persisted = engine.ticket_store.get_ticket(ticket.ticket_id)
    assert persisted is not None
    assert persisted.status == TicketStatus.REJECTED


def test_given_already_escalated_ticket_when_duplicate_job_runs_then_safe_noop() -> (
    None
):
    """AC-013: Duplicate escalation jobs do not produce duplicate transitions."""
    sub_time = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
    ticket = _make_pending_ticket(submitted_at=sub_time)

    engine = create_default_sla_engine(tickets={ticket.ticket_id: ticket})
    _, esc_job = engine.schedule_sla_jobs(ticket)

    # First escalation runs
    first_res = engine.process_job(esc_job, esc_job.scheduled_at)
    assert first_res.action_taken is True
    assert first_res.status == SLAJobStatus.EXECUTED

    persisted_after_first = engine.ticket_store.get_ticket(ticket.ticket_id)
    assert persisted_after_first is not None
    assert persisted_after_first.status == TicketStatus.ESCALATED
    audit_count_after_first = len(persisted_after_first.audit_events)

    # A duplicate escalation job (e.g. from service bus redelivery)
    duplicate_esc_job = SLAJob(
        job_id="job-duplicate-esc",
        ticket_id=ticket.ticket_id,
        job_type=SLAJobType.ESCALATION,
        scheduled_at=esc_job.scheduled_at,
        created_at=esc_job.created_at,
    )
    engine.job_store.schedule_job(duplicate_esc_job)

    dup_res = engine.process_job(
        duplicate_esc_job, esc_job.scheduled_at + timedelta(minutes=10)
    )

    assert dup_res.action_taken is False
    assert dup_res.status == SLAJobStatus.SKIPPED
    assert dup_res.ticket_status_before == TicketStatus.ESCALATED
    assert dup_res.ticket_status_after == TicketStatus.ESCALATED

    # No duplicate lifecycle transition was added
    persisted_after_dup = engine.ticket_store.get_ticket(ticket.ticket_id)
    assert persisted_after_dup is not None
    assert len(persisted_after_dup.audit_events) == audit_count_after_first


def test_duplicate_reminder_job_suppression() -> None:
    """AC-013: Duplicate reminder job does not dispatch a duplicate reminder event."""
    sub_time = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
    ticket = _make_pending_ticket(submitted_at=sub_time)

    engine = create_default_sla_engine(tickets={ticket.ticket_id: ticket})
    rem_job, _ = engine.schedule_sla_jobs(ticket)

    # First reminder execution
    res1 = engine.process_job(rem_job, rem_job.scheduled_at)
    assert res1.action_taken is True
    assert len(engine.reminder_events) == 1

    # Second reminder job created for same ticket
    dup_rem_job = SLAJob(
        job_id="job-duplicate-rem",
        ticket_id=ticket.ticket_id,
        job_type=SLAJobType.REMINDER,
        scheduled_at=rem_job.scheduled_at,
        created_at=rem_job.created_at,
    )
    res2 = engine.process_job(dup_rem_job, rem_job.scheduled_at + timedelta(minutes=5))

    assert res2.action_taken is False
    assert res2.status == SLAJobStatus.SKIPPED
    assert len(engine.reminder_events) == 1  # Still 1, no duplicate reminder


def test_already_executed_job_replayed_returns_cached_noop() -> None:
    """Test idempotency when an already executed job instance is replayed."""
    sub_time = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
    ticket = _make_pending_ticket(submitted_at=sub_time)

    engine = create_default_sla_engine(tickets={ticket.ticket_id: ticket})
    rem_job, _ = engine.schedule_sla_jobs(ticket)

    res1 = engine.process_job(rem_job, rem_job.scheduled_at)
    assert res1.status == SLAJobStatus.EXECUTED

    # Replay same job object
    res2 = engine.process_job(rem_job, rem_job.scheduled_at)
    assert res2.action_taken is False
    assert res2.status == SLAJobStatus.EXECUTED
    assert "already marked EXECUTED" in res2.message


def test_process_due_jobs_in_schedule_sequence() -> None:
    """Test process_due_jobs batches and executes scheduled jobs as clock progresses."""
    sub_time = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
    t1 = _make_pending_ticket(ticket_id="TCK-SEQ-1", submitted_at=sub_time)
    t2 = _make_pending_ticket(ticket_id="TCK-SEQ-2", submitted_at=sub_time)

    engine = create_default_sla_engine(tickets={t1.ticket_id: t1, t2.ticket_id: t2})
    engine.schedule_sla_jobs(t1)
    engine.schedule_sla_jobs(t2)

    # At T0 + 10 hours: no jobs due
    clock_10h = sub_time + timedelta(hours=10)
    assert len(engine.process_due_jobs(clock_10h)) == 0

    # At 72 elapsed hours (Thursday 09:00): escalation jobs are due!
    clock_72h = sub_time + timedelta(hours=72)
    results = engine.process_due_jobs(clock_72h)
    assert len(results) == 2
    assert all(r.job_type == SLAJobType.ESCALATION for r in results)
    assert all(r.status == SLAJobStatus.EXECUTED for r in results)


def test_dispatch_window_performance_and_accuracy() -> None:
    """NFR-002: Verify dispatch within 5 minutes of calculated threshold."""
    config = SLAConfiguration(dispatch_window_minutes=5)
    scheduled_at = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)

    # On time (0 min diff)
    assert config.is_within_dispatch_window(scheduled_at, scheduled_at) is True

    # 4 min 59 sec late -> within window
    assert (
        config.is_within_dispatch_window(
            scheduled_at,
            scheduled_at + timedelta(minutes=4, seconds=59),
        )
        is True
    )

    # 5 min 1 sec late -> outside window
    assert (
        config.is_within_dispatch_window(
            scheduled_at,
            scheduled_at + timedelta(minutes=5, seconds=1),
        )
        is False
    )

    # Simulated load: 100 jobs within 2m of threshold -> 100% compliance (>99%)
    compliant_count = sum(
        1
        for i in range(100)
        if config.is_within_dispatch_window(
            scheduled_at,
            scheduled_at + timedelta(seconds=i),
        )
    )
    assert compliant_count == 100
    assert (compliant_count / 100) >= 0.99


def test_nonexistent_ticket_in_store_handled_gracefully() -> None:
    """Test job for non-existent ticket skips gracefully."""
    engine = create_default_sla_engine(tickets={})
    orphan_job = SLAJob(
        job_id="job-orphan",
        ticket_id="NON-EXISTENT",
        job_type=SLAJobType.REMINDER,
        scheduled_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    engine.job_store.schedule_job(orphan_job)

    result = engine.process_job(orphan_job, datetime.now(UTC))
    assert result.action_taken is False
    assert result.status == SLAJobStatus.SKIPPED
    assert "does not exist" in result.message


def test_custom_sla_configuration_and_calendar() -> None:
    """Test configurable thresholds and custom working calendar."""
    custom_calendar = BusinessCalendar(
        work_days=frozenset({0, 1, 2, 3}),  # 4-day work week: Mon-Thu
        work_start_time=time(10, 0),
        work_end_time=time(18, 0),  # 8h/day
    )
    config = SLAConfiguration(
        reminder_threshold_hours=Decimal("24"),  # 3 work days
        escalation_threshold_hours=Decimal("48"),
        escalation_uses_business_hours=True,
        business_calendar=custom_calendar,
    )

    # Monday 10:00 + 24 business hours (3 days: Mon, Tue, Wed) -> Wed 18:00
    mon_10am = datetime(2026, 10, 5, 10, 0, tzinfo=UTC)
    deadline = config.calculate_reminder_deadline(mon_10am)
    assert deadline == datetime(2026, 10, 7, 18, 0, tzinfo=UTC)


def test_telemetry_and_privacy_no_pii_leakage() -> None:
    """RAI/Privacy: Ensure sensitive health/compensation data is excluded."""
    sub_time = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
    sensitive_data = SensitiveTicketData(
        medical_reason="Post-operative recovery from orthopedic surgery",
        medical_notes="Dr. Smith note ref #44321",
        compensation_amount=Decimal("1500.00"),
    )
    ticket = _make_pending_ticket(
        submitted_at=sub_time,
        ticket_type=TicketType.SICK_LEAVE,
        sensitive_data=sensitive_data,
    )

    engine = create_default_sla_engine(tickets={ticket.ticket_id: ticket})
    rem_job, _ = engine.schedule_sla_jobs(ticket)

    result = engine.process_job(rem_job, rem_job.scheduled_at)
    assert result.reminder_event is not None
    summary = result.reminder_event.summary

    # Assert no sensitive notes, diagnosis, doctor names, or compensation appear
    assert "orthopedic surgery" not in summary
    assert "Dr. Smith" not in summary
    assert "1500" not in summary

    # Verify audit details
    assert result.audit_event is not None
    details_str = str(getattr(result.audit_event, "details", {}))
    assert "orthopedic" not in details_str
    assert "1500" not in details_str
