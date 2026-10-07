"""Unit and integration tests for containerized web runtime and background Functions.

Validates:
1. FastAPI /healthz and /readyz probes.
2. Bot Framework /api/messages activity ingestion and error handling.
3. Service Bus SLA reminder and escalation trigger in function_app.py.
4. Dockerfile and .dockerignore security and operational compliance.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from hr_time_leave import (
    SensitiveTicketData,
    Ticket,
    TicketType,
    app,
    process_bot_activity,
    process_service_bus_message,
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
