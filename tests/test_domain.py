"""Acceptance tests for the ticket domain and P01 lifecycle behavior."""

from dataclasses import asdict, replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from hr_time_leave.domain import (
    InvalidTransitionError,
    SensitiveTicketData,
    Ticket,
    TicketRuleViolation,
    TicketSchemaError,
    TicketStatus,
    TicketType,
    submit_ticket,
    transition_ticket,
    validate_ticket_payload,
)


@pytest.fixture()
def annual_leave_draft() -> Ticket:
    """Create a schema-valid annual leave draft for domain tests."""
    return Ticket(
        ticket_id="ticket-001",
        employee_id="employee-001",
        manager_id="manager-001",
        ticket_type=TicketType.ANNUAL_LEAVE,
        created_at=datetime(2026, 9, 29, 1, 0, tzinfo=UTC),
        start_date=date(2026, 10, 5),
        end_date=date(2026, 10, 6),
        accrued_leave_days=Decimal("5"),
        requested_leave_days=Decimal("2"),
        requested_hours=Decimal("16"),
    )


def test_given_valid_annual_leave_when_submitted_then_pending_approval(
    annual_leave_draft: Ticket,
) -> None:
    # Arrange
    submission_time = datetime(2026, 9, 29, 1, 5, tzinfo=UTC)

    # Act
    submitted_ticket = submit_ticket(
        annual_leave_draft,
        actor_id="employee-001",
        channel="teams",
        occurred_at=submission_time,
    )

    # Assert
    assert submitted_ticket.status is TicketStatus.PENDING_APPROVAL
    assert submitted_ticket.audit_events[-1].previous_status is TicketStatus.DRAFT
    assert submitted_ticket.audit_events[-1].new_status is TicketStatus.PENDING_APPROVAL


def test_given_request_above_borrowing_ceiling_when_submitted_then_blocked_with_rule(
    annual_leave_draft: Ticket,
) -> None:
    # Arrange
    over_borrowing_ticket = replace(
        annual_leave_draft,
        accrued_leave_days=Decimal("1"),
        requested_leave_days=Decimal("5"),
    )

    # Act and Assert
    with pytest.raises(TicketRuleViolation, match="three-day borrowing ceiling"):
        submit_ticket(
            over_borrowing_ticket,
            actor_id="employee-001",
            channel="teams",
            occurred_at=datetime(2026, 9, 29, 1, 5, tzinfo=UTC),
        )


def test_given_rejection_without_reason_when_transitioned_then_refused(
    annual_leave_draft: Ticket,
) -> None:
    # Arrange
    pending_ticket = submit_ticket(
        annual_leave_draft,
        actor_id="employee-001",
        channel="teams",
        occurred_at=datetime(2026, 9, 29, 1, 5, tzinfo=UTC),
    )

    # Act and Assert
    with pytest.raises(TicketRuleViolation, match="non-empty rejection reason"):
        transition_ticket(
            pending_ticket,
            TicketStatus.REJECTED,
            actor_id="manager-001",
            channel="teams",
            occurred_at=datetime(2026, 9, 29, 2, 0, tzinfo=UTC),
        )


def test_given_rejection_with_reason_when_transitioned_then_rejected(
    annual_leave_draft: Ticket,
) -> None:
    # Arrange
    pending_ticket = submit_ticket(
        annual_leave_draft,
        actor_id="employee-001",
        channel="teams",
        occurred_at=datetime(2026, 9, 29, 1, 5, tzinfo=UTC),
    )

    # Act
    rejected_ticket = transition_ticket(
        pending_ticket,
        TicketStatus.REJECTED,
        actor_id="manager-001",
        channel="teams",
        occurred_at=datetime(2026, 9, 29, 2, 0, tzinfo=UTC),
        rejection_reason="Dates conflict with team coverage.",
    )

    # Assert
    assert rejected_ticket.status is TicketStatus.REJECTED
    assert rejected_ticket.rejection_reason == "Dates conflict with team coverage."
    assert rejected_ticket.audit_events[-1].rejection_reason == (
        "Dates conflict with team coverage."
    )


def test_given_sensitive_ticket_fields_when_projected_for_manager_then_omitted(
    annual_leave_draft: Ticket,
) -> None:
    # Arrange
    ticket_with_private_data = replace(
        annual_leave_draft,
        employee_reason="private employee health details",
        sensitive_data=SensitiveTicketData(
            medical_reason="private diagnosis",
            medical_notes="private clinical notes",
            compensation_amount=Decimal("1250.50"),
        ),
    )

    # Act
    projection = asdict(ticket_with_private_data.manager_view())

    # Assert
    assert "private diagnosis" not in repr(projection)
    assert "private clinical notes" not in repr(projection)
    assert "private employee health details" not in repr(projection)
    assert "1250.50" not in repr(projection)
    assert "sensitive_data" not in projection
    assert "employee_reason" not in projection


def test_given_unknown_ticket_property_when_schema_validated_then_rejected(
    annual_leave_draft: Ticket,
) -> None:
    # Arrange
    invalid_payload = annual_leave_draft.to_payload()
    invalid_payload["unexpected_property"] = "not allowed"

    # Act and Assert
    with pytest.raises(TicketSchemaError, match="additionalProperties"):
        validate_ticket_payload(invalid_payload)


def test_given_approved_ticket_when_transitioned_again_then_rejected(
    annual_leave_draft: Ticket,
) -> None:
    # Arrange
    pending_ticket = submit_ticket(
        annual_leave_draft,
        actor_id="employee-001",
        channel="teams",
        occurred_at=datetime(2026, 9, 29, 1, 5, tzinfo=UTC),
    )
    approved_ticket = transition_ticket(
        pending_ticket,
        TicketStatus.APPROVED,
        actor_id="manager-001",
        channel="teams",
        occurred_at=datetime(2026, 9, 29, 2, 0, tzinfo=UTC),
    )

    # Act and Assert
    with pytest.raises(InvalidTransitionError, match="APPROVED to REJECTED"):
        transition_ticket(
            approved_ticket,
            TicketStatus.REJECTED,
            actor_id="manager-001",
            channel="teams",
            occurred_at=datetime(2026, 9, 29, 2, 1, tzinfo=UTC),
            rejection_reason="A later decision is not allowed.",
        )
