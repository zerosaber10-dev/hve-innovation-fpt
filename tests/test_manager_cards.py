"""Unit tests for Microsoft Teams manager approval card and action handler.

Verifies:
- AC-008: Sanitized card generation with zero sensitive PHI / compensation leakage.
- AC-009: Protected approval transition, audit event, and employee notification.
- AC-010: Mandatory rejection reason, refusal without reason, and rejection transition.
- Direct-report authorization, status checks, and idempotent action token handling.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from hr_time_leave.domain import (
    CERTIFIED_MEDICAL_LEAVE_STATUS,
    LifecycleAction,
    SensitiveTicketData,
    Ticket,
    TicketRuleViolation,
    TicketStatus,
    TicketType,
    submit_ticket,
)
from hr_time_leave.manager_cards import (
    DuplicateActionTokenError,
    InMemoryActionTokenStore,
    ManagerAuthorizationError,
    RejectionReasonRequiredError,
    TicketNotPendingError,
    UnsupportedManagerActionError,
    build_manager_approval_card,
    generate_action_token,
    handle_card_action_payload,
    handle_manager_action,
)


def _make_pending_annual_leave_ticket(
    ticket_id: str = "TCK-ANNUAL-101",
    employee_id: str = "emp_alice_001",
    manager_id: str = "mgr_bob_002",
) -> Ticket:
    """Create a valid PENDING_APPROVAL annual leave ticket for testing."""
    now = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
    draft = Ticket(
        ticket_id=ticket_id,
        employee_id=employee_id,
        manager_id=manager_id,
        ticket_type=TicketType.ANNUAL_LEAVE,
        created_at=now,
        status=TicketStatus.DRAFT,
        start_date=date(2026, 10, 15),
        end_date=date(2026, 10, 16),
        accrued_leave_days=Decimal("15"),
        requested_leave_days=Decimal("2"),
        employee_reason="Family vacation to the coast",
        sensitive_data=SensitiveTicketData(
            medical_reason=None,
            medical_notes=None,
            compensation_amount=Decimal("450.00"),
        ),
    )
    return submit_ticket(
        draft,
        actor_id=employee_id,
        channel="web_portal",
        occurred_at=now,
    )


def _make_pending_sick_leave_ticket(
    ticket_id: str = "TCK-SICK-202",
    employee_id: str = "emp_clara_003",
    manager_id: str = "mgr_bob_002",
) -> Ticket:
    """Create a valid PENDING_APPROVAL sick leave ticket with sensitive health data."""
    now = datetime(2026, 10, 2, 8, 30, tzinfo=UTC)
    draft = Ticket(
        ticket_id=ticket_id,
        employee_id=employee_id,
        manager_id=manager_id,
        ticket_type=TicketType.SICK_LEAVE,
        created_at=now,
        status=TicketStatus.DRAFT,
        start_date=date(2026, 10, 2),
        end_date=date(2026, 10, 5),
        accrued_leave_days=Decimal("10"),
        requested_leave_days=Decimal("3"),
        employee_reason="Severe illness, unable to work",
        sensitive_data=SensitiveTicketData(
            medical_reason="Acute bronchitis infection",
            medical_notes="Doctor note Dr. Smith clinic rx-99214 bed rest",
            compensation_amount=Decimal("1250.00"),
        ),
    )
    return submit_ticket(
        draft,
        actor_id=employee_id,
        channel="msteams",
        occurred_at=now,
    )


# --- AC-008: Sanitized Card Generation Tests ---


def test_given_sick_leave_when_card_built_then_zero_leakage_and_certified() -> None:
    """AC-008: Verify zero leakage of medical notes/diagnosis and compensation."""
    ticket = _make_pending_sick_leave_ticket()
    token = "act_test_token_sick_01"

    card = build_manager_approval_card(ticket, action_token=token)
    card_json = json.dumps(card)

    # 1. Zero leakage assertions: No sensitive medical notes, diagnoses,
    # compensation, or employee reasons
    assert "Acute bronchitis infection" not in card_json
    assert "bronchitis" not in card_json.lower()
    assert "Doctor note Dr. Smith" not in card_json
    assert "rx-99214" not in card_json
    assert "1250.00" not in card_json
    assert "1250" not in card_json
    assert "Severe illness, unable to work" not in card_json
    assert "medical_notes" not in card_json
    assert "medical_reason" not in card_json
    assert "compensation_amount" not in card_json

    # 2. Absence of leave timing/duration for sick leave per
    # certification-only disclosure boundary
    assert "2026-10-02" not in card_json
    assert "2026-10-05" not in card_json

    # 3. Certified medical status is disclosed
    assert CERTIFIED_MEDICAL_LEAVE_STATUS in card_json

    # 4. Card schema and basic structure
    assert card["type"] == "AdaptiveCard"
    assert card["version"] == "1.5"
    assert len(card["actions"]) == 2
    assert card["actions"][0]["title"] == "Approve"
    assert card["actions"][1]["title"] == "Reject"


def test_given_annual_leave_when_card_built_then_shows_summary_and_actions() -> None:
    """AC-008: Verify permitted request summary for annual leave."""
    ticket = _make_pending_annual_leave_ticket()
    card = build_manager_approval_card(ticket)
    card_json = json.dumps(card)

    # Permitted fields present
    assert ticket.ticket_id in card_json
    assert ticket.employee_id in card_json
    assert "Annual Leave" in card_json
    assert "2026-10-15" in card_json
    assert "2026-10-16" in card_json
    assert "Requested Days" in card_json

    # Sensitive/employee reasons excluded
    assert "Family vacation" not in card_json
    assert "450.00" not in card_json


# --- AC-009: Approval Action & Notification Tests ---


def test_given_manager_when_approving_then_transitions_and_notifies() -> None:
    """AC-009: Manager selects Approve -> APPROVED, audit, notification."""
    ticket = _make_pending_annual_leave_ticket()
    store = InMemoryActionTokenStore()
    decision_time = datetime(2026, 10, 2, 14, 0, tzinfo=UTC)
    token = generate_action_token(ticket.ticket_id, ticket.manager_id)

    result = handle_manager_action(
        ticket,
        LifecycleAction.APPROVE,
        caller_id=ticket.manager_id,
        action_token=token,
        channel="msteams",
        occurred_at=decision_time,
        token_store=store,
    )

    # 1. State transition
    assert result.ticket.status == TicketStatus.APPROVED
    assert result.action == LifecycleAction.APPROVE
    assert not result.is_idempotent_replay

    # 2. Audit event
    assert len(result.ticket.audit_events) == 2  # SUBMIT + APPROVE
    audit = result.audit_event
    assert audit.action == LifecycleAction.APPROVE
    assert audit.actor_id == ticket.manager_id
    assert audit.channel == "msteams"
    assert audit.previous_status == TicketStatus.PENDING_APPROVAL
    assert audit.new_status == TicketStatus.APPROVED
    assert audit.occurred_at == decision_time

    # 3. Employee notification
    notification = result.notification
    assert notification.recipient_id == ticket.employee_id
    assert notification.ticket_id == ticket.ticket_id
    assert notification.status == TicketStatus.APPROVED
    assert notification.decision_by == ticket.manager_id
    assert "approved" in notification.message.lower()
    assert notification.rejection_reason is None


# --- AC-010: Rejection Action & Reason Tests ---


def test_given_manager_rejection_without_reason_then_refuses_decision() -> None:
    """AC-010: Rejection without explicit reason is refused and raises error."""
    ticket = _make_pending_annual_leave_ticket()
    token = generate_action_token(ticket.ticket_id, ticket.manager_id)

    # Empty reason
    with pytest.raises(
        RejectionReasonRequiredError, match="non-empty rejection reason"
    ):
        handle_manager_action(
            ticket,
            LifecycleAction.REJECT,
            caller_id=ticket.manager_id,
            action_token=token,
            rejection_reason="",
        )

    # Whitespace-only reason
    with pytest.raises(
        RejectionReasonRequiredError, match="non-empty rejection reason"
    ):
        handle_manager_action(
            ticket,
            "REJECT",
            caller_id=ticket.manager_id,
            action_token=token,
            rejection_reason="   \t\n  ",
        )

    # Ticket remains pending
    assert ticket.status == TicketStatus.PENDING_APPROVAL


def test_given_rejection_with_reason_then_transitions_and_records() -> None:
    """AC-010: Rejection with explicit reason transitions to REJECTED."""
    ticket = _make_pending_annual_leave_ticket()
    token = generate_action_token(ticket.ticket_id, ticket.manager_id)
    reason = "Team headcount coverage required during quarterly release window"
    decision_time = datetime(2026, 10, 2, 15, 30, tzinfo=UTC)

    result = handle_manager_action(
        ticket,
        LifecycleAction.REJECT,
        caller_id=ticket.manager_id,
        action_token=token,
        channel="msteams",
        occurred_at=decision_time,
        rejection_reason=reason,
    )

    # 1. State transition & reason
    assert result.ticket.status == TicketStatus.REJECTED
    assert result.ticket.rejection_reason == reason
    assert result.action == LifecycleAction.REJECT

    # 2. Audit event
    assert result.audit_event.action == LifecycleAction.REJECT
    assert result.audit_event.actor_id == ticket.manager_id
    assert result.audit_event.rejection_reason == reason

    # 3. Notification
    assert result.notification.recipient_id == ticket.employee_id
    assert result.notification.status == TicketStatus.REJECTED
    assert result.notification.rejection_reason == reason
    assert reason in result.notification.message


# --- Authorization & State Precondition Tests ---


def test_given_unauthorized_caller_when_action_attempted_then_denies_access() -> None:
    """Verify server-side direct-report authorization check fails for non-managers."""
    ticket = _make_pending_annual_leave_ticket(manager_id="mgr_bob_002")
    token = "act_unauthorized_test"

    with pytest.raises(ManagerAuthorizationError, match="not authorized"):
        handle_manager_action(
            ticket,
            LifecycleAction.APPROVE,
            caller_id="mgr_imposter_999",
            action_token=token,
        )


def test_given_non_pending_ticket_when_action_attempted_then_rejects() -> None:
    """Verify actions on non-PENDING_APPROVAL tickets are refused."""
    ticket = _make_pending_annual_leave_ticket()
    token = "act_token_already_approved"

    # First approve the ticket
    approved_result = handle_manager_action(
        ticket,
        LifecycleAction.APPROVE,
        caller_id=ticket.manager_id,
        action_token=token,
    )
    approved_ticket = approved_result.ticket

    # Now attempt another action with a different token
    with pytest.raises(TicketNotPendingError, match="PENDING_APPROVAL"):
        handle_manager_action(
            approved_ticket,
            LifecycleAction.REJECT,
            caller_id=ticket.manager_id,
            action_token="act_different_token",
            rejection_reason="Changed my mind",
        )


# --- Idempotency & Action Token Tests ---


def test_given_identical_token_replayed_then_returns_cached_result_safely() -> None:
    """Verify idempotent token replay returns previous result safely."""
    ticket = _make_pending_annual_leave_ticket()
    store = InMemoryActionTokenStore()
    token = "act_idempotent_test_01"

    # Initial action
    first_result = handle_manager_action(
        ticket,
        LifecycleAction.APPROVE,
        caller_id=ticket.manager_id,
        action_token=token,
        token_store=store,
    )
    assert not first_result.is_idempotent_replay
    assert len(first_result.ticket.audit_events) == 2

    # Replayed action with identical token
    replay_result = handle_manager_action(
        ticket,
        LifecycleAction.APPROVE,
        caller_id=ticket.manager_id,
        action_token=token,
        token_store=store,
    )
    assert replay_result.is_idempotent_replay
    assert replay_result.ticket.ticket_id == first_result.ticket.ticket_id
    assert replay_result.ticket.status == TicketStatus.APPROVED
    # No duplicate audit events added
    assert len(replay_result.ticket.audit_events) == 2


def test_given_token_reused_for_different_ticket_then_raises_duplicate_error() -> None:
    """Verify an action token cannot be reused across different tickets."""
    ticket1 = _make_pending_annual_leave_ticket(ticket_id="TCK-001")
    ticket2 = _make_pending_annual_leave_ticket(ticket_id="TCK-002")
    store = InMemoryActionTokenStore()
    token = "act_shared_token_attempt"

    handle_manager_action(
        ticket1,
        LifecycleAction.APPROVE,
        caller_id=ticket1.manager_id,
        action_token=token,
        token_store=store,
    )

    with pytest.raises(
        DuplicateActionTokenError, match="consumed for another operation"
    ):
        handle_manager_action(
            ticket2,
            LifecycleAction.APPROVE,
            caller_id=ticket2.manager_id,
            action_token=token,
            token_store=store,
        )


def test_given_blank_action_token_then_rejected() -> None:
    """Verify empty or blank action token is rejected."""
    ticket = _make_pending_annual_leave_ticket()

    with pytest.raises(DuplicateActionTokenError, match="non-empty action token"):
        handle_manager_action(
            ticket,
            LifecycleAction.APPROVE,
            caller_id=ticket.manager_id,
            action_token="   ",
        )


# --- Raw Card Payload Tests ---


def test_given_raw_card_payload_when_approve_then_succeeds() -> None:
    """Verify parsing and executing raw Teams card action payload."""
    ticket = _make_pending_annual_leave_ticket()
    token = "act_raw_payload_01"
    payload = {
        "action": "APPROVE",
        "ticket_id": ticket.ticket_id,
        "action_token": token,
    }

    result = handle_card_action_payload(
        payload,
        ticket=ticket,
        caller_id=ticket.manager_id,
    )
    assert result.ticket.status == TicketStatus.APPROVED
    assert result.action == LifecycleAction.APPROVE


def test_given_raw_card_payload_with_mismatched_ticket_then_fails() -> None:
    """Verify raw payload with mismatched ticket ID is rejected."""
    ticket = _make_pending_annual_leave_ticket(ticket_id="TCK-EXP-001")
    payload = {
        "action": "APPROVE",
        "ticket_id": "TCK-WRONG-999",
        "action_token": "act_mismatch_test",
    }

    with pytest.raises(TicketRuleViolation, match="does not match target ticket"):
        handle_card_action_payload(
            payload,
            ticket=ticket,
            caller_id=ticket.manager_id,
        )


def test_given_unsupported_action_string_then_raises_error() -> None:
    """Verify unrecognized action names are rejected."""
    ticket = _make_pending_annual_leave_ticket()

    with pytest.raises(
        UnsupportedManagerActionError, match="Unsupported manager action"
    ):
        handle_manager_action(
            ticket,
            "REQUEST_INFO",
            caller_id=ticket.manager_id,
            action_token="act_unsupported_01",
        )
