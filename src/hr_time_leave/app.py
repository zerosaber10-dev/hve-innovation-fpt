"""FastAPI web application entrypoint for HR Time and Leave Copilot.

Provides production-grade endpoints for Bot Framework messaging ingestion,
liveness and readiness probes, and CORS/exception middleware.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx
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


_BOT_TOKEN_CACHE: dict[str, Any] = {"token": None, "expires_at": 0.0}


def get_bot_framework_token() -> str | None:
    """Acquire OAuth2 Bearer token for Microsoft Bot Framework Connector API.

    Caches valid tokens until expiry. Uses client credentials if BOT_APP_PASSWORD
    is configured, falling back to Azure Managed Identity / DefaultAzureCredential.

    Returns:
        str | None: Raw JWT access token if authentication succeeded, None otherwise.
    """
    global _BOT_TOKEN_CACHE
    now = time.time()
    cached_token = _BOT_TOKEN_CACHE.get("token")
    expires_at = float(_BOT_TOKEN_CACHE.get("expires_at", 0.0))
    if cached_token and now < expires_at - 60.0:
        return str(cached_token)

    bot_app_id = os.getenv("BOT_APP_ID") or os.getenv("MICROSOFT_APP_ID")
    bot_app_password = (
        os.getenv("BOT_APP_PASSWORD")
        or os.getenv("MICROSOFT_APP_PASSWORD")
        or os.getenv("AZURE_CLIENT_SECRET")
    )
    tenant_id = (
        os.getenv("AZURE_TENANT_ID")
        or os.getenv("MICROSOFT_APP_TENANT_ID")
        or "botframework.com"
    )

    if bot_app_id and bot_app_password:
        token_url = (
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        )
        token_payload = {
            "grant_type": "client_credentials",
            "client_id": bot_app_id,
            "client_secret": bot_app_password,
            "scope": "https://api.botframework.com/.default",
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(token_url, data=token_payload)
                if resp.status_code == 200:
                    data = resp.json()
                    token = data.get("access_token")
                    expires_in = float(data.get("expires_in", 3600))
                    _BOT_TOKEN_CACHE["token"] = token
                    _BOT_TOKEN_CACHE["expires_at"] = now + expires_in
                    logger.info(
                        "Successfully acquired Bot Framework token for appId=%s",
                        bot_app_id,
                    )
                    return token
                logger.warning(
                    "Failed to acquire Bot Framework token: HTTP %s - %s",
                    resp.status_code,
                    resp.text,
                )
        except Exception as exc:
            logger.warning("Error requesting Bot Framework token: %s", exc)

    # Fallback to Azure Managed Identity / DefaultAzureCredential
    try:
        from azure.identity import DefaultAzureCredential

        cred = DefaultAzureCredential()
        token_obj = cred.get_token("https://api.botframework.com/.default")
        if token_obj and token_obj.token:
            _BOT_TOKEN_CACHE["token"] = token_obj.token
            _BOT_TOKEN_CACHE["expires_at"] = float(token_obj.expires_on)
            logger.info("Acquired Bot Framework token via Managed Identity")
            return token_obj.token
    except Exception as exc:
        logger.debug(
            "Managed Identity token retrieval for Bot Framework skipped/failed: %s",
            exc,
        )

    return None


def send_bot_framework_activity(
    service_url: str,
    conversation_id: str,
    activity_payload: dict[str, Any],
    reply_to_id: str | None = None,
) -> bool:
    """Dispatch activity payload to Microsoft Bot Framework Connector service.

    Args:
        service_url: Target Bot Connector service URL (e.g. from incoming activity).
        conversation_id: Target conversation identifier.
        activity_payload: Complete Activity schema dictionary.
        reply_to_id: Optional ID of the parent activity being replied to.

    Returns:
        bool: True if Connector accepted activity (HTTP 200/201/202), False otherwise.
    """
    clean_service_url = service_url.rstrip("/")
    if clean_service_url.endswith("/v3"):
        base_endpoint = clean_service_url
    else:
        base_endpoint = f"{clean_service_url}/v3"

    if reply_to_id:
        endpoint = (
            f"{base_endpoint}/conversations/{conversation_id}/activities/{reply_to_id}"
        )
    else:
        endpoint = (
            f"{base_endpoint}/conversations/{conversation_id}/activities"
        )

    headers: dict[str, str] = {"Content-Type": "application/json"}
    token = get_bot_framework_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(endpoint, json=activity_payload, headers=headers)
            if resp.status_code in (200, 201, 202):
                logger.info(
                    "Successfully delivered Bot Framework activity to %s (HTTP %s)",
                    endpoint,
                    resp.status_code,
                )
                return True
            logger.warning(
                "Bot Framework Connector rejected activity at %s: HTTP %s - %s",
                endpoint,
                resp.status_code,
                resp.text,
            )
            return False
    except Exception as exc:
        logger.warning(
            "Exception delivering Bot Framework activity to %s: %s",
            endpoint,
            exc,
        )
        return False


def process_bot_activity(activity: dict[str, Any]) -> dict[str, Any]:
    """Process incoming Microsoft Bot Framework or Teams activity payload.

    Validates required activity attributes ('type') and dispatches either to
    card action handler or conversational message processor. Also proactively
    delivers response activities back to Microsoft Bot Connector serviceUrl.

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

    service_url = activity.get("serviceUrl")
    conversation = activity.get("conversation")
    conv_id = (
        conversation.get("id")
        if isinstance(conversation, dict) and "id" in conversation
        else None
    )
    activity_id = activity.get("id")
    bot_app_id = os.getenv("BOT_APP_ID") or os.getenv("MICROSOFT_APP_ID") or ""
    bot_recipient = activity.get("recipient")
    bot_id = (
        bot_recipient.get("id")
        if isinstance(bot_recipient, dict) and bot_recipient.get("id")
        else (bot_app_id or "hr-time-leave-copilot")
    )
    bot_name = (
        bot_recipient.get("name")
        if isinstance(bot_recipient, dict) and bot_recipient.get("name")
        else "Enterprise HR Time and Leave Copilot"
    )

    # Teams card action / invoke handling
    if activity_type in ("invoke", "adaptiveCard/action"):
        card_value = activity.get("value")
        if isinstance(card_value, dict) and "action" in card_value:
            return {
                "status": "accepted",
                "activityId": activity_id or "",
                "action": card_value.get("action"),
                "ticket_id": card_value.get("ticket_id"),
            }
        return {
            "status": "accepted",
            "activityId": activity_id or "",
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

        # Proactively dispatch response back to Bot Framework Connector
        # if serviceUrl is present in inbound activity
        if service_url and conv_id:
            outbound_activity = {
                "type": "message",
                "from": {
                    "id": bot_id,
                    "name": bot_name,
                },
                "recipient": (
                    sender_info
                    if isinstance(sender_info, dict)
                    else {"id": "User", "name": "User"}
                ),
                "conversation": conversation,
                "replyToId": activity_id,
                "text": response_text,
            }
            send_bot_framework_activity(
                service_url=service_url,
                conversation_id=conv_id,
                activity_payload=outbound_activity,
                reply_to_id=activity_id,
            )

        return {
            "type": "message",
            "status": "processed",
            "recipient": sender_info,
            "text": response_text,
            "conversation": conversation,
        }

    # Welcome message on conversationUpdate when users join
    if activity_type == "conversationUpdate":
        members_added = activity.get("membersAdded")
        if (
            service_url
            and conv_id
            and isinstance(members_added, list)
            and members_added
        ):
            human_members = [
                m
                for m in members_added
                if isinstance(m, dict)
                and m.get("id") != bot_id
                and m.get("id") != bot_app_id
            ]
            if human_members:
                welcome_text = (
                    "Hello! I am your Enterprise HR Time and Leave Copilot. "
                    "I can assist with annual leave, sick leave, overtime, "
                    "and attendance adjustments. How can I help you today?"
                )
                welcome_activity = {
                    "type": "message",
                    "from": {
                        "id": bot_id,
                        "name": bot_name,
                    },
                    "recipient": human_members[0],
                    "conversation": conversation,
                    "text": welcome_text,
                }
                send_bot_framework_activity(
                    service_url=service_url,
                    conversation_id=conv_id,
                    activity_payload=welcome_activity,
                )

    # Other event types (conversationUpdate, installationUpdate, etc.)
    return {
        "status": "acknowledged",
        "type": activity_type,
        "activityId": activity_id or "",
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

    logger.info(
        "Received Bot Framework activity type=%s id=%s channel=%s",
        payload.get("type"),
        payload.get("id"),
        payload.get("channelId"),
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
