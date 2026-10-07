"""Azure Functions background worker for SLA reminders and HR escalations.

Processes asynchronous Service Bus messages triggered by scheduled timer
or queue events, evaluating SLA policies and executing ticket transitions.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

import azure.functions as func

from hr_time_leave.sla import (
    SLAEngine,
    SLAJob,
    SLAJobStatus,
    SLAJobType,
    create_default_sla_engine,
)

logger = logging.getLogger("hr_time_leave.functions")

# Azure Functions Python v2 Programming Model Application instance
app = func.FunctionApp()


@app.service_bus_queue_trigger(
    arg_name="msg",
    queue_name="hr-sla-jobs",
    connection="SERVICE_BUS_CONNECTION",
)
def hr_sla_service_bus_handler(msg: func.ServiceBusMessage) -> None:
    """Handle incoming SLA reminder and escalation messages from Service Bus."""
    body = msg.get_body()
    logger.info("Received Service Bus SLA message: %d bytes", len(body))
    result = process_service_bus_message(body)
    logger.info(
        "Processed SLA message: job_id=%s, ticket_id=%s, action_taken=%s, status=%s",
        result.get("job_id"),
        result.get("ticket_id"),
        result.get("action_taken"),
        result.get("job_status"),
    )


def parse_message_payload(message: dict[str, Any] | str | bytes) -> dict[str, Any]:
    """Parse incoming Service Bus message into structured dictionary.

    Args:
        message: Raw message payload as dictionary, JSON string, or UTF-8 bytes.

    Returns:
        dict[str, Any]: Parsed JSON message content.

    Raises:
        ValueError: If message cannot be parsed into a dictionary.
    """
    if isinstance(message, dict):
        return message

    if isinstance(message, bytes):
        try:
            message = message.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Unable to decode message bytes as UTF-8: {exc}") from exc

    if isinstance(message, str):
        try:
            parsed = json.loads(message)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed JSON message must be a dictionary object")
            return parsed
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON message format: {exc}") from exc

    raise ValueError(f"Unsupported message type: {type(message).__name__}")


def process_service_bus_message(
    message: dict[str, Any] | str | bytes,
    *,
    engine: SLAEngine | None = None,
    evaluation_time: datetime | None = None,
) -> dict[str, Any]:
    """Process an SLA reminder or escalation message from Azure Service Bus.

    Evaluates the SLA job, verifies ticket existence and state, and executes
    the appropriate reminder or escalation transition.

    Args:
        message: Service Bus message body (dict, JSON string, or bytes).
        engine: Optional custom SLAEngine instance. Defaults to in-memory engine.
        evaluation_time: Optional evaluation timestamp (defaults to UTC now).

    Returns:
        dict[str, Any]: Structured processing outcome including status and
            actions taken.

    Raises:
        ValueError: If message schema is invalid or required fields are missing.
    """
    payload = parse_message_payload(message)

    ticket_id = payload.get("ticket_id")
    if not ticket_id or not isinstance(ticket_id, str):
        raise ValueError("Missing or invalid required message field: 'ticket_id'")

    raw_job_type = payload.get("job_type", "").upper()
    if raw_job_type not in (SLAJobType.REMINDER.value, SLAJobType.ESCALATION.value):
        raise ValueError(
            f"Invalid or missing 'job_type': {raw_job_type!r}. "
            f"Expected one of {[t.value for t in SLAJobType]}"
        )

    job_type = SLAJobType(raw_job_type)
    current_time = evaluation_time or datetime.now(UTC)
    active_engine = engine or create_default_sla_engine()

    # Construct SLAJob instance from message metadata
    job_id = payload.get("job_id", f"job-{ticket_id}-{job_type.value.lower()}")
    sla_job = SLAJob(
        job_id=job_id,
        ticket_id=ticket_id,
        job_type=job_type,
        scheduled_at=current_time,
        created_at=current_time,
        status=SLAJobStatus.SCHEDULED,
    )

    result = active_engine.process_job(sla_job, current_time)

    return {
        "status": "processed" if result.action_taken else "skipped",
        "job_id": result.job_id,
        "ticket_id": result.ticket_id,
        "job_type": result.job_type.value,
        "action_taken": result.action_taken,
        "job_status": result.status.value,
        "ticket_status_before": result.ticket_status_before.value,
        "ticket_status_after": result.ticket_status_after.value,
        "message": result.message,
        "processed_at": current_time.isoformat(),
    }
