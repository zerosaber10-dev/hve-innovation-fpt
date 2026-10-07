"""Grounded policy retrieval and structured ingestion for HR policies."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Final

DEFAULT_HR_ESCALATION_PATH: Final[str] = (
    "HR Operations (hr-operations@example.com / HR Operations Administrator Queue)"
)
DEFAULT_RELEVANCE_THRESHOLD: Final[float] = 0.18

_STOPWORDS: Final[frozenset[str]] = frozenset(
    {
        "a",
        "about",
        "above",
        "after",
        "again",
        "against",
        "all",
        "am",
        "an",
        "and",
        "any",
        "are",
        "as",
        "at",
        "be",
        "because",
        "been",
        "before",
        "being",
        "below",
        "between",
        "both",
        "but",
        "by",
        "can",
        "cannot",
        "could",
        "did",
        "do",
        "does",
        "doing",
        "down",
        "during",
        "each",
        "few",
        "for",
        "from",
        "further",
        "had",
        "has",
        "have",
        "having",
        "he",
        "her",
        "here",
        "hers",
        "herself",
        "him",
        "himself",
        "his",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "itself",
        "me",
        "more",
        "most",
        "my",
        "myself",
        "no",
        "nor",
        "not",
        "of",
        "off",
        "on",
        "once",
        "only",
        "or",
        "other",
        "ought",
        "our",
        "ours",
        "ourselves",
        "out",
        "over",
        "own",
        "same",
        "she",
        "should",
        "so",
        "some",
        "such",
        "than",
        "that",
        "the",
        "their",
        "theirs",
        "them",
        "themselves",
        "then",
        "there",
        "these",
        "they",
        "this",
        "those",
        "through",
        "to",
        "too",
        "under",
        "until",
        "up",
        "very",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "while",
        "who",
        "whom",
        "why",
        "with",
        "would",
        "you",
        "your",
        "yours",
        "yourself",
        "yourselves",
    }
)


_NUMBER_WORDS: Final[dict[str, str]] = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "twelve": "12",
    "fifteen": "15",
    "eighteen": "18",
    "twenty-four": "24",
    "forty": "40",
    "forty-eight": "48",
    "seventy-two": "72",
}


class QueryResultStatus(StrEnum):
    """Execution status of a policy query lookup."""

    ANSWERED = "ANSWERED"
    UNSUPPORTED = "UNSUPPORTED"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True)
class PolicyCitation:
    """Explicit citation identifying the authoritative policy source."""

    document_id: str
    version: str
    section_number: str
    section_title: str
    clause_text: str | None = None

    def format_citation(self) -> str:
        """Render a standardized human-readable citation string."""
        return (
            f"{self.document_id} v{self.version}, "
            f"Section {self.section_number}: {self.section_title}"
        )


@dataclass(frozen=True)
class PolicySection:
    """Structured policy chunk containing metadata, text, and clauses."""

    document_id: str
    version: str
    section_number: str
    section_title: str
    content: str
    clauses: list[str]
    parent_title: str | None = None


@dataclass(frozen=True)
class PolicyDocument:
    """Full policy document model preserving version and structured sections."""

    document_id: str
    version: str
    title: str
    effective_date: str | None = None
    organization: str | None = None
    applies_to: str | None = None
    sections: list[PolicySection] = field(default_factory=list)


@dataclass(frozen=True)
class RetrievalScore:
    """Scored policy retrieval result with hybrid rankings."""

    section: PolicySection
    bm25_score: float
    dense_score: float
    hybrid_score: float
    best_clause: str | None = None


@dataclass(frozen=True)
class PolicyConflictRule:
    """Declared conflict definition between two sources on a specific topic."""

    source_a: str
    source_b: str
    topic_keywords: list[str]
    description: str


@dataclass(frozen=True)
class PolicyAnswer:
    """Grounded policy answer containing citations, status, and escalation."""

    status: QueryResultStatus
    question: str
    answer: str
    citations: list[PolicyCitation]
    confidence_score: float
    escalation_path: str | None = None
    conflict_details: str | None = None


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric terms excluding stopwords."""
    raw_tokens = re.findall(r"[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)?", text.lower())
    tokens: list[str] = []
    for t in raw_tokens:
        if (len(t) >= 2 or t.isdigit()) and t not in _STOPWORDS and t != "s":
            tokens.append(t)
            if t in _NUMBER_WORDS:
                tokens.append(_NUMBER_WORDS[t])
    return tokens


