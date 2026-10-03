"""Asynchronous SLA timer engine for manager reminders and HR escalations."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta, tzinfo
from decimal import Decimal
from enum import StrEnum
from typing import Final, Protocol

from hr_time_leave.domain import (
    LifecycleAction,
    LifecycleEvent,
    Ticket,
    TicketStatus,
    TicketType,
    transition_ticket,
)

DEFAULT_REMINDER_THRESHOLD_HOURS: Final[Decimal] = Decimal("48")
DEFAULT_ESCALATION_THRESHOLD_HOURS: Final[Decimal] = Decimal("72")
DEFAULT_DISPATCH_WINDOW_MINUTES: Final[int] = 5
DEFAULT_HR_QUEUE_NAME: Final[str] = "HR_OPERATIONS"
SYSTEM_ACTOR_ID: Final[str] = "SYSTEM_SLA_ENGINE"
SLA_CHANNEL: Final[str] = "service_bus_timer"


class SLAJobType(StrEnum):
    """Supported SLA job categories."""

    REMINDER = "REMINDER"
    ESCALATION = "ESCALATION"


class SLAJobStatus(StrEnum):
    """Lifecycle statuses for an asynchronous SLA job."""

    SCHEDULED = "SCHEDULED"
    EXECUTED = "EXECUTED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class BusinessCalendar:
    """Configurable business-hour calendar for SLA deadline calculations."""

    work_days: frozenset[int] = frozenset({0, 1, 2, 3, 4})  # Monday=0 ... Friday=4
    work_start_time: time = time(9, 0)
    work_end_time: time = time(17, 0)
    holidays: frozenset[date] = field(default_factory=frozenset)
    calendar_timezone: tzinfo = UTC

    def __post_init__(self) -> None:
        if self.work_start_time >= self.work_end_time:
            raise ValueError(
                f"Work start time ({self.work_start_time}) must be earlier than "
                f"end time ({self.work_end_time})."
            )
        if not self.work_days:
            raise ValueError("Business calendar must have at least one work day.")

    @property
    def daily_work_seconds(self) -> int:
        """Total working seconds in a standard business day."""
        start_seconds = (
            self.work_start_time.hour * 3600 + self.work_start_time.minute * 60
        )
        end_seconds = self.work_end_time.hour * 3600 + self.work_end_time.minute * 60
        return end_seconds - start_seconds

    def is_business_day(self, target_date: date) -> bool:
        """Check if a date is a scheduled work day and not an observed holiday."""
        return (target_date.weekday() in self.work_days) and (
            target_date not in self.holidays
        )

    def is_business_hour(self, dt: datetime) -> bool:
        """Check if a given timestamp falls within business hours."""
        local_dt = dt.astimezone(self.calendar_timezone)
        if not self.is_business_day(local_dt.date()):
            return False
        current_time = local_dt.time()
        return self.work_start_time <= current_time < self.work_end_time

    def normalize_to_business_time(self, dt: datetime) -> datetime:
        """Advance a timestamp to the next opening business instant if outside hours."""
        current = dt.astimezone(self.calendar_timezone)
        while True:
            current_date = current.date()
            if not self.is_business_day(current_date):
                current = datetime.combine(
                    current_date + timedelta(days=1),
                    self.work_start_time,
                ).replace(tzinfo=self.calendar_timezone)
                continue

            current_time = current.time()
            if current_time < self.work_start_time:
                return datetime.combine(
                    current_date,
                    self.work_start_time,
                ).replace(tzinfo=self.calendar_timezone)

            if current_time >= self.work_end_time:
                current = datetime.combine(
                    current_date + timedelta(days=1),
                    self.work_start_time,
                ).replace(tzinfo=self.calendar_timezone)
                continue

            return current

    def add_business_hours(
        self,
        start_dt: datetime,
        hours: Decimal | float | int,
    ) -> datetime:
        """Advance a timestamp by business hours, skipping non-working periods."""
        if hours < 0:
            raise ValueError("Business hours increment cannot be negative.")
        if hours == 0:
            return start_dt

        remaining_seconds = int(Decimal(str(hours)) * Decimal("3600"))
        current = self.normalize_to_business_time(start_dt)

        while remaining_seconds > 0:
            current_date = current.date()
            day_end = datetime.combine(
                current_date,
                self.work_end_time,
            ).replace(tzinfo=self.calendar_timezone)

            seconds_left_in_day = int((day_end - current).total_seconds())

            if remaining_seconds <= seconds_left_in_day:
                current = current + timedelta(seconds=remaining_seconds)
                remaining_seconds = 0
            else:
                remaining_seconds -= seconds_left_in_day
                # Advance to start of next business day
                next_day = current_date + timedelta(days=1)
                while not self.is_business_day(next_day):
                    next_day += timedelta(days=1)
                current = datetime.combine(
                    next_day,
                    self.work_start_time,
                ).replace(tzinfo=self.calendar_timezone)

        return current.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class SLAConfiguration:
    """Configurable thresholds and calendar settings for the SLA engine."""

    reminder_threshold_hours: Decimal = DEFAULT_REMINDER_THRESHOLD_HOURS
    escalation_threshold_hours: Decimal = DEFAULT_ESCALATION_THRESHOLD_HOURS
    reminder_uses_business_hours: bool = True
    escalation_uses_business_hours: bool = False
    business_calendar: BusinessCalendar = field(default_factory=BusinessCalendar)
    dispatch_window_minutes: int = DEFAULT_DISPATCH_WINDOW_MINUTES
    hr_queue_name: str = DEFAULT_HR_QUEUE_NAME
    urgency_level: str = "URGENT"

    def calculate_reminder_deadline(self, start_dt: datetime) -> datetime:
        """Calculate the UTC timestamp for the urgent manager reminder."""
        normalized_start = start_dt.astimezone(UTC)
        if self.reminder_uses_business_hours:
            return self.business_calendar.add_business_hours(
                normalized_start,
                self.reminder_threshold_hours,
            )
        delta_seconds = int(self.reminder_threshold_hours * Decimal("3600"))
        return normalized_start + timedelta(seconds=delta_seconds)

    def calculate_escalation_deadline(self, start_dt: datetime) -> datetime:
        """Calculate the UTC timestamp for HR queue escalation."""
        normalized_start = start_dt.astimezone(UTC)
        if self.escalation_uses_business_hours:
            return self.business_calendar.add_business_hours(
                normalized_start,
                self.escalation_threshold_hours,
            )
        delta_seconds = int(self.escalation_threshold_hours * Decimal("3600"))
        return normalized_start + timedelta(seconds=delta_seconds)

    def is_within_dispatch_window(
        self,
        scheduled_at: datetime,
        dispatched_at: datetime,
    ) -> bool:
        """Check if job dispatch occurred within the allowed window (e.g. 5 minutes)."""
        diff = abs((dispatched_at - scheduled_at).total_seconds())
        allowed_seconds = self.dispatch_window_minutes * 60
        return diff <= allowed_seconds


@dataclass(slots=True)
class SLAJob:
    """Asynchronous SLA timer job metadata."""

    job_id: str
    ticket_id: str
    job_type: SLAJobType
    scheduled_at: datetime
    created_at: datetime
    status: SLAJobStatus = SLAJobStatus.SCHEDULED
    executed_at: datetime | None = None
    execution_reason: str | None = None
    attempts: int = 0
    idempotency_key: str = ""

    def __post_init__(self) -> None:
        if self.scheduled_at.tzinfo is None:
            self.scheduled_at = self.scheduled_at.replace(tzinfo=UTC)
        else:
            self.scheduled_at = self.scheduled_at.astimezone(UTC)
        if self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=UTC)
        else:
            self.created_at = self.created_at.astimezone(UTC)
        if not self.idempotency_key:
            self.idempotency_key = f"{self.ticket_id}:{self.job_type.value}"


@dataclass(frozen=True, slots=True)
class ManagerReminderEvent:
    """Auditable notification event emitted when reminder SLA elapses (AC-011)."""

    ticket_id: str
    manager_id: str
    employee_id: str
    ticket_type: TicketType
    sent_at: datetime
    urgency: str
    summary: str
    channel: str = "teams"
    job_id: str = ""


@dataclass(frozen=True, slots=True)
class HREscalationEvent:
    """Auditable notification event emitted when escalation SLA elapses (AC-012)."""

    ticket_id: str
    escalated_at: datetime
    queue_name: str
    previous_status: TicketStatus
    new_status: TicketStatus
    manager_id: str
    employee_id: str
    channel: str = SLA_CHANNEL
    job_id: str = ""


@dataclass(frozen=True, slots=True)
class SLAAuditEvent:
    """Attributable record of one SLA timer execution or suppression."""

    audit_id: str
    actor_id: str
    action: str
    ticket_id: str
    channel: str
    occurred_at: datetime
    previous_status: TicketStatus
    new_status: TicketStatus
    details: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SLAProcessingResult:
    """Outcome of attempting to process an SLA job."""

    job_id: str
    ticket_id: str
    job_type: SLAJobType
    action_taken: bool
    status: SLAJobStatus
    ticket_status_before: TicketStatus
    ticket_status_after: TicketStatus
    message: str
    reminder_event: ManagerReminderEvent | None = None
    escalation_event: HREscalationEvent | None = None
    audit_event: SLAAuditEvent | LifecycleEvent | None = None


class TicketStore(Protocol):
    """Protocol for authoritative ticket persistence and retrieval."""

    def get_ticket(self, ticket_id: str) -> Ticket | None:
        """Fetch ticket by ID."""
        ...

    def save_ticket(self, ticket: Ticket) -> None:
        """Save updated ticket state."""
        ...


class SLAJobStore(Protocol):
    """Protocol for durable SLA job scheduling and state tracking."""

    def schedule_job(self, job: SLAJob) -> None:
        """Schedule a new SLA job."""
        ...

    def get_job(self, job_id: str) -> SLAJob | None:
        """Retrieve job by ID."""
        ...

    def get_pending_jobs(self, as_of: datetime) -> list[SLAJob]:
        """Fetch all scheduled jobs due on or before as_of."""
        ...

    def update_job(self, job: SLAJob) -> None:
        """Update job status and execution metadata."""
        ...

    def get_jobs_for_ticket(self, ticket_id: str) -> list[SLAJob]:
        """Fetch all jobs associated with a ticket."""
        ...


class InMemoryTicketStore:
    """Thread-safe in-memory ticket store for testing and local runtime."""

    def __init__(self, tickets: dict[str, Ticket] | None = None) -> None:
        self._tickets: dict[str, Ticket] = dict(tickets or {})
        self._lock = threading.Lock()

    def get_ticket(self, ticket_id: str) -> Ticket | None:
        with self._lock:
            return self._tickets.get(ticket_id)

    def save_ticket(self, ticket: Ticket) -> None:
        with self._lock:
            self._tickets[ticket.ticket_id] = ticket

    def all_tickets(self) -> list[Ticket]:
        with self._lock:
            return list(self._tickets.values())


class InMemorySLAJobStore:
    """Thread-safe in-memory SLA job store."""

    def __init__(self) -> None:
        self._jobs: dict[str, SLAJob] = {}
        self._lock = threading.Lock()

    def schedule_job(self, job: SLAJob) -> None:
        with self._lock:
            self._jobs[job.job_id] = job

    def get_job(self, job_id: str) -> SLAJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def get_pending_jobs(self, as_of: datetime) -> list[SLAJob]:
        normalized_as_of = as_of.astimezone(UTC)
        with self._lock:
            due = [
                j
                for j in self._jobs.values()
                if j.status == SLAJobStatus.SCHEDULED
                and j.scheduled_at <= normalized_as_of
            ]
            due.sort(key=lambda j: j.scheduled_at)
            return due

    def update_job(self, job: SLAJob) -> None:
        with self._lock:
            self._jobs[job.job_id] = job

    def get_jobs_for_ticket(self, ticket_id: str) -> list[SLAJob]:
        with self._lock:
            return [j for j in self._jobs.values() if j.ticket_id == ticket_id]


class SLAEngine:
    """Asynchronous SLA Timer Scheduler and Processor."""

    def __init__(
        self,
        ticket_store: TicketStore,
        job_store: SLAJobStore | None = None,
        config: SLAConfiguration | None = None,
    ) -> None:
        self._ticket_store = ticket_store
        self._job_store: SLAJobStore = (
            job_store if job_store is not None else InMemorySLAJobStore()
        )
        self._config = config if config is not None else SLAConfiguration()
        self._audit_records: list[SLAAuditEvent] = []
        self._reminder_events: list[ManagerReminderEvent] = []
        self._escalation_events: list[HREscalationEvent] = []
        self._lock = threading.Lock()

    @property
    def config(self) -> SLAConfiguration:
        """Engine configuration."""
        return self._config

    @property
    def job_store(self) -> SLAJobStore:
        """Underlying job store."""
        return self._job_store

    @property
    def ticket_store(self) -> TicketStore:
        """Underlying ticket store."""
        return self._ticket_store

    @property
    def audit_records(self) -> list[SLAAuditEvent]:
        """Captured SLA audit events."""
        with self._lock:
            return list(self._audit_records)

    @property
    def reminder_events(self) -> list[ManagerReminderEvent]:
        """Dispatched manager reminder events."""
        with self._lock:
            return list(self._reminder_events)

    @property
    def escalation_events(self) -> list[HREscalationEvent]:
        """Dispatched HR escalation events."""
        with self._lock:
            return list(self._escalation_events)

    def schedule_sla_jobs(
        self,
        ticket: Ticket,
        *,
        base_time: datetime | None = None,
    ) -> tuple[SLAJob, SLAJob]:
        """Schedule SLA reminder and escalation jobs for a submitted ticket."""
        if base_time is not None:
            start_time = base_time
        else:
            submit_event = next(
                (
                    e
                    for e in ticket.audit_events
                    if e.action == LifecycleAction.SUBMIT
                    or e.new_status == TicketStatus.PENDING_APPROVAL
                ),
                None,
            )
            start_time = submit_event.occurred_at if submit_event else ticket.created_at

        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=UTC)
        else:
            start_time = start_time.astimezone(UTC)

        reminder_deadline = self._config.calculate_reminder_deadline(start_time)
        escalation_deadline = self._config.calculate_escalation_deadline(start_time)

        now = datetime.now(UTC)
        reminder_job = SLAJob(
            job_id=f"job-rem-{ticket.ticket_id}-{uuid.uuid4().hex[:8]}",
            ticket_id=ticket.ticket_id,
            job_type=SLAJobType.REMINDER,
            scheduled_at=reminder_deadline,
            created_at=now,
        )
        escalation_job = SLAJob(
            job_id=f"job-esc-{ticket.ticket_id}-{uuid.uuid4().hex[:8]}",
            ticket_id=ticket.ticket_id,
            job_type=SLAJobType.ESCALATION,
            scheduled_at=escalation_deadline,
            created_at=now,
        )

        self._job_store.schedule_job(reminder_job)
        self._job_store.schedule_job(escalation_job)
        return reminder_job, escalation_job

    def process_job(
        self,
        job_or_id: str | SLAJob,
        current_time: datetime,
    ) -> SLAProcessingResult:
        """Process an SLA job after re-checking ticket state (AC-011, AC-012, AC-013).

        Safely no-ops without duplicate transitions or duplicate audits if ticket
        is already decided (APPROVED/REJECTED), cancelled, or already escalated.
        """
        normalized_current_time = (
            current_time.replace(tzinfo=UTC)
            if current_time.tzinfo is None
            else current_time.astimezone(UTC)
        )

        job = (
            self._job_store.get_job(job_or_id)
            if isinstance(job_or_id, str)
            else job_or_id
        )
        if job is None:
            return SLAProcessingResult(
                job_id=str(job_or_id),
                ticket_id="UNKNOWN",
                job_type=SLAJobType.REMINDER,
                action_taken=False,
                status=SLAJobStatus.FAILED,
                ticket_status_before=TicketStatus.DRAFT,
                ticket_status_after=TicketStatus.DRAFT,
                message=f"Job {job_or_id} not found.",
            )

        # Thread-safe execution per job
        with self._lock:
            # Check 1: Has this job already executed or skipped?
            if job.status in (SLAJobStatus.EXECUTED, SLAJobStatus.SKIPPED):
                ticket = self._ticket_store.get_ticket(job.ticket_id)
                current_status = ticket.status if ticket else TicketStatus.DRAFT
                return SLAProcessingResult(
                    job_id=job.job_id,
                    ticket_id=job.ticket_id,
                    job_type=job.job_type,
                    action_taken=False,
                    status=job.status,
                    ticket_status_before=current_status,
                    ticket_status_after=current_status,
                    message=(
                        f"Job {job.job_id} already marked {job.status.value}; "
                        "safely no-op."
                    ),
                )

            # Check 2: Authoritative ticket state re-check from ticket store
            ticket = self._ticket_store.get_ticket(job.ticket_id)
            if ticket is None:
                job.status = SLAJobStatus.SKIPPED
                job.executed_at = normalized_current_time
                job.execution_reason = f"Ticket {job.ticket_id} not found."
                self._job_store.update_job(job)
                return SLAProcessingResult(
                    job_id=job.job_id,
                    ticket_id=job.ticket_id,
                    job_type=job.job_type,
                    action_taken=False,
                    status=SLAJobStatus.SKIPPED,
                    ticket_status_before=TicketStatus.DRAFT,
                    ticket_status_after=TicketStatus.DRAFT,
                    message=f"Ticket {job.ticket_id} does not exist in store.",
                )

            current_status = ticket.status

            # AC-013: Safe suppression on decided, cancelled, or escalated tickets
            if current_status is not TicketStatus.PENDING_APPROVAL:
                job.status = SLAJobStatus.SKIPPED
                job.executed_at = normalized_current_time
                job.execution_reason = (
                    f"Ticket {ticket.ticket_id} is in non-pending status "
                    f"'{current_status.value}'. Suppressed without action."
                )
                self._job_store.update_job(job)
                return SLAProcessingResult(
                    job_id=job.job_id,
                    ticket_id=job.ticket_id,
                    job_type=job.job_type,
                    action_taken=False,
                    status=SLAJobStatus.SKIPPED,
                    ticket_status_before=current_status,
                    ticket_status_after=current_status,
                    message=(
                        f"Ticket {ticket.ticket_id} is {current_status.value}. "
                        "SLA action safely suppressed without duplicate transition."
                    ),
                )

            # Handle Reminder Job (AC-011)
            if job.job_type is SLAJobType.REMINDER:
                # Check if reminder already executed for this ticket
                already_reminded = any(
                    r.ticket_id == ticket.ticket_id for r in self._reminder_events
                )
                if already_reminded:
                    job.status = SLAJobStatus.SKIPPED
                    job.executed_at = normalized_current_time
                    job.execution_reason = (
                        f"Reminder already dispatched for ticket {ticket.ticket_id}."
                    )
                    self._job_store.update_job(job)
                    return SLAProcessingResult(
                        job_id=job.job_id,
                        ticket_id=job.ticket_id,
                        job_type=job.job_type,
                        action_taken=False,
                        status=SLAJobStatus.SKIPPED,
                        ticket_status_before=current_status,
                        ticket_status_after=current_status,
                        message="Duplicate reminder job safely suppressed.",
                    )

                reminder_event = ManagerReminderEvent(
                    ticket_id=ticket.ticket_id,
                    manager_id=ticket.manager_id,
                    employee_id=ticket.employee_id,
                    ticket_type=ticket.ticket_type,
                    sent_at=normalized_current_time,
                    urgency=self._config.urgency_level,
                    summary=(
                        f"Urgent reminder: Pending {ticket.ticket_type.value} request "
                        f"requires review for ticket {ticket.ticket_id}."
                    ),
                    channel="teams",
                    job_id=job.job_id,
                )
                audit_event = SLAAuditEvent(
                    audit_id=f"audit-sla-{uuid.uuid4().hex[:8]}",
                    actor_id=SYSTEM_ACTOR_ID,
                    action="SLA_REMINDER",
                    ticket_id=ticket.ticket_id,
                    channel=SLA_CHANNEL,
                    occurred_at=normalized_current_time,
                    previous_status=current_status,
                    new_status=current_status,
                    details={
                        "manager_id": ticket.manager_id,
                        "job_id": job.job_id,
                        "urgency": self._config.urgency_level,
                    },
                )

                self._reminder_events.append(reminder_event)
                self._audit_records.append(audit_event)

                job.status = SLAJobStatus.EXECUTED
                job.executed_at = normalized_current_time
                job.execution_reason = "48h business SLA reminder delivered to manager."
                self._job_store.update_job(job)

                return SLAProcessingResult(
                    job_id=job.job_id,
                    ticket_id=job.ticket_id,
                    job_type=job.job_type,
                    action_taken=True,
                    status=SLAJobStatus.EXECUTED,
                    ticket_status_before=current_status,
                    ticket_status_after=current_status,
                    message="Urgent manager reminder dispatched and audited.",
                    reminder_event=reminder_event,
                    audit_event=audit_event,
                )

            # Handle Escalation Job (AC-012)
            if job.job_type is SLAJobType.ESCALATION:
                updated_ticket = transition_ticket(
                    ticket,
                    TicketStatus.ESCALATED,
                    actor_id=SYSTEM_ACTOR_ID,
                    channel=SLA_CHANNEL,
                    occurred_at=normalized_current_time,
                    action=LifecycleAction.ESCALATE,
                )
                self._ticket_store.save_ticket(updated_ticket)

                escalation_event = HREscalationEvent(
                    ticket_id=ticket.ticket_id,
                    escalated_at=normalized_current_time,
                    queue_name=self._config.hr_queue_name,
                    previous_status=current_status,
                    new_status=TicketStatus.ESCALATED,
                    manager_id=ticket.manager_id,
                    employee_id=ticket.employee_id,
                    channel=SLA_CHANNEL,
                    job_id=job.job_id,
                )
                self._escalation_events.append(escalation_event)

                job.status = SLAJobStatus.EXECUTED
                job.executed_at = normalized_current_time
                job.execution_reason = (
                    "72h SLA escalation triggered. Ticket routed to HR queue."
                )
                self._job_store.update_job(job)

                # The latest lifecycle event on the ticket is the escalation audit
                latest_audit = updated_ticket.audit_events[-1]

                return SLAProcessingResult(
                    job_id=job.job_id,
                    ticket_id=job.ticket_id,
                    job_type=job.job_type,
                    action_taken=True,
                    status=SLAJobStatus.EXECUTED,
                    ticket_status_before=current_status,
                    ticket_status_after=TicketStatus.ESCALATED,
                    message="Unreviewed ticket escalated to HR Operations queue.",
                    escalation_event=escalation_event,
                    audit_event=latest_audit,
                )

            # Unknown job type fallback
            return SLAProcessingResult(
                job_id=job.job_id,
                ticket_id=job.ticket_id,
                job_type=job.job_type,
                action_taken=False,
                status=SLAJobStatus.FAILED,
                ticket_status_before=current_status,
                ticket_status_after=current_status,
                message=f"Unsupported SLA job type: {job.job_type}",
            )

    def process_due_jobs(self, current_time: datetime) -> list[SLAProcessingResult]:
        """Fetch and execute all pending SLA jobs due at or before current_time."""
        due_jobs = self._job_store.get_pending_jobs(current_time)
        results: list[SLAProcessingResult] = []
        for job in due_jobs:
            result = self.process_job(job, current_time)
            results.append(result)
        return results


def create_default_sla_engine(
    tickets: dict[str, Ticket] | None = None,
    config: SLAConfiguration | None = None,
) -> SLAEngine:
    """Convenience factory creating an SLAEngine with in-memory stores."""
    ticket_store = InMemoryTicketStore(tickets)
    job_store = InMemorySLAJobStore()
    return SLAEngine(
        ticket_store=ticket_store,
        job_store=job_store,
        config=config,
    )
