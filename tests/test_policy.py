"""Comprehensive unit tests for grounded HR policy retrieval and question answering.

Verifies:
- Structured ingestion and chunking of SOP-HR-042 v3.2.
- AC-001: 1-2 days annual leave notice returns 48-hour rule citing SOP-HR-042 v3.2.
- AC-002: Out-of-corpus question is refused with unsupported status and HR escalation.
- AC-003: Policy conflicts across sources are detected and definitive answers withheld.
- Hybrid BM25/dense retrieval behavior and citation formatting.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hr_time_leave.policy import (
    DEFAULT_HR_ESCALATION_PATH,
    PolicyCitation,
    PolicyDocument,
    PolicyEngine,
    PolicySection,
    QueryResultStatus,
    load_policy_file,
)

_SOP_PATH = (
    Path(__file__).parent.parent
    / ".copilot-tracking"
    / "research"
    / "workshop-input"
    / "policies"
    / "sop-hr-time-and-leave.md"
)


@pytest.fixture
def sop_document() -> PolicyDocument:
    """Fixture providing parsed SOP-HR-042 v3.2 policy document."""
    assert _SOP_PATH.is_file(), f"SOP policy file missing at {_SOP_PATH}"
    return load_policy_file(_SOP_PATH)


@pytest.fixture
def policy_engine(sop_document: PolicyDocument) -> PolicyEngine:
    """Fixture providing a PolicyEngine pre-indexed with SOP-HR-042 v3.2."""
    engine = PolicyEngine()
    engine.ingest_document(sop_document)
    return engine


def test_given_sop_markdown_when_parsed_then_metadata_and_sections_preserved(
    sop_document: PolicyDocument,
) -> None:
    """Verify policy parsing captures document ID, version, dates, and sections."""
    assert sop_document.document_id == "SOP-HR-042"
    assert sop_document.version == "3.2"
    assert sop_document.effective_date == "January 1, 2026"
    assert sop_document.organization == "NovaTech Global Solutions"
    assert sop_document.title == (
        "Standard Operating Procedure (SOP): Workforce Time, Attendance & "
        "Leave Management"
    )

    sec_map = {s.section_number: s for s in sop_document.sections}
    expected_sections = [
        "1",
        "2.1",
        "2.2",
        "3.1",
        "3.2",
        "4.1",
        "4.2",
        "4.3",
        "5.1",
        "5.2",
        "6.1",
        "6.2",
        "7.1",
        "7.2",
    ]
    for sec_num in expected_sections:
        assert sec_num in sec_map, f"Missing expected section {sec_num}"

    sec_41 = sec_map["4.1"]
    assert sec_41.section_title == "Annual Leave (Paid Vacation)"
    assert sec_41.parent_title == "Paid Time Off (PTO) & Leave Categories"
    assert len(sec_41.clauses) >= 3

    # Check advance notice clause is extracted
    notice_clause = next(
        (c for c in sec_41.clauses if "48 hours" in c and "1 to 2" in c),
        None,
    )
    assert notice_clause is not None
    assert "48 hours" in notice_clause


def test_given_ac001_when_asking_annual_leave_notice_then_returns_48h_and_citation(
    policy_engine: PolicyEngine,
) -> None:
    """AC-001: 1-2 annual leave days notice returns 48h rule citing SOP v3.2."""
    question = "Which notice period applies to one to two annual-leave days?"
    answer = policy_engine.answer_query(question)

    assert answer.status == QueryResultStatus.ANSWERED
    assert "48 hours" in answer.answer.lower()
    assert "sop-hr-042" in answer.answer.lower()
    assert "3.2" in answer.answer

    assert len(answer.citations) == 1
    citation = answer.citations[0]
    assert citation.document_id == "SOP-HR-042"
    assert citation.version == "3.2"
    assert citation.section_number == "4.1"
    assert citation.section_title == "Annual Leave (Paid Vacation)"
    assert citation.clause_text is not None
    assert "48 hours" in citation.clause_text
    assert (
        citation.format_citation()
        == "SOP-HR-042 v3.2, Section 4.1: Annual Leave (Paid Vacation)"
    )


def test_given_ac001_variation_when_asked_then_returns_grounded_answer(
    policy_engine: PolicyEngine,
) -> None:
    """AC-001 variation: Alternative user phrasing still retrieves 48h notice rule."""
    question = (
        "How much advance notice is required for 1 to 2 consecutive days of vacation?"
    )
    answer = policy_engine.answer_query(question)

    assert answer.status == QueryResultStatus.ANSWERED
    assert "48 hours" in answer.answer.lower()
    assert len(answer.citations) >= 1
    assert answer.citations[0].section_number == "4.1"


def test_given_ac002_when_out_of_corpus_question_then_unsupported_and_escalated(
    policy_engine: PolicyEngine,
) -> None:
    """AC-002: Out-of-corpus query is refused with unsupported status and escalation."""
    out_of_corpus_questions = [
        "Can I bring my pet parrot to the customer demo room?",
        "What is the corporate discount rate for Gold's Gym membership?",
        "What is the stock option vesting cliff for new senior engineers?",
        "Can I expense Michelin star dinners on client travel?",
    ]

    for question in out_of_corpus_questions:
        answer = policy_engine.answer_query(question)
        assert answer.status == QueryResultStatus.UNSUPPORTED, (
            f"Question '{question}' was not refused as unsupported"
        )
        assert "outside the approved hr policy corpus" in answer.answer.lower()
        assert answer.escalation_path == DEFAULT_HR_ESCALATION_PATH
        assert DEFAULT_HR_ESCALATION_PATH in answer.answer
        assert answer.citations == [], (
            "Unsupported query must not hallucinate citations"
        )


def test_given_ac003_when_cross_source_conflict_registered_then_withholds_answer(
    policy_engine: PolicyEngine,
) -> None:
    """AC-003: Registered conflict across sources withholds answer and cites both."""
    # Register conflict between SOP-HR-042 and SPEC-HRIS-014 regarding auto-escalation
    spec_doc = PolicyDocument(
        document_id="SPEC-HRIS-014",
        version="1.0",
        title="Technical Specification: HRIS Ticket SLA Processing",
        sections=[
            PolicySection(
                document_id="SPEC-HRIS-014",
                version="1.0",
                section_number="3.2",
                section_title="SLA Escalation Trigger",
                content=(
                    "If a ticket remains unaddressed after 48 hours, it auto-escalates "
                    "to the HR Administrator Queue."
                ),
                clauses=[
                    "If a ticket remains unaddressed after 48 hours, it escalates."
                ],
            )
        ],
    )
    policy_engine.ingest_document(spec_doc)

    policy_engine.register_policy_conflict(
        source_a="SOP-HR-042",
        source_b="SPEC-HRIS-014",
        topic_keywords=["auto-escalat", "escalat", "sla threshold"],
        description=(
            "SOP-HR-042 Section 5.2 specifies auto-escalation after 72 hours, whereas "
            "SPEC-HRIS-014 Section 3.2 specifies auto-escalation after 48 hours."
        ),
    )

    question = "When does an unreviewed ticket auto-escalate under the SLA policy?"
    answer = policy_engine.answer_query(question)

    assert answer.status == QueryResultStatus.CONFLICT
    assert "conflict was detected" in answer.answer.lower()
    assert "definitive answer is withheld" in answer.answer.lower()
    assert "hr policy owner" in answer.answer.lower()
    assert answer.escalation_path == DEFAULT_HR_ESCALATION_PATH

    cited_docs = {c.document_id for c in answer.citations}
    assert "SOP-HR-042" in cited_docs
    assert "SPEC-HRIS-014" in cited_docs


def test_given_ac003_when_dynamic_multi_source_conflict_then_detected(
    policy_engine: PolicyEngine,
) -> None:
    """AC-003: Dynamic heuristic conflict between 2 sources is detected."""
    # Ingest regional amendment with conflicting annual leave notice rule
    regional_doc = PolicyDocument(
        document_id="SOP-HR-042-REGIONAL",
        version="1.0",
        title="Regional Amendment: Workforce Leave Management",
        sections=[
            PolicySection(
                document_id="SOP-HR-042-REGIONAL",
                version="1.0",
                section_number="4.1",
                section_title="Annual Leave Notice Requirements",
                content=(
                    "Requests for 1 to 2 consecutive business days: "
                    "Must be submitted at least 24 hours in advance."
                ),
                clauses=[
                    "Requests for 1 to 2 consecutive business days: "
                    "Must be submitted at least 24 hours in advance."
                ],
            )
        ],
    )
    policy_engine.ingest_document(regional_doc)

    question = "What is the advance notice requirement for 1 to 2 days of annual leave?"
    answer = policy_engine.answer_query(question)

    assert answer.status == QueryResultStatus.CONFLICT
    assert "conflict" in answer.answer.lower()
    assert "definitive answer is withheld" in answer.answer.lower()
    cited_docs = {c.document_id for c in answer.citations}
    assert "SOP-HR-042" in cited_docs
    assert "SOP-HR-042-REGIONAL" in cited_docs


def test_given_empty_engine_when_queried_then_refuses_gracefully() -> None:
    """Empty policy engine safely refuses queries without crashing."""
    engine = PolicyEngine()
    answer = engine.answer_query("What is the annual leave policy?")
    assert answer.status == QueryResultStatus.UNSUPPORTED
    assert answer.citations == []


def test_given_missing_policy_file_when_loaded_then_raises_file_not_found() -> None:
    """Loading a non-existent policy file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_policy_file("non_existent_policy_file.md")


def test_given_hybrid_retrieval_when_scored_then_ranks_relevant_sections(
    policy_engine: PolicyEngine,
) -> None:
    """Hybrid retrieval scores combine BM25 and dense similarity with valid ordering."""
    query = "overtime meal break and standard working hours"
    results = policy_engine.retrieve(query, top_k=3)
    assert len(results) > 0
    top_result = results[0]
    assert top_result.hybrid_score > 0.0
    assert top_result.section.section_number in ("2.1", "2.2", "3.1", "3.2")
    assert top_result.bm25_score >= 0.0
    assert top_result.dense_score >= 0.0


def test_given_citation_when_formatted_then_matches_standard() -> None:
    """PolicyCitation formatting produces expected standardized string."""
    citation = PolicyCitation(
        document_id="SOP-HR-042",
        version="3.2",
        section_number="6.2",
        section_title="Data Privacy & Guardrails",
    )
    assert (
        citation.format_citation()
        == "SOP-HR-042 v3.2, Section 6.2: Data Privacy & Guardrails"
    )