def _extract_char_ngrams(text: str, n: int = 3) -> dict[str, int]:
    """Extract character n-gram frequencies for subword semantic similarity."""
    cleaned = re.sub(r"\s+", " ", text.lower().strip())
    if len(cleaned) < n:
        return {cleaned: 1} if cleaned else {}
    counts: dict[str, int] = {}
    for i in range(len(cleaned) - n + 1):
        gram = cleaned[i : i + n]
        counts[gram] = counts.get(gram, 0) + 1
    return counts


def _cosine_similarity(vec_a: dict[str, int], vec_b: dict[str, int]) -> float:
    """Calculate cosine similarity between two frequency vectors."""
    if not vec_a or not vec_b:
        return 0.0
    common_keys = set(vec_a.keys()) & set(vec_b.keys())
    if not common_keys:
        return 0.0
    dot_product = sum(vec_a[k] * vec_b[k] for k in common_keys)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def parse_policy_document(markdown_text: str) -> PolicyDocument:
    """Parse Markdown policy into a structured PolicyDocument with chunks.

    Preserves document ID, version, effective date, organization, and decomposes
    the body into hierarchical sections and individual clauses.
    """
    doc_id_match = re.search(r"\*\*Document ID:\*\*\s*([^\n\r]+)", markdown_text)
    document_id = doc_id_match.group(1).strip() if doc_id_match else "UNKNOWN-DOC"

    version_match = re.search(r"\*\*Version:\*\*\s*([^\n\r]+)", markdown_text)
    version = version_match.group(1).strip() if version_match else "1.0"

    date_match = re.search(r"\*\*Effective Date:\*\*\s*([^\n\r]+)", markdown_text)
    effective_date = date_match.group(1).strip() if date_match else None

    org_match = re.search(r"\*\*Organization:\*\*\s*([^\n\r]+)", markdown_text)
    organization = org_match.group(1).strip() if org_match else None

    applies_match = re.search(r"\*\*Applies To:\*\*\s*([^\n\r]+)", markdown_text)
    applies_to = applies_match.group(1).strip() if applies_match else None

    title_match = re.search(r"^#\s+([^\n\r]+)", markdown_text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "HR Policy"

    sections: list[PolicySection] = []
    lines = markdown_text.splitlines()

    current_parent_title: str | None = None
    current_sec_num: str | None = None
    current_sec_title: str | None = None
    current_content_lines: list[str] = []

    def commit_section() -> None:
        nonlocal current_sec_num, current_sec_title, current_content_lines
        if current_sec_num and current_sec_title:
            raw_content = "\n".join(current_content_lines).strip()
            clauses = _extract_clauses(raw_content)
            sections.append(
                PolicySection(
                    document_id=document_id,
                    version=version,
                    section_number=current_sec_num,
                    section_title=current_sec_title,
                    content=raw_content,
                    clauses=clauses,
                    parent_title=current_parent_title,
                )
            )
        current_content_lines = []

    heading_pattern = re.compile(r"^(#{2,3})\s+(\d+(?:\.\d+)?)\.?\s+(.+)$")

    for line in lines:
        stripped = line.strip()
        h_match = heading_pattern.match(stripped)
        if h_match:
            level = len(h_match.group(1))
            sec_num = h_match.group(2).strip()
            sec_title = h_match.group(3).strip()

            commit_section()

            if level == 2:
                current_parent_title = sec_title
                current_sec_num = sec_num
                current_sec_title = sec_title
            else:  # level == 3
                current_sec_num = sec_num
                current_sec_title = sec_title
        else:
            if current_sec_num is not None:
                current_content_lines.append(line)

    commit_section()

    return PolicyDocument(
        document_id=document_id,
        version=version,
        title=title,
        effective_date=effective_date,
        organization=organization,
        applies_to=applies_to,
        sections=sections,
    )


def _extract_clauses(content: str) -> list[str]:
    """Extract individual clauses and rules from section content."""
    clauses: list[str] = []
    lines = content.splitlines()
    buffer: list[str] = []
    parent_bullet: str | None = None

    def flush_buffer() -> None:
        nonlocal buffer
        if buffer:
            combined = " ".join(buffer).strip()
            if combined:
                clauses.append(combined)
            buffer = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped == "---":
            flush_buffer()
            continue

        indent = len(line) - len(line.lstrip())
        bullet_match = re.match(r"^(\*|-|\d+\.)\s+(.+)$", stripped)
        if bullet_match:
            bullet_body = bullet_match.group(2).strip()
            if indent == 0:
                flush_buffer()
                if bullet_body.endswith(":") or line.rstrip().endswith(":"):
                    cleaned_parent = re.sub(r"^\*+|\*+$", "", bullet_body)
                    parent_bullet = cleaned_parent.strip().rstrip(":")
                else:
                    parent_bullet = None
                    buffer.append(bullet_body)
            else:
                flush_buffer()
                cleaned_body = re.sub(r"^\*+|\*+$", "", bullet_body).strip()
                if parent_bullet:
                    clauses.append(f"{parent_bullet}: {cleaned_body}")
                else:
                    clauses.append(cleaned_body)
        else:
            buffer.append(stripped)

    flush_buffer()
    return [c for c in clauses if c]


def load_policy_file(file_path: str | Path) -> PolicyDocument:
    """Read a local markdown policy file and parse into a PolicyDocument."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Policy file not found: {file_path}")
    text = path.read_text(encoding="utf-8")
    return parse_policy_document(text)


class PolicyEngine:
    """Grounded hybrid policy retrieval and question answering engine."""

    def __init__(
        self,
        relevance_threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
        escalation_path: str = DEFAULT_HR_ESCALATION_PATH,
    ) -> None:
        self.relevance_threshold: float = relevance_threshold
        self.escalation_path: str = escalation_path
        self._documents: dict[str, PolicyDocument] = {}
        self._sections: list[PolicySection] = []
        self._section_tokens: list[list[str]] = []
        self._section_char_ngrams: list[dict[str, int]] = []
        self._doc_freq: dict[str, int] = {}
        self._avg_doc_len: float = 0.0
        self._conflict_rules: list[PolicyConflictRule] = []

    def ingest_document(self, document: PolicyDocument) -> None:
        """Ingest a parsed PolicyDocument and re-index for hybrid search."""
        key = f"{document.document_id}:{document.version}"
        self._documents[key] = document
        self._reindex()

    def ingest_markdown(self, markdown_text: str) -> PolicyDocument:
        """Parse and ingest raw Markdown policy content."""
        doc = parse_policy_document(markdown_text)
        self.ingest_document(doc)
        return doc

    def ingest_file(self, file_path: str | Path) -> PolicyDocument:
        """Load and ingest a policy Markdown file from disk."""
        doc = load_policy_file(file_path)
        self.ingest_document(doc)
        return doc

    def register_policy_conflict(
        self,
        source_a: str,
        source_b: str,
        topic_keywords: list[str],
        description: str,
    ) -> None:
        """Register a known cross-source policy conflict for detection."""
        self._conflict_rules.append(
            PolicyConflictRule(
                source_a=source_a,
                source_b=source_b,
                topic_keywords=[k.lower() for k in topic_keywords],
                description=description,
            )
        )

    def _reindex(self) -> None:
        """Build hybrid BM25 and dense representation indices."""
        self._sections = []
        for doc in self._documents.values():
            self._sections.extend(doc.sections)

        self._section_tokens = []
        self._section_char_ngrams = []
        self._doc_freq = {}
        total_tokens = 0

        for sec in self._sections:
            combined_text = (
                f"{sec.section_number} {sec.section_title} "
                f"{sec.parent_title or ''} {sec.content}"
            )
            tokens = _tokenize(combined_text)
            self._section_tokens.append(tokens)
            total_tokens += len(tokens)

            unique_tokens = set(tokens)
            for token in unique_tokens:
                self._doc_freq[token] = self._doc_freq.get(token, 0) + 1

            self._section_char_ngrams.append(_extract_char_ngrams(combined_text))

        n_sections = len(self._sections)
        self._avg_doc_len = (total_tokens / n_sections) if n_sections > 0 else 0.0

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalScore]:
        """Perform hybrid BM25 and dense semantic search across indexed policies."""
        if not self._sections:
            return []

        query_tokens = _tokenize(query)
        query_ngrams = _extract_char_ngrams(query)
        n_sections = len(self._sections)
        k1 = 1.5
        b = 0.75

        bm25_scores: list[float] = []
        dense_scores: list[float] = []

        for i in range(n_sections):
            # BM25 score calculation
            score = 0.0
            sec_len = len(self._section_tokens[i])
            token_counts: dict[str, int] = {}
            for t in self._section_tokens[i]:
                token_counts[t] = token_counts.get(t, 0) + 1

            for qt in query_tokens:
                if qt in self._doc_freq:
                    df = self._doc_freq[qt]
                    idf = math.log(1.0 + (n_sections - df + 0.5) / (df + 0.5))
                    tf = token_counts.get(qt, 0)
                    denom = tf + k1 * (
                        1.0 - b + b * (sec_len / (self._avg_doc_len or 1.0))
                    )
                    score += idf * ((tf * (k1 + 1.0)) / (denom or 1.0))
            bm25_scores.append(score)

            # Dense subword semantic similarity
            dense_sim = _cosine_similarity(query_ngrams, self._section_char_ngrams[i])
            dense_scores.append(dense_sim)

        # Normalize BM25
        max_bm25 = max(bm25_scores) if bm25_scores else 0.0
        normalized_bm25 = (
            [s / max_bm25 for s in bm25_scores]
            if max_bm25 > 0.0
            else [0.0] * n_sections
        )

        results: list[RetrievalScore] = []
        unique_query_tokens = set(query_tokens)
        for i in range(n_sections):
            sec_token_set = set(self._section_tokens[i])
            matched_tokens = sum(1 for qt in unique_query_tokens if qt in sec_token_set)
            query_coverage = (
                matched_tokens / len(unique_query_tokens)
                if unique_query_tokens
                else 0.0
            )

            # Guard against spurious matches where only 1 generic token matches
            coverage_factor = 1.0
            if len(unique_query_tokens) >= 2 and matched_tokens < 2:
                coverage_factor = 0.1
            elif query_coverage < 0.3:
                coverage_factor = query_coverage / 0.3

            h_score = (
                0.6 * normalized_bm25[i] + 0.4 * dense_scores[i]
            ) * coverage_factor
            if h_score > 0.0:
                best_clause = self._find_best_clause(query, self._sections[i])
                results.append(
                    RetrievalScore(
                        section=self._sections[i],
                        bm25_score=bm25_scores[i],
                        dense_score=dense_scores[i],
                        hybrid_score=h_score,
                        best_clause=best_clause,
                    )
                )

        results.sort(key=lambda r: r.hybrid_score, reverse=True)
        return results[:top_k]

    def _find_best_clause(self, query: str, section: PolicySection) -> str | None:
        """Find the single clause most relevant to the query within a section."""
        if not section.clauses:
            return None
        query_tokens = set(_tokenize(query))
        query_ngrams = _extract_char_ngrams(query)

        best_score = -1.0
        best_clause: str | None = None

        for clause in section.clauses:
            clause_tokens = set(_tokenize(clause))
            overlap = len(query_tokens & clause_tokens)
            clause_ngrams = _extract_char_ngrams(clause)
            sim = _cosine_similarity(query_ngrams, clause_ngrams)
            combined = 0.7 * (overlap / (len(query_tokens) or 1)) + 0.3 * sim
            if combined > best_score:
                best_score = combined
                best_clause = clause

        return best_clause

    def _detect_conflicts(
        self, query: str, retrieved: list[RetrievalScore]
    ) -> tuple[bool, str | None, list[PolicyCitation]]:
        """Evaluate whether query hits a declared or multi-source policy conflict."""
        query_lower = query.lower()

        # 1. Check registered conflict rules
        for rule in self._conflict_rules:
            matches_rule = any(kw in query_lower for kw in rule.topic_keywords)
            if matches_rule:
                # Check if both sources are in the index or retrieved results
                indexed_doc_ids = {d.document_id for d in self._documents.values()}
                if (
                    rule.source_a in indexed_doc_ids
                    and rule.source_b in indexed_doc_ids
                ):
                    matching_citations: list[PolicyCitation] = []
                    for r in retrieved:
                        if r.section.document_id in (rule.source_a, rule.source_b):
                            matching_citations.append(
                                PolicyCitation(
                                    document_id=r.section.document_id,
                                    version=r.section.version,
                                    section_number=r.section.section_number,
                                    section_title=r.section.section_title,
                                    clause_text=r.best_clause,
                                )
                            )
                    # If specific section citations weren't both top-retrieved,
                    # synthesize base citations
                    found_doc_ids = {c.document_id for c in matching_citations}
                    if rule.source_a not in found_doc_ids:
                        doc_a = next(
                            (
                                d
                                for d in self._documents.values()
                                if d.document_id == rule.source_a
                            ),
                            None,
                        )
                        if doc_a and doc_a.sections:
                            matching_citations.append(
                                PolicyCitation(
                                    document_id=doc_a.document_id,
                                    version=doc_a.version,
                                    section_number=doc_a.sections[0].section_number,
                                    section_title=doc_a.sections[0].section_title,
                                )
                            )
                    if rule.source_b not in found_doc_ids:
                        doc_b = next(
                            (
                                d
                                for d in self._documents.values()
                                if d.document_id == rule.source_b
                            ),
                            None,
                        )
                        if doc_b and doc_b.sections:
                            matching_citations.append(
                                PolicyCitation(
                                    document_id=doc_b.document_id,
                                    version=doc_b.version,
                                    section_number=doc_b.sections[0].section_number,
                                    section_title=doc_b.sections[0].section_title,
                                )
                            )
                    return True, rule.description, matching_citations

        # 2. Dynamic heuristic conflict detection across multi-source top results
        if len(retrieved) >= 2:
            top_sources = {r.section.document_id for r in retrieved[:3]}
            if len(top_sources) >= 2:
                # Compare high-scoring sections from distinct documents
                r1 = retrieved[0]
                r2 = next(
                    (
                        r
                        for r in retrieved[1:]
                        if r.section.document_id != r1.section.document_id
                    ),
                    None,
                )
                if r2 and r1.hybrid_score > 0.25 and r2.hybrid_score > 0.25:
                    c1_text = r1.best_clause or r1.section.content
                    c2_text = r2.best_clause or r2.section.content
                    # Check for contradictory numerical or threshold directives
                    nums1 = set(re.findall(r"\b\d+\b", c1_text))
                    nums2 = set(re.findall(r"\b\d+\b", c2_text))
                    if nums1 and nums2 and nums1 != nums2:
                        conflict_desc = (
                            f"Contradictory policy terms detected between "
                            f"{r1.section.document_id} (Section "
                            f"{r1.section.section_number}) and "
                            f"{r2.section.document_id} (Section "
                            f"{r2.section.section_number})."
                        )
                        citations = [
                            PolicyCitation(
                                document_id=r1.section.document_id,
                                version=r1.section.version,
                                section_number=r1.section.section_number,
                                section_title=r1.section.section_title,
                                clause_text=r1.best_clause,
                            ),
                            PolicyCitation(
                                document_id=r2.section.document_id,
                                version=r2.section.version,
                                section_number=r2.section.section_number,
                                section_title=r2.section.section_title,
                                clause_text=r2.best_clause,
                            ),
                        ]
                        return True, conflict_desc, citations

        return False, None, []

    def answer_query(self, question: str) -> PolicyAnswer:
        """Answer a policy query with citations, or refuse out-of-corpus/conflicts."""
        retrieved = self.retrieve(question, top_k=5)

        # Check for conflicts across sources (AC-003)
        has_conflict, conflict_desc, conflict_citations = self._detect_conflicts(
            question, retrieved
        )
        if has_conflict:
            answer_text = (
                f"A policy conflict was detected regarding your inquiry: "
                f"{conflict_desc} In accordance with Responsible AI and HR "
                "compliance guardrails, a definitive answer is withheld until the "
                "conflict is resolved by the HR policy owner. "
                f"Please escalate to {self.escalation_path}."
            )
            return PolicyAnswer(
                status=QueryResultStatus.CONFLICT,
                question=question,
                answer=answer_text,
                citations=conflict_citations,
                confidence_score=retrieved[0].hybrid_score if retrieved else 0.0,
                escalation_path=self.escalation_path,
                conflict_details=conflict_desc,
            )

        # Check if question is outside the approved policy corpus (AC-002)
        if not retrieved or retrieved[0].hybrid_score < self.relevance_threshold:
            answer_text = (
                "This question is outside the approved HR policy corpus and "
                "cannot be answered authoritatively. The agent does not "
                "generate unverified policy rules. For guidance on this topic, "
                f"please contact {self.escalation_path}."
            )
            return PolicyAnswer(
                status=QueryResultStatus.UNSUPPORTED,
                question=question,
                answer=answer_text,
                citations=[],
                confidence_score=retrieved[0].hybrid_score if retrieved else 0.0,
                escalation_path=self.escalation_path,
            )

        # Grounded answer synthesis (AC-001)
        top = retrieved[0]
        citation = PolicyCitation(
            document_id=top.section.document_id,
            version=top.section.version,
            section_number=top.section.section_number,
            section_title=top.section.section_title,
            clause_text=top.best_clause,
        )

        formatted_answer = _synthesize_grounded_answer(
            question=question,
            section=top.section,
            best_clause=top.best_clause,
        )

        return PolicyAnswer(
            status=QueryResultStatus.ANSWERED,
            question=question,
            answer=formatted_answer,
            citations=[citation],
            confidence_score=top.hybrid_score,
        )


def _synthesize_grounded_answer(
    question: str, section: PolicySection, best_clause: str | None
) -> str:
    """Synthesize a definitive answer strictly grounded in the policy section."""
    clean_clause = best_clause.strip() if best_clause else section.content.strip()
    clean_clause = re.sub(r"\*+", "", clean_clause).strip()

    # If the matched clause is an introductory header ending with ':',
    # provide full section content
    if clean_clause.endswith(":") and section.content:
        clean_clause = re.sub(r"\*+", "", section.content).strip()

    return (
        f"According to {section.document_id} version {section.version} "
        f"(Section {section.section_number}: {section.section_title}): {clean_clause}"
    )


def create_default_policy_engine(
    policy_path: str | Path | None = None,
) -> PolicyEngine:
    """Instantiate and optionally populate the default policy engine."""
    engine = PolicyEngine()
    if policy_path is not None:
        engine.ingest_file(policy_path)
    else:
        bundled_sop = Path(__file__).parent / "policies" / "sop-hr-time-and-leave.md"
        if bundled_sop.is_file():
            engine.ingest_file(bundled_sop)
    return engine
