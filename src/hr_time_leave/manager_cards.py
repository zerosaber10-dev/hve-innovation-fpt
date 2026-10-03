"""Microsoft Teams Adaptive Card generator and protected manager action handler."""

from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any, Final, Protocol

from hr_time_leave.domain import (
    LifecycleAction,
    LifecycleEvent,
    Ticket,
    TicketRuleViolation,
    TicketStatus,
    transition_ticket,
)

TEAMS_ADAPTIVE_CARD_SCHEMA: Final[str] = (
    "http://adaptivecards.io/schemas/adaptive-card.json"
)
ADAPTIVE_CARD_VERSION: Final[str] = "1.5"


class ManagerAuthorizationError(PermissionError):
    """Raised when a caller is not authorized to act on a ticket."""


class TicketNotPendingError(ValueError):
    """Raised when an action is attempted on a ticket that is not pending approval."""


class RejectionReasonRequiredError(TicketRuleViolation):
    """Raised when a rejection action lacks a mandatory reason."""


class DuplicateActionTokenError(ValueError):
    """Raised when an action token is invalid or has been consumed improperly."""


class UnsupportedManagerActionError(ValueError):
    """Raised when an unhandled manager lifecycle action is submitted."""


@dataclass(frozen=True, slots=True)
class EmployeeNotificationEvent:
    """Attributable notification sent to an employee following a manager decision."""

    recipient_id: str
    ticket_id: str
    status: TicketStatus
    decision_by: str
    occurred_at: datetime
    message: str
    rejection_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ManagerActionResult:
    """Result of processing a protected manager action."""

    ticket: Ticket
    action: LifecycleAction
    audit_event: LifecycleEvent
    notification: EmployeeNotificationEvent
    is_idempotent_replay: bool = False


def generate_action_token(
    ticket_id: str,
    manager_id: str,
    prefix: str = "act",
) -> str:
    """Generate a cryptographically secure, random action token."""
    entropy = secrets.token_urlsafe(24)
    return f"{prefix}_{ticket_id}_{entropy}"


class ActionTokenStore(Protocol):
    """Protocol for idempotent action token storage."""

    def is_token_used(self, token: str) -> bool:
        """Return True if the action token has already been recorded."""
        ...

    def get_action_result(self, token: str) -> ManagerActionResult | None:
        """Return previously recorded action result for this token, if any."""
        ...

    def record_action(
        self,
        token: str,
        ticket_id: str,
        manager_id: str,
        action: LifecycleAction,
        result: ManagerActionResult,
    ) -> None:
        """Record an executed action result for a token."""
        ...


