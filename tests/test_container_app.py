"""Unit and integration tests for containerized web runtime and background Functions.

Validates:
1. FastAPI /healthz and /readyz probes.
2. Bot Framework /api/messages activity ingestion and error handling.
3. Service Bus SLA reminder and escalation trigger in function_app.py.
4. Dockerfile and .dockerignore security and operational compliance.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import azure.functions as func
import pytest
from starlette.testclient import TestClient

from hr_time_leave import (
    SensitiveTicketData,
    Ticket,
    TicketType,
    app,
    generate_agent_response,
    get_bot_framework_token,
    hr_sla_service_bus_handler,
    process_bot_activity,
    process_service_bus_message,
    send_bot_framework_activity,
    submit_ticket,
)
from hr_time_leave.sla import create_default_sla_engine

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCKERFILE_PATH = REPO_ROOT / "Dockerfile"
DOCKERIGNORE_PATH = REPO_ROOT / ".dockerignore"


@pytest.fixture
def client() -> TestClient:
    """Fixture providing Starlette TestClient for FastAPI app."""
    return TestClient(app)


class TestHealthAndReadinessProbes:
    """Validate liveness and readiness probe contracts."""

    def test_given_healthz_endpoint_when_called_then_returns_200_and_expected_fields(
        self, client: TestClient
    ) -> None:
        response = client.get("/healthz")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "healthy"
        assert payload["service"] == "hr-time-leave-agent"
        assert payload["version"] == "0.1.0"

    def test_given_readyz_endpoint_when_called_then_returns_200_and_dependency_checks(
        self, client: TestClient
    ) -> None:
        response = client.get("/readyz")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ready"
        assert payload["service"] == "hr-time-leave-agent"
        assert "checks" in payload
        assert payload["checks"].get("domain") == "ok"
        assert payload["checks"].get("policy") == "ok"
        assert payload["checks"].get("sla") == "ok"


class TestBotMessagesEndpoint:
    """Validate Microsoft Bot Framework webhook activity routing and error handling."""

    def test_given_valid_message_activity_when_posted_then_returns_200(
        self, client: TestClient
    ) -> None:
        activity = {
            "type": "message",
            "id": "act-123",
            "text": "Check annual leave balance",
            "from": {"id": "emp-101", "name": "Alice Employee"},
            "conversation": {"id": "conv-456"},
        }
        response = client.post("/api/messages", json=activity)
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "message"
        assert data["status"] == "processed"
        assert "Alice Employee" in data["text"]

    def test_given_valid_card_action_invoke_when_posted_then_returns_200(
        self, client: TestClient
    ) -> None:
        activity = {
            "type": "invoke",
            "id": "act-124",
            "value": {
                "action": "APPROVE",
                "ticket_id": "TICK-2026-001",
            },
        }
        response = client.post("/api/messages", json=activity)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["action"] == "APPROVE"
        assert data["ticket_id"] == "TICK-2026-001"

    def test_given_invalid_json_payload_when_posted_then_returns_400(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/messages",
            content="invalid-json-data",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
        assert "Invalid JSON payload" in response.json().get("detail", "")

    def test_given_missing_type_field_when_posted_then_returns_400(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/messages",
            json={"text": "Missing activity type"},
        )
        assert response.status_code == 400
        error_detail = response.json().get("detail", "")
        assert "Missing or invalid required activity field: 'type'" in error_detail

    def test_given_empty_payload_when_posted_then_returns_400(
        self, client: TestClient
    ) -> None:
        response = client.post("/api/messages", json={})
        assert response.status_code == 400

    def test_given_non_dict_payload_when_bot_activity_processed_then_raises_error(
        self,
    ) -> None:
        with pytest.raises(ValueError, match="dictionary"):
            process_bot_activity("not-a-dict")  # type: ignore[arg-type]


class TestFunctionsServiceBusSLAHandler:
    """Validate background Azure Functions SLA queue processing."""

    def test_given_valid_reminder_message_when_processed_then_executes_job(
        self,
    ) -> None:
        now = datetime(2026, 10, 12, 10, 0, tzinfo=UTC)
        draft = Ticket(
            ticket_id="TICK-SLA-001",
            employee_id="EMP-101",
            manager_id="MGR-201",
            ticket_type=TicketType.ANNUAL_LEAVE,
            created_at=now,
            start_date=date(2026, 10, 20),
            end_date=date(2026, 10, 22),
            requested_leave_days=Decimal("3"),
            accrued_leave_days=Decimal("15"),
            sensitive_data=SensitiveTicketData(),
        )
        ticket = submit_ticket(
            draft,
            actor_id="EMP-101",
            channel="web",
            occurred_at=now,
        )
        engine = create_default_sla_engine(tickets={ticket.ticket_id: ticket})

        message = {
            "ticket_id": ticket.ticket_id,
            "job_type": "REMINDER",
            "job_id": "job-rem-001",
        }
        result = process_service_bus_message(
            message,
            engine=engine,
            evaluation_time=now,
        )

        assert result["ticket_id"] == ticket.ticket_id
        assert result["job_type"] == "REMINDER"
        assert result["action_taken"] is True
        assert result["job_status"] == "EXECUTED"

    def test_given_valid_escalation_message_when_processed_then_escalates_ticket(
        self,
    ) -> None:
        now = datetime(2026, 10, 12, 10, 0, tzinfo=UTC)
        draft = Ticket(
            ticket_id="TICK-SLA-002",
            employee_id="EMP-102",
            manager_id="MGR-202",
            ticket_type=TicketType.ANNUAL_LEAVE,
            created_at=now,
            start_date=date(2026, 10, 25),
            end_date=date(2026, 10, 27),
            requested_leave_days=Decimal("3"),
            accrued_leave_days=Decimal("15"),
            sensitive_data=SensitiveTicketData(),
        )
        ticket = submit_ticket(
            draft,
            actor_id="EMP-102",
            channel="web",
            occurred_at=now,
        )
        engine = create_default_sla_engine(tickets={ticket.ticket_id: ticket})

        message_bytes = json.dumps(
            {
                "ticket_id": ticket.ticket_id,
                "job_type": "ESCALATION",
            }
        ).encode("utf-8")

        result = process_service_bus_message(
            message_bytes,
            engine=engine,
            evaluation_time=now,
        )

        assert result["ticket_id"] == ticket.ticket_id
        assert result["job_type"] == "ESCALATION"
        assert result["action_taken"] is True
        assert result["ticket_status_after"] == "ESCALATED"

    def test_given_missing_ticket_id_when_processed_then_raises_value_error(
        self,
    ) -> None:
        with pytest.raises(ValueError, match="ticket_id"):
            process_service_bus_message({"job_type": "REMINDER"})

    def test_given_invalid_job_type_when_processed_then_raises_value_error(
        self,
    ) -> None:
        with pytest.raises(ValueError, match="job_type"):
            process_service_bus_message(
                {"ticket_id": "TICK-001", "job_type": "INVALID_TYPE"}
            )

    def test_given_invalid_json_string_when_processed_then_raises_value_error(
        self,
    ) -> None:
        with pytest.raises(ValueError, match="Invalid JSON"):
            process_service_bus_message("not-json-content")

    def test_given_service_bus_trigger_when_invoked_then_executes_handler(
        self,
    ) -> None:
        raw_payload = json.dumps(
            {
                "ticket_id": "TICK-SLA-TRIGGER",
                "job_type": "REMINDER",
            }
        ).encode("utf-8")
        msg = func.ServiceBusMessage(body=raw_payload)
        # Should not raise exception
        hr_sla_service_bus_handler(msg)


class TestAgentResponseAndRAG:
    """Validate conversational agent response generation and RAG policy grounding."""

    def test_policy_question_returns_grounded_answer(
        self,
    ) -> None:
        response = generate_agent_response(
            "What is the advance notice requirement for 1-2 days annual leave?",
            sender="Bob Employee",
        )
        assert "Bob Employee" in response
        assert "48 hours" in response
        assert "SOP-HR-042" in response

    def test_casual_greeting_returns_welcoming_message(
        self,
    ) -> None:
        response = generate_agent_response("hello", sender="Carol")
        assert "Carol" in response
        assert "HR Time and Leave Copilot" in response

    def test_given_empty_query_when_generating_response_then_prompts_for_inquiry(
        self,
    ) -> None:
        response = generate_agent_response("", sender="David")
        assert "David" in response
        assert "assist" in response

    def test_given_azure_openai_mock_when_invoked_then_calls_completion(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class MockChoice:
            class MockMessage:
                content = "Based on SOP-HR-042, please submit 48 hours in advance."
            message = MockMessage()

        class MockCompletion:
            choices = [MockChoice()]

        class MockChatCompletions:
            def create(self, **kwargs: Any) -> MockCompletion:
                assert kwargs.get("model") == "gpt-6-luna"
                return MockCompletion()

        class MockChat:
            completions = MockChatCompletions()

        class MockOpenAI:
            def __init__(self, **kwargs: Any) -> None:
                pass
            chat = MockChat()

        endpoint_url = "https://test-foundry.services.ai.azure.com/openai/v1"
        monkeypatch.setenv("OPENAI_ENDPOINT", endpoint_url)
        monkeypatch.setenv("OPENAI_DEPLOYMENT_NAME", "gpt-6-luna")
        monkeypatch.setenv("OPENAI_API_KEY", "fake-test-key")
        monkeypatch.setattr("openai.OpenAI", MockOpenAI)

        result = generate_agent_response(
            "How much notice for 1 day leave?", sender="Eve"
        )
        assert "Eve" in result
        assert "48 hours in advance" in result


class TestCORSConfiguration:
    """Validate CORS headers and Microsoft Teams origin allowance."""

    def test_given_teams_origin_when_options_preflight_then_allowed(
        self, client: TestClient
    ) -> None:
        response = client.options(
            "/api/messages",
            headers={
                "Origin": "https://teams.microsoft.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.status_code == 200
        assert (
            response.headers.get("access-control-allow-origin")
            == "https://teams.microsoft.com"
        )
        assert response.headers.get("access-control-allow-credentials") == "true"


class TestBotFrameworkConnectorIntegration:
    """Validate outbound activity dispatching and token handling for Bot Connector."""

    def test_given_bot_credentials_when_token_requested_then_returns_jwt(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BOT_APP_ID", "test-bot-id")
        monkeypatch.setenv("BOT_APP_PASSWORD", "test-secret")
        monkeypatch.setenv("AZURE_TENANT_ID", "test-tenant-id")

        class MockResponse:
            status_code = 200

            def json(self) -> dict[str, Any]:
                return {"access_token": "mock-jwt-token", "expires_in": 3600}

        def mock_post(*args: Any, **kwargs: Any) -> MockResponse:
            return MockResponse()

        monkeypatch.setattr("httpx.Client.post", mock_post)

        from hr_time_leave.app import _BOT_TOKEN_CACHE

        _BOT_TOKEN_CACHE.clear()

        token = get_bot_framework_token()
        assert token == "mock-jwt-token"

    def test_given_cached_token_when_requested_again_then_returns_cached(
        self,
    ) -> None:
        from hr_time_leave.app import _BOT_TOKEN_CACHE

        _BOT_TOKEN_CACHE["token"] = "cached-token"
        _BOT_TOKEN_CACHE["expires_at"] = time.time() + 3000.0

        token = get_bot_framework_token()
        assert token == "cached-token"

    def test_given_valid_activity_payload_when_dispatched_then_posts_to_connector_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[dict[str, Any]] = []

        class MockResponse:
            status_code = 200
            text = "OK"

        def mock_post(client_self: Any, url: str, **kwargs: Any) -> MockResponse:
            calls.append({"url": url, "kwargs": kwargs})
            return MockResponse()

        monkeypatch.setattr("httpx.Client.post", mock_post)
        app_mod = sys.modules["hr_time_leave.app"]
        monkeypatch.setattr(
            app_mod, "get_bot_framework_token", lambda: "mock-token"
        )

        success = send_bot_framework_activity(
            service_url="https://webchat.botframework.com/v3/",
            conversation_id="conv-abc",
            activity_payload={"type": "message", "text": "hello"},
            reply_to_id="act-xyz",
        )
        assert success is True
        assert len(calls) == 1
        assert (
            calls[0]["url"]
            == "https://webchat.botframework.com/v3/conversations/conv-abc/activities/act-xyz"
        )
        assert (
            calls[0]["kwargs"]["headers"]["Authorization"]
            == "Bearer mock-token"
        )

    def test_given_connector_failure_when_dispatched_then_returns_false_cleanly(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class MockResponse:
            status_code = 500
            text = "Internal Server Error"

        def mock_post(client_self: Any, url: str, **kwargs: Any) -> MockResponse:
            return MockResponse()

        monkeypatch.setattr("httpx.Client.post", mock_post)
        app_mod = sys.modules["hr_time_leave.app"]
        monkeypatch.setattr(
            app_mod, "get_bot_framework_token", lambda: None
        )

        success = send_bot_framework_activity(
            service_url="https://smba.trafficmanager.net/teams/v3",
            conversation_id="conv-def",
            activity_payload={"type": "message", "text": "hello"},
        )
        assert success is False

    def test_given_inbound_message_with_service_url_then_triggers_outbound_dispatch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        dispatched: list[dict[str, Any]] = []

        def mock_send(
            service_url: str,
            conversation_id: str,
            activity_payload: dict[str, Any],
            reply_to_id: str | None = None,
        ) -> bool:
            dispatched.append(
                {
                    "service_url": service_url,
                    "conversation_id": conversation_id,
                    "payload": activity_payload,
                    "reply_to_id": reply_to_id,
                }
            )
            return True

        app_mod = sys.modules["hr_time_leave.app"]
        monkeypatch.setattr(
            app_mod, "send_bot_framework_activity", mock_send
        )

        activity = {
            "type": "message",
            "id": "act-999",
            "text": "hi",
            "serviceUrl": "https://webchat.botframework.com/v3/",
            "from": {"id": "usr-1", "name": "Bob"},
            "conversation": {"id": "conv-999"},
        }
        result = process_bot_activity(activity)
        assert result["status"] == "processed"
        assert len(dispatched) == 1
        assert (
            dispatched[0]["service_url"]
            == "https://webchat.botframework.com/v3/"
        )
        assert dispatched[0]["conversation_id"] == "conv-999"
        assert dispatched[0]["reply_to_id"] == "act-999"
        assert (
            "Enterprise HR Time and Leave Copilot"
            in dispatched[0]["payload"]["text"]
        )

    def test_given_conversation_update_when_user_joins_then_sends_welcome_activity(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        dispatched: list[dict[str, Any]] = []

        def mock_send(
            service_url: str,
            conversation_id: str,
            activity_payload: dict[str, Any],
            reply_to_id: str | None = None,
        ) -> bool:
            dispatched.append(activity_payload)
            return True

        app_mod = sys.modules["hr_time_leave.app"]
        monkeypatch.setattr(
            app_mod, "send_bot_framework_activity", mock_send
        )
        monkeypatch.setenv("BOT_APP_ID", "bot-id-123")

        activity = {
            "type": "conversationUpdate",
            "serviceUrl": "https://webchat.botframework.com/v3/",
            "conversation": {"id": "conv-welcome"},
            "membersAdded": [
                {"id": "bot-id-123", "name": "Bot"},
                {"id": "user-456", "name": "New Employee"},
            ],
        }
        result = process_bot_activity(activity)
        assert result["status"] == "acknowledged"
        assert len(dispatched) == 1
        welcome_msg = dispatched[0]["text"].lower()
        assert "copilot" in welcome_msg or "assist" in welcome_msg


class TestDockerfileCompliance:
    """Validate Dockerfile syntax, non-root security context, and directives."""

    def test_given_dockerfile_exists_then_targets_python_311_slim(self) -> None:
        assert DOCKERFILE_PATH.is_file(), f"Dockerfile missing at {DOCKERFILE_PATH}"
        content = DOCKERFILE_PATH.read_text(encoding="utf-8")
        assert "FROM python:3.11-slim" in content

    def test_given_dockerfile_then_executes_as_non_root_user(self) -> None:
        content = DOCKERFILE_PATH.read_text(encoding="utf-8")
        assert "useradd" in content
        assert "10001" in content
        assert "USER appuser:10001" in content

    def test_given_dockerfile_then_exposes_port_8000(self) -> None:
        content = DOCKERFILE_PATH.read_text(encoding="utf-8")
        assert "EXPOSE 8000" in content
        assert "PORT=8000" in content

    def test_given_dockerfile_then_defines_healthcheck(self) -> None:
        content = DOCKERFILE_PATH.read_text(encoding="utf-8")
        assert "HEALTHCHECK" in content
        assert "/healthz" in content

    def test_given_dockerfile_then_runs_uvicorn_command(self) -> None:
        content = DOCKERFILE_PATH.read_text(encoding="utf-8")
        assert "CMD" in content
        assert "uvicorn" in content
        assert "hr_time_leave.app:app" in content

    def test_given_dockerignore_then_excludes_sensitive_patterns(self) -> None:
        assert DOCKERIGNORE_PATH.is_file(), f"Missing at {DOCKERIGNORE_PATH}"
        content = DOCKERIGNORE_PATH.read_text(encoding="utf-8")
        assert ".git" in content
        assert "__pycache__" in content
        assert ".venv" in content
        assert ".copilot-tracking" in content
