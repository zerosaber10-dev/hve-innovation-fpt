"""FastAPI web application entrypoint for HR Time and Leave Copilot.

Provides production-grade endpoints for Bot Framework messaging ingestion,
liveness and readiness probes, and CORS/exception middleware.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("hr_time_leave.app")

app = FastAPI(
    title="Enterprise HR Time and Leave Copilot",
    version="0.1.0",
    description="Containerized runtime for HR Time and Leave Agent",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standard ASGI application alias
application = app


def check_readiness() -> dict[str, str]:
    """Execute subsystem readiness checks.

    Returns:
        dict[str, str]: Component name mapped to readiness state ('ok' or error).
    """
    checks: dict[str, str] = {}

    # 1. Domain schema validator readiness
    try:
        from hr_time_leave.domain import _TICKET_VALIDATOR

        checks["domain"] = "ok" if _TICKET_VALIDATOR is not None else "error"
    except Exception as exc:  # pragma: no cover
        checks["domain"] = f"error: {exc}"

    # 2. Policy engine readiness
    try:
        from hr_time_leave.policy import create_default_policy_engine

        engine = create_default_policy_engine()
        checks["policy"] = "ok" if engine is not None else "error"
    except Exception as exc:  # pragma: no cover
        checks["policy"] = f"error: {exc}"

    # 3. SLA engine readiness
    try:
        from hr_time_leave.sla import create_default_sla_engine

        sla = create_default_sla_engine()
        checks["sla"] = "ok" if sla is not None else "error"
    except Exception as exc:  # pragma: no cover
        checks["sla"] = f"error: {exc}"

    return checks


def process_bot_activity(activity: dict[str, Any]) -> dict[str, Any]:
    """Process incoming Microsoft Bot Framework or Teams activity payload.

    Validates required activity attributes ('type') and dispatches either to
    card action handler or conversational message processor.

    Args:
        activity: Ingested activity payload dictionary.

    Returns:
        dict[str, Any]: Processing result or outgoing response activity.

    Raises:
        ValueError: If activity schema is invalid or required fields are missing.
    """
    if not isinstance(activity, dict):
        raise ValueError("Activity payload must be a dictionary")

    activity_type = activity.get("type")
    if not activity_type or not isinstance(activity_type, str):
        raise ValueError("Missing or invalid required activity field: 'type'")

    # Teams card action / invoke handling
    if activity_type in ("invoke", "adaptiveCard/action"):
        card_value = activity.get("value")
        if isinstance(card_value, dict) and "action" in card_value:
            return {
                "status": "accepted",
                "activityId": activity.get("id", ""),
                "action": card_value.get("action"),
                "ticket_id": card_value.get("ticket_id"),
            }
        return {
            "status": "accepted",
            "activityId": activity.get("id", ""),
            "type": activity_type,
        }

    # Standard conversation message handling
    if activity_type == "message":
        text = activity.get("text", "")
        sender_info = activity.get("from")
        sender = (
            sender_info.get("name", "User")
            if isinstance(sender_info, dict)
            else "User"
        )
        return {
            "type": "message",
            "status": "processed",
            "recipient": sender_info,
            "text": f"Received message from {sender}: {text}",
            "conversation": activity.get("conversation"),
        }

    # Other event types (conversationUpdate, installationUpdate, etc.)
    return {
        "status": "acknowledged",
        "type": activity_type,
        "activityId": activity.get("id", ""),
    }


@app.get("/healthz")
async def health_check() -> dict[str, str]:
    """Return liveness probe status adhering to platform contract."""
    return {
        "status": "healthy",
        "service": "hr-time-leave-agent",
        "version": "0.1.0",
    }


@app.get("/readyz")
async def readiness_probe() -> dict[str, Any]:
    """Return readiness probe status verifying downstream dependencies."""
    checks = check_readiness()
    all_healthy = all(status_val == "ok" for status_val in checks.values())

    if not all_healthy:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "degraded", "checks": checks},
        )

    return {
        "status": "ready",
        "service": "hr-time-leave-agent",
        "version": "0.1.0",
        "checks": checks,
    }


@app.post("/api/messages")
async def bot_messages_endpoint(request: Request) -> dict[str, Any]:
    """Handle Microsoft Bot Framework and Teams webhook activities."""
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload: {exc}",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload must be a JSON object",
        )

    try:
        return process_bot_activity(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected error processing bot activity")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing activity",
        ) from exc
