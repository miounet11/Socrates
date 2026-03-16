"""Pipeline orchestration helpers and local review heuristics."""

from __future__ import annotations

import re
from collections import Counter

from socrates.exceptions import ProviderError
from socrates.models import (
    ContentDraft,
    ContentFrame,
    ContentOutline,
    ContentRequest,
    ReviewFinding,
    ReviewReport,
    ReviewSeverity,
)
from socrates.prompts import (
    build_direct_draft_messages,
    build_draft_messages,
    build_frame_messages,
    build_outline_messages,
    build_review_messages,
)
from socrates.providers.base import LLMProvider

AI_TONE_PATTERNS = [
    "in today's fast-paced",
    "game-changing",
    "revolutionary",
    "unlock the power of",
    "delve into",
    "in conclusion",
]

UNSUPPORTED_CLAIM_PATTERNS = [
    r"\bguarantee(?:d|s)?\b",
    r"\balways\b",
    r"\bnever\b",
    r"\bbest-in-class\b",
    r"\bworld-class\b",
]


def generate_frame(
    provider: LLMProvider,
    request: ContentRequest,
    *,
    model: str,
    temperature: float,
) -> ContentFrame:
    return provider.structured_completion(
        messages=build_frame_messages(request),
        response_model=ContentFrame,
        model=model,
        temperature=temperature,
    )


def generate_outline(
    provider: LLMProvider,
    request: ContentRequest,
    frame: ContentFrame,
    *,
    model: str,
    temperature: float,
) -> ContentOutline:
    return provider.structured_completion(
        messages=build_outline_messages(request, frame),
        response_model=ContentOutline,
        model=model,
        temperature=temperature,
    )


def generate_draft(
    provider: LLMProvider,
    request: ContentRequest,
    *,
    model: str,
    temperature: float,
    frame: ContentFrame | None = None,
    outline: ContentOutline | None = None,
    direct: bool = False,
) -> ContentDraft:
    messages = build_direct_draft_messages(request) if direct else build_draft_messages(
        request,
        frame,
        outline,
    )
    return provider.structured_completion(
        messages=messages,
        response_model=ContentDraft,
        model=model,
        temperature=temperature,
    )


def generate_review(
    provider: LLMProvider,
    request: ContentRequest,
    draft: ContentDraft,
    *,
    model: str,
    temperature: float,
    frame: ContentFrame | None = None,
) -> ReviewReport:
    heuristics = heuristic_review(draft)
    try:
        model_report = provider.structured_completion(
            messages=build_review_messages(request, draft, frame, heuristics),
            response_model=ReviewReport,
            model=model,
            temperature=temperature,
        )
    except ProviderError:
        return heuristics.model_copy(
            update={
                "summary": "Model review was unavailable; returning heuristic review only.",
            }
        )
    return merge_reviews(model_report, heuristics)


def heuristic_review(draft: ContentDraft) -> ReviewReport:
    findings: list[ReviewFinding] = []
    unsupported_claims: list[str] = []
    repetition_flags: list[str] = []
    ai_tone_flags: list[str] = []
    lowered = draft.body.lower()

    for phrase in AI_TONE_PATTERNS:
        if phrase in lowered:
            ai_tone_flags.append(phrase)
            findings.append(
                ReviewFinding(
                    severity=ReviewSeverity.WARNING,
                    category="ai_tone",
                    evidence=phrase,
                    recommendation="Replace stock phrasing with audience-specific wording.",
                )
            )

    for pattern in UNSUPPORTED_CLAIM_PATTERNS:
        for match in re.finditer(pattern, draft.body, flags=re.IGNORECASE):
            claim = match.group(0)
            unsupported_claims.append(claim)
            findings.append(
                ReviewFinding(
                    severity=ReviewSeverity.WARNING,
                    category="unsupported_claim",
                    evidence=claim,
                    recommendation="Either support the claim with evidence or soften it.",
                )
            )

    paragraphs = [paragraph.strip() for paragraph in draft.body.split("\n\n") if paragraph.strip()]
    normalized_paragraphs = [re.sub(r"\s+", " ", paragraph.lower()) for paragraph in paragraphs]
    repeated_paragraphs = [
        paragraph for paragraph, count in Counter(normalized_paragraphs).items() if count > 1
    ]
    for paragraph in repeated_paragraphs:
        excerpt = paragraph[:120]
        repetition_flags.append(excerpt)
        findings.append(
            ReviewFinding(
                severity=ReviewSeverity.WARNING,
                category="repetition",
                evidence=excerpt,
                recommendation="Cut or combine repeated paragraphs.",
            )
        )

    score = 92
    score -= 8 * len(unsupported_claims)
    score -= 6 * len(repetition_flags)
    score -= 5 * len(ai_tone_flags)
    score = max(0, min(100, score))

    if findings:
        summary = "Heuristic review found issues that should be tightened before publishing."
    else:
        summary = "Heuristic review did not find obvious publishability issues."

    passes = not any(
        finding.severity == ReviewSeverity.ERROR for finding in findings
    ) and score >= 75
    return ReviewReport(
        publishability_score=score,
        summary=summary,
        findings=findings,
        unsupported_claims=unsupported_claims,
        repetition_flags=repetition_flags,
        ai_tone_flags=ai_tone_flags,
        passes=passes,
    )


def merge_reviews(primary: ReviewReport, secondary: ReviewReport) -> ReviewReport:
    merged_findings = primary.findings[:]
    existing = {(finding.category, finding.evidence) for finding in merged_findings}
    for finding in secondary.findings:
        key = (finding.category, finding.evidence)
        if key not in existing:
            merged_findings.append(finding)
            existing.add(key)

    unsupported_claims = list(
        dict.fromkeys([*primary.unsupported_claims, *secondary.unsupported_claims])
    )
    repetition_flags = list(
        dict.fromkeys([*primary.repetition_flags, *secondary.repetition_flags])
    )
    ai_tone_flags = list(dict.fromkeys([*primary.ai_tone_flags, *secondary.ai_tone_flags]))
    combined_score = max(
        0,
        min(100, round((primary.publishability_score + secondary.publishability_score) / 2)),
    )
    passes = primary.passes and secondary.passes and combined_score >= 75
    return ReviewReport(
        publishability_score=combined_score,
        summary=primary.summary,
        findings=merged_findings,
        unsupported_claims=unsupported_claims,
        repetition_flags=repetition_flags,
        ai_tone_flags=ai_tone_flags,
        passes=passes,
    )
