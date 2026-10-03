"""Deterministic ticket contracts and lifecycle behavior."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Final

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

BORROWING_CEILING_DAYS: Final[Decimal] = Decimal("3")
CERTIFIED_MEDICAL_LEAVE_STATUS: Final[str] = "Certified Medical Leave Approved by HR"
_SCHEMA_PATH: Final[Path] = Path(__file__).parent / "schemas" / "ticket.schema.json"
_TICKET_SCHEMA: Final[dict[str, object]] = json.loads(
    _SCHEMA_PATH.read_text(encoding="utf-8")
)
Draft202012Validator.check_schema(_TICKET_SCHEMA)
_TICKET_VALIDATOR: Final[Draft202012Validator] = Draft202012Validator(
    _TICKET_SCHEMA,
    format_checker=FormatChecker(),
)


class TicketType(StrEnum):
    """Ticket categories accepted by the initial domain model."""

    ANNUAL_LEAVE = "ANNUAL_LEAVE"
    SICK_LEAVE = "SICK_LEAVE"
    OVERTIME = "OVERTIME"
    ATTENDANCE_ADJUSTMENT = "ATTENDANCE_ADJUSTMENT"


class TicketStatus(StrEnum):
    """Supported lifecycle states for a time and leave ticket."""

    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    CANCELLED = "CANCELLED"


class LifecycleAction(StrEnum):
    """Explicit lifecycle actions recorded in audit events."""

    SUBMIT = "SUBMIT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"
    CANCEL = "CANCEL"


class TicketSchemaError(ValueError):
    """Raised when a ticket violates the published JSON Schema contract."""


class TicketRuleViolation(ValueError):
    """Raised when a ticket action violates a deterministic business rule."""


class InvalidTransitionError(ValueError):
    """Raised when a lifecycle transition is not allowed."""


@dataclass(frozen=True, slots=True)
class SensitiveTicketData:
    """Restricted ticket fields excluded from manager-facing projections."""

    medical_reason: str | None = None
    medical_notes: str | None = None
    compensation_amount: Decimal | None = None


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
    """Attributable record of one accepted lifecycle transition."""

    actor_id: str
    action: LifecycleAction
    channel: str
    occurred_at: datetime
    previous_status: TicketStatus
    new_status: TicketStatus
    rejection_reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.action, LifecycleAction):
            try:
                object.__setattr__(self, "action", LifecycleAction(str(self.action)))
            except ValueError as error:
                raise TicketRuleViolation(
                    f"Invalid lifecycle action {self.action!r}; must be one of "
                    f"{', '.join(a.value for a in LifecycleAction)}."
                ) from error


@dataclass(frozen=True, slots=True)
class Ticket:
    """Validated domain state for a time or leave request."""

    ticket_id: str
    employee_id: str
    manager_id: str
    ticket_type: TicketType
    created_at: datetime
    status: TicketStatus = TicketStatus.DRAFT
    start_date: date | None = None
    end_date: date | None = None
    accrued_leave_days: Decimal | None = None
    requested_leave_days: Decimal | None = None
    requested_hours: Decimal | None = None
    employee_reason: str | None = None
    sensitive_data: SensitiveTicketData = field(default_factory=SensitiveTicketData)
    rejection_reason: str | None = None
    audit_events: tuple[LifecycleEvent, ...] = ()

    def to_payload(self) -> dict[str, object]:
        """Return the JSON-compatible payload validated by the ticket schema."""
        return {
            "ticket_id": self.ticket_id,
            "employee_id": self.employee_id,
            "manager_id": self.manager_id,
            "ticket_type": self.ticket_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "accrued_leave_days": _number(self.accrued_leave_days),
            "requested_leave_days": _number(self.requested_leave_days),
            "requested_hours": _number(self.requested_hours),
            "employee_reason": self.employee_reason,
            "sensitive_data": {
                "medical_reason": self.sensitive_data.medical_reason,
                "medical_notes": self.sensitive_data.medical_notes,
                "compensation_amount": _number(self.sensitive_data.compensation_amount),
            },
            "rejection_reason": self.rejection_reason,
        }

    def manager_view(self) -> ManagerTicketView:
        """Return an allowlisted manager view without private fields.

        Enforces a certification-only disclosure boundary for SICK_LEAVE per
        SOP-HR-042 and PRD NFR-008 so managers see certification status without
        sensitive medical details, employee reasons, or timing/quantity leakage.
        """
        if self.ticket_type is TicketType.SICK_LEAVE:
            return ManagerTicketView(
                ticket_id=self.ticket_id,
                ticket_type=self.ticket_type,
                status=self.status,
                start_date=None,
                end_date=None,
                requested_leave_days=None,
                requested_hours=None,
                certification_status=CERTIFIED_MEDICAL_LEAVE_STATUS,
            )
        return ManagerTicketView(
            ticket_id=self.ticket_id,
            ticket_type=self.ticket_type,
            status=self.status,
            start_date=self.start_date,
            end_date=self.end_date,
            requested_leave_days=self.requested_leave_days,
            requested_hours=self.requested_hours,
            certification_status=None,
        )


@dataclass(frozen=True, slots=True)
class ManagerTicketView:
    """Allowlisted request summary intended for a manager-facing surface."""

    ticket_id: str
    ticket_type: TicketType
    status: TicketStatus
    start_date: date | None
    end_date: date | None
    requested_leave_days: Decimal | None
    requested_hours: Decimal | None
    certification_status: str | None = None


_ALLOWED_TRANSITIONS: Final[dict[TicketStatus, frozenset[TicketStatus]]] = {
    TicketStatus.DRAFT: frozenset(
        {TicketStatus.PENDING_APPROVAL, TicketStatus.CANCELLED}
    ),
    TicketStatus.PENDING_APPROVAL: frozenset(
        {
            TicketStatus.APPROVED,
            TicketStatus.REJECTED,
            TicketStatus.ESCALATED,
            TicketStatus.CANCELLED,
        }
    ),
    TicketStatus.ESCALATED: frozenset(
        {TicketStatus.APPROVED, TicketStatus.REJECTED, TicketStatus.CANCELLED}
    ),
    TicketStatus.APPROVED: frozenset(),
    TicketStatus.REJECTED: frozenset(),
    TicketStatus.CANCELLED: frozenset(),
}

_DEFAULT_ACTIONS: Final[dict[TicketStatus, LifecycleAction]] = {
    TicketStatus.PENDING_APPROVAL: LifecycleAction.SUBMIT,
    TicketStatus.APPROVED: LifecycleAction.APPROVE,
    TicketStatus.REJECTED: LifecycleAction.REJECT,
    TicketStatus.ESCALATED: LifecycleAction.ESCALATE,
    TicketStatus.CANCELLED: LifecycleAction.CANCEL,
}


def validate_ticket(ticket: Ticket) -> None:
    """Validate a ticket against the versioned JSON Schema contract.

    Raises:
        TicketSchemaError: If a ticket field violates the schema.
    """
    validate_ticket_payload(ticket.to_payload())


def validate_ticket_payload(payload: object) -> None:
    """Validate untrusted ticket data against the versioned JSON Schema contract.

    Raises:
        TicketSchemaError: If the payload violates the schema.
    """
    try:
        _TICKET_VALIDATOR.validate(payload)
    except ValidationError as error:
        field_path = ".".join(str(part) for part in error.absolute_path) or "<root>"
        constraint = str(error.validator or "schema")
        raise TicketSchemaError(
            f"Ticket field {field_path!r} violates the "
            f"{constraint!r} schema constraint."
        ) from error


def submit_ticket(
    ticket: Ticket,
    *,
    actor_id: str,
    channel: str,
    occurred_at: datetime,
) -> Ticket:
    """Validate and submit a draft ticket for approval.

    Raises:
        InvalidTransitionError: If the ticket is not a draft.
        TicketRuleViolation: If leave exceeds the balance plus borrowing ceiling.
        TicketSchemaError: If the ticket violates the JSON Schema contract.
    """
    if ticket.status is not TicketStatus.DRAFT:
        raise InvalidTransitionError(
            f"Only a DRAFT ticket can be submitted; received {ticket.status.value}."
        )
    validate_ticket(ticket)
    if ticket.ticket_type is TicketType.ANNUAL_LEAVE:
        _validate_annual_leave_balance(ticket)
    return transition_ticket(
        ticket,
        TicketStatus.PENDING_APPROVAL,
        actor_id=actor_id,
        channel=channel,
        occurred_at=occurred_at,
        action=LifecycleAction.SUBMIT,
    )


def transition_ticket(
    ticket: Ticket,
    target_status: TicketStatus,
    *,
    actor_id: str,
    channel: str,
    occurred_at: datetime,
    action: LifecycleAction | str | None = None,
    rejection_reason: str | None = None,
) -> Ticket:
    """Apply one allowed, attributable lifecycle transition.

    Raises:
        InvalidTransitionError: If the transition is not allowed.
        TicketRuleViolation: If a rejection reason or action is missing or invalid.
        TicketSchemaError: If the resulting ticket violates the JSON Schema.
    """
    if target_status not in _ALLOWED_TRANSITIONS[ticket.status]:
        raise InvalidTransitionError(
            f"Transition from {ticket.status.value} to {target_status.value} "
            "is not allowed."
        )
    normalized_reason: str | None = None
    if target_status is TicketStatus.REJECTED:
        normalized_reason = rejection_reason.strip() if rejection_reason else ""
        if not normalized_reason:
            raise TicketRuleViolation(
                "A non-empty rejection reason is required before rejecting a ticket."
            )
    _validate_transition_metadata(actor_id, channel, occurred_at)
    if action is not None:
        if isinstance(action, LifecycleAction):
            resolved_action = action
        else:
            try:
                resolved_action = LifecycleAction(str(action))
            except ValueError as error:
                raise TicketRuleViolation(
                    f"Invalid lifecycle action {action!r}; must be one of "
                    f"{', '.join(a.value for a in LifecycleAction)}."
                ) from error
    else:
        if target_status not in _DEFAULT_ACTIONS:
            raise TicketRuleViolation(
                "No default lifecycle action mapped for target status "
                f"{target_status.value}."
            )
        resolved_action = _DEFAULT_ACTIONS[target_status]

    normalized_time = occurred_at.astimezone(UTC)
    event = LifecycleEvent(
        actor_id=actor_id,
        action=resolved_action,
        channel=channel,
        occurred_at=normalized_time,
        previous_status=ticket.status,
        new_status=target_status,
        rejection_reason=normalized_reason,
    )
    updated_ticket = replace(
        ticket,
        status=target_status,
        rejection_reason=normalized_reason
        if target_status is TicketStatus.REJECTED
        else ticket.rejection_reason,
        audit_events=(*ticket.audit_events, event),
    )
    validate_ticket(updated_ticket)
    return updated_ticket


def _validate_annual_leave_balance(ticket: Ticket) -> None:
    """Enforce the accrued balance plus the fixed borrowing ceiling."""
    if ticket.accrued_leave_days is None or ticket.requested_leave_days is None:
        raise TicketRuleViolation(
            "Annual leave submission requires accrued and requested leave-day values."
        )
    maximum_days = ticket.accrued_leave_days + BORROWING_CEILING_DAYS
    if ticket.requested_leave_days > maximum_days:
        raise TicketRuleViolation(
            f"Requested {ticket.requested_leave_days} days exceeds accrued balance "
            f"{ticket.accrued_leave_days} days plus the three-day borrowing ceiling "
            f"(maximum {maximum_days} days)."
        )


def _validate_transition_metadata(
    actor_id: str,
    channel: str,
    occurred_at: datetime,
) -> None:
    """Require attributable transition metadata and a timezone-aware timestamp."""
    if not actor_id.strip():
        raise TicketRuleViolation("A non-empty actor ID is required for a transition.")
    if not channel.strip():
        raise TicketRuleViolation("A non-empty channel is required for a transition.")
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise TicketRuleViolation(
            "Transition timestamps must include a timezone and are stored in UTC."
        )


def _number(value: Decimal | None) -> int | float | None:
    """Convert exact domain decimals to JSON Schema-compatible numeric values."""
    if value is None:
        return None
    if value == value.to_integral_value():
        return int(value)
    return float(value)
