"""FastAPI web application entrypoint for HR Time and Leave Copilot.

Provides production-grade endpoints for Bot Framework messaging ingestion,
liveness and readiness probes, and CORS/exception middleware.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("hr_time_leave.app")

ALLOWED_ORIGIN_REGEX = (
    r"^https://([a-zA-Z0-9-]+\.)*(teams\.microsoft\.com|office\.com|skype\.com)$"
)
ALLOWED_ORIGINS = [
    "https://teams.microsoft.com",
    "https://gov.teams.microsoft.us",
    "https://dod.teams.microsoft.us",
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
]

app = FastAPI(
    title="Enterprise HR Time and Leave Copilot",
    version="0.1.0",
    description="Containerized runtime for HR Time and Leave Agent",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Standard ASGI application alias
application = app

_POLICY_ENGINE: Any = None


def get_policy_engine() -> Any:
    """Retrieve or lazily initialize the default grounded policy engine."""
    global _POLICY_ENGINE
    if _POLICY_ENGINE is None:
        from hr_time_leave.policy import create_default_policy_engine

        _POLICY_ENGINE = create_default_policy_engine()
    return _POLICY_ENGINE


def _call_azure_openai(prompt: str, context: str, sender: str) -> str | None:
    """Attempt invocation of Azure OpenAI (GPT-6 Luna) deployment."""
    endpoint = (
        os.environ.get("OPENAI_ENDPOINT") or os.environ.get("AZURE_OPENAI_ENDPOINT")
    )
    if not endpoint:
        return None

    deployment_name = os.environ.get("OPENAI_DEPLOYMENT_NAME", "gpt-6-luna")
    api_key = os.environ.get("OPENAI_API_KEY")

    system_prompt = (
        "You are the Enterprise HR Time and Leave Copilot for NovaTech. "
        "Provide clear, helpful, professional, and compliant guidance based "
        "strictly on the provided company HR policy context. "
        f"\n\n[POLICY CONTEXT]\n{context}"
    )

    try:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        from openai import AzureOpenAI, OpenAI

        if api_key:
            client = OpenAI(base_url=endpoint, api_key=api_key)
        else:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
            )
            is_cog_svc = (
                "cognitiveservices.azure.com" in endpoint
                and "/openai/v1" not in endpoint
            )
            if is_cog_svc:
                client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_version="2024-10-01-preview",
                    azure_ad_token_provider=token_provider,
                )
            else:
                client = OpenAI(
                    base_url=endpoint,
                    api_key=token_provider,
                )

        completion = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Employee {sender} asks: {prompt}"},
            ],
            max_tokens=800,
            temperature=0.2,
        )
        content = completion.choices[0].message.content
        if content:
            return content.strip()
    except Exception as exc:
        logger.warning(
            "Azure OpenAI gpt-6-luna call failed, falling back to policy engine: %s",
            exc,
        )
    return None


def generate_agent_response(query: str, sender: str = "User") -> str:
    """Generate agent response via Azure OpenAI (GPT-6 Luna) with RAG grounding,
    falling back to local deterministic PolicyEngine when offline or unconfigured.
    """
    clean_query = (query or "").strip()
    if not clean_query:
        return f"Hello {sender}, how may I assist you with HR leave today?"

    # Check for simple greetings
    if clean_query.lower() in ("hi", "hello", "hey", "help", "who are you"):
        return (
            f"Hello {sender}! I am your Enterprise HR Time and Leave Copilot. "
            "I can assist with annual leave, sick leave, overtime, "
            "and attendance adjustments. How can I help you today?"
        )

    # 1. Retrieve policy grounding via PolicyEngine
    engine = get_policy_engine()
    policy_ans = engine.answer_query(clean_query)

    # 2. If Azure OpenAI endpoint is configured, invoke GPT-6 Luna with grounded context
    llm_answer = _call_azure_openai(
        prompt=clean_query,
        context=policy_ans.answer,
        sender=sender,
    )
    if llm_answer:
        if sender and sender != "User" and sender not in llm_answer:
            return f"Hello {sender}. {llm_answer}"
        return llm_answer

    # 3. Deterministic local policy engine response
    return f"Hello {sender}. {policy_ans.answer}"


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
        response_text = generate_agent_response(text, sender=sender)
        return {
            "type": "message",
            "status": "processed",
            "recipient": sender_info,
            "text": response_text,
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
