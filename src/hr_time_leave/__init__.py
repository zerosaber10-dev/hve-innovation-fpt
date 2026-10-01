"""Domain foundation for HR time and leave ticket workflows."""

from hr_time_leave.domain import (
    InvalidTransitionError,
    LifecycleEvent,
    ManagerTicketView,
    SensitiveTicketData,
    Ticket,
    TicketRuleViolation,
    TicketSchemaError,
    TicketStatus,
    TicketType,
    submit_ticket,
    transition_ticket,
    validate_ticket,
    validate_ticket_payload,
)

__all__ = [
    "InvalidTransitionError",
    "LifecycleEvent",
    "ManagerTicketView",
    "SensitiveTicketData",
    "Ticket",
    "TicketRuleViolation",
    "TicketSchemaError",
    "TicketStatus",
    "TicketType",
    "submit_ticket",
    "transition_ticket",
    "validate_ticket",
    "validate_ticket_payload",
]