class InMemoryActionTokenStore:
    """Thread-safe in-memory store for idempotent action tokens."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: dict[
            str, tuple[str, str, LifecycleAction, ManagerActionResult]
        ] = {}

    def is_token_used(self, token: str) -> bool:
        """Return True if token has already been registered."""
        with self._lock:
            return token in self._store

    def get_action_result(self, token: str) -> ManagerActionResult | None:
        """Return stored result if present."""
        with self._lock:
            record = self._store.get(token)
            return record[3] if record is not None else None

    def record_action(
        self,
        token: str,
        ticket_id: str,
        manager_id: str,
        action: LifecycleAction,
        result: ManagerActionResult,
    ) -> None:
        """Store the action result under the given token."""
        with self._lock:
            self._store[token] = (ticket_id, manager_id, action, result)

    def clear(self) -> None:
        """Reset the token store."""
        with self._lock:
            self._store.clear()


_DEFAULT_ACTION_TOKEN_STORE: Final[InMemoryActionTokenStore] = (
    InMemoryActionTokenStore()
)


def get_default_action_token_store() -> InMemoryActionTokenStore:
    """Return the module-level default action token store."""
    return _DEFAULT_ACTION_TOKEN_STORE


def build_manager_approval_card(
    ticket: Ticket,
    *,
    action_token: str | None = None,
) -> dict[str, Any]:
    """Build a sanitized Microsoft Teams Adaptive Card for manager approval (AC-008).

    Uses `ticket.manager_view()` exclusively, guaranteeing zero disclosure
    of sensitive medical diagnosis/notes, employee reasons, or compensation amounts.
    """
    token = action_token or generate_action_token(ticket.ticket_id, ticket.manager_id)
    view = ticket.manager_view()

    formatted_type = view.ticket_type.value.replace("_", " ").title()
    facts: list[dict[str, str]] = [
        {"title": "Ticket ID", "value": view.ticket_id},
        {"title": "Request Type", "value": formatted_type},
        {"title": "Employee ID", "value": ticket.employee_id},
        {"title": "Current Status", "value": view.status.value},
    ]

    if view.certification_status:
        facts.append(
            {"title": "Medical Certification", "value": view.certification_status}
        )
    if view.start_date:
        facts.append({"title": "Start Date", "value": view.start_date.isoformat()})
    if view.end_date:
        facts.append({"title": "End Date", "value": view.end_date.isoformat()})
    if view.requested_leave_days is not None:
        facts.append(
            {"title": "Requested Days", "value": str(view.requested_leave_days)}
        )
    if view.requested_hours is not None:
        facts.append({"title": "Requested Hours", "value": str(view.requested_hours)})

    body: list[dict[str, Any]] = [
        {
            "type": "Container",
            "items": [
                {
                    "type": "TextBlock",
                    "text": "HR Time & Leave Decision Request",
                    "weight": "Bolder",
                    "size": "Medium",
                    "wrap": True,
                },
                {
                    "type": "TextBlock",
                    "text": (
                        f"Review request for {ticket.employee_id} • {formatted_type}"
                    ),
                    "isSubtle": True,
                    "spacing": "None",
                    "wrap": True,
                },
            ],
        },
        {
            "type": "FactSet",
            "facts": facts,
        },
        {
            "type": "TextBlock",
            "text": (
                "Privacy Notice: Detailed medical diagnoses, doctor notes, "
                "and employee compensation details are withheld per "
                "data protection policy."
            ),
            "isSubtle": True,
            "size": "Small",
            "wrap": True,
        },
    ]

    actions: list[dict[str, Any]] = [
        {
            "type": "Action.Submit",
            "title": "Approve",
            "style": "positive",
            "data": {
                "action": LifecycleAction.APPROVE.value,
                "ticket_id": view.ticket_id,
                "action_token": token,
            },
        },
        {
            "type": "Action.ShowCard",
            "title": "Reject",
            "style": "destructive",
            "card": {
                "type": "AdaptiveCard",
                "$schema": TEAMS_ADAPTIVE_CARD_SCHEMA,
                "version": ADAPTIVE_CARD_VERSION,
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "Specify rejection reason (mandatory):",
                        "weight": "Bolder",
                        "wrap": True,
                    },
                    {
                        "type": "Input.Text",
                        "id": "rejection_reason",
                        "placeholder": "Enter explicit reason for rejection...",
                        "isMultiline": True,
                        "isRequired": True,
                    },
                ],
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": "Confirm Rejection",
                        "style": "destructive",
                        "data": {
                            "action": LifecycleAction.REJECT.value,
                            "ticket_id": view.ticket_id,
                            "action_token": token,
                        },
                    }
                ],
            },
        },
    ]

    return {
        "$schema": TEAMS_ADAPTIVE_CARD_SCHEMA,
        "type": "AdaptiveCard",
        "version": ADAPTIVE_CARD_VERSION,
        "msteams": {"width": "Full"},
        "body": body,
        "actions": actions,
    }


def handle_manager_action(
    ticket: Ticket,
    action: LifecycleAction | str,
    *,
    caller_id: str,
    action_token: str,
    channel: str = "msteams",
    occurred_at: datetime | None = None,
    rejection_reason: str | None = None,
    token_store: ActionTokenStore | None = None,
) -> ManagerActionResult:
    """Process a server-side manager approval or rejection action.

    Enforces:
    1. Direct-report authorization (caller_id == ticket.manager_id).
    2. Idempotency token check (safe retry on replay).
    3. Ticket state check (must be PENDING_APPROVAL).
    4. Mandatory rejection reason for REJECT.
    5. Lifecycle transition with audit event and employee notification.
    """
    # 1. Authorization check
    if caller_id != ticket.manager_id:
        raise ManagerAuthorizationError(
            f"Caller {caller_id!r} is not authorized to act on ticket "
            f"{ticket.ticket_id!r}; assigned manager is {ticket.manager_id!r}."
        )

    # 2. Token store resolution & Idempotency check
    active_store = (
        token_store if token_store is not None else get_default_action_token_store()
    )

    if not action_token or not action_token.strip():
        raise DuplicateActionTokenError("A non-empty action token is required.")

    normalized_token = action_token.strip()

    if active_store.is_token_used(normalized_token):
        cached_result = active_store.get_action_result(normalized_token)
        if (
            cached_result is not None
            and cached_result.ticket.ticket_id == ticket.ticket_id
        ):
            return replace(cached_result, is_idempotent_replay=True)
        raise DuplicateActionTokenError(
            f"Action token {normalized_token!r} has already been consumed "
            "for another operation."
        )

    # 3. Status check
    if ticket.status is not TicketStatus.PENDING_APPROVAL:
        raise TicketNotPendingError(
            f"Ticket {ticket.ticket_id!r} has status {ticket.status.value!r}; "
            "manager action requires status PENDING_APPROVAL."
        )

    # 4. Resolve action
    try:
        resolved_action = (
            action
            if isinstance(action, LifecycleAction)
            else LifecycleAction(str(action))
        )
    except ValueError as error:
        raise UnsupportedManagerActionError(
            f"Unsupported manager action {action!r}; must be APPROVE or REJECT."
        ) from error

    event_time = occurred_at or datetime.now(UTC)
    if event_time.tzinfo is None or event_time.utcoffset() is None:
        raise TicketRuleViolation(
            "Transition timestamps must include a timezone and are stored in UTC."
        )
    event_time_utc = event_time.astimezone(UTC)

    # 5. Execute action
    if resolved_action is LifecycleAction.APPROVE:
        updated_ticket = transition_ticket(
            ticket,
            TicketStatus.APPROVED,
            actor_id=caller_id,
            channel=channel,
            occurred_at=event_time_utc,
            action=LifecycleAction.APPROVE,
        )
        audit_event = updated_ticket.audit_events[-1]
        notification = EmployeeNotificationEvent(
            recipient_id=ticket.employee_id,
            ticket_id=ticket.ticket_id,
            status=TicketStatus.APPROVED,
            decision_by=caller_id,
            occurred_at=event_time_utc,
            message=(
                f"Your {ticket.ticket_type.value.replace('_', ' ').title()} "
                f"request ({ticket.ticket_id}) has been approved by your manager."
            ),
            rejection_reason=None,
        )
    elif resolved_action is LifecycleAction.REJECT:
        cleaned_reason = rejection_reason.strip() if rejection_reason else ""
        if not cleaned_reason:
            raise RejectionReasonRequiredError(
                "A non-empty rejection reason is required before rejecting a ticket."
            )
        updated_ticket = transition_ticket(
            ticket,
            TicketStatus.REJECTED,
            actor_id=caller_id,
            channel=channel,
            occurred_at=event_time_utc,
            action=LifecycleAction.REJECT,
            rejection_reason=cleaned_reason,
        )
        audit_event = updated_ticket.audit_events[-1]
        notification = EmployeeNotificationEvent(
            recipient_id=ticket.employee_id,
            ticket_id=ticket.ticket_id,
            status=TicketStatus.REJECTED,
            decision_by=caller_id,
            occurred_at=event_time_utc,
            message=(
                f"Your {ticket.ticket_type.value.replace('_', ' ').title()} "
                f"request ({ticket.ticket_id}) was rejected by your manager. "
                f"Reason: {cleaned_reason}"
            ),
            rejection_reason=cleaned_reason,
        )
    else:
        raise UnsupportedManagerActionError(
            f"Manager action {resolved_action.value!r} cannot be "
            "executed via manager card."
        )

    result = ManagerActionResult(
        ticket=updated_ticket,
        action=resolved_action,
        audit_event=audit_event,
        notification=notification,
        is_idempotent_replay=False,
    )

    active_store.record_action(
        token=normalized_token,
        ticket_id=ticket.ticket_id,
        manager_id=caller_id,
        action=resolved_action,
        result=result,
    )
    return result


def handle_card_action_payload(
    payload: dict[str, Any],
    *,
    ticket: Ticket,
    caller_id: str,
    channel: str = "msteams",
    occurred_at: datetime | None = None,
    token_store: ActionTokenStore | None = None,
) -> ManagerActionResult:
    """Parse and execute a raw card action payload from Microsoft Teams."""
    payload_ticket_id = payload.get("ticket_id")
    if payload_ticket_id and payload_ticket_id != ticket.ticket_id:
        raise TicketRuleViolation(
            f"Payload ticket ID {payload_ticket_id!r} does not match "
            f"target ticket {ticket.ticket_id!r}."
        )

    action_token = payload.get("action_token")
    if not action_token or not str(action_token).strip():
        raise DuplicateActionTokenError(
            "Missing action token in card submission payload."
        )

    raw_action = payload.get("action")
    if not raw_action:
        raise UnsupportedManagerActionError(
            "Missing action in card submission payload."
        )

    rejection_reason = payload.get("rejection_reason")
    if rejection_reason is not None and not isinstance(rejection_reason, str):
        rejection_reason = str(rejection_reason)

    return handle_manager_action(
        ticket,
        raw_action,
        caller_id=caller_id,
        action_token=str(action_token),
        channel=channel,
        occurred_at=occurred_at,
        rejection_reason=rejection_reason,
        token_store=token_store,
    )
