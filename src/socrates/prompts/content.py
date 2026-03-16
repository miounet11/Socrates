"""Prompt templates for each generation stage."""

from __future__ import annotations

from socrates.models import (
    ContentDraft,
    ContentFrame,
    ContentOutline,
    ContentRequest,
    ReviewReport,
)

Message = dict[str, str]

FRAME_SYSTEM_PROMPT = """
You are Socrates, a senior content strategist for publishable work.
Your job is to build execution-grade content rubrics, not generic advice.
Every item must be specific to the audience, platform, and buying context.
Do not explain your reasoning. Produce only the structured output.
""".strip()

OUTLINE_SYSTEM_PROMPT = """
You are Socrates, a strategic editor.
Turn the approved content frame into a publishable outline with concrete sequencing.
Avoid filler sections and avoid headings that could fit any topic.
Do not explain your reasoning. Produce only the structured output.
""".strip()

DRAFT_SYSTEM_PROMPT = """
You are Socrates, a senior B2B content writer.
Write publishable content that follows the supplied brief exactly.
Do not expose internal planning, rubrics, or chain-of-thought.
Prefer concrete claims, credible phrasing, and audience-aware pacing over hype.
Produce only the structured output.
""".strip()

REVIEW_SYSTEM_PROMPT = """
You are Socrates, an exacting editorial reviewer.
Audit the draft for publishability, unsupported claims, repetition, and AI-flavored phrasing.
Prefer sharp, actionable findings over vague criticism.
Produce only the structured output.
""".strip()


def _request_payload(request: ContentRequest) -> str:
    return request.model_dump_json(indent=2, exclude_none=True)


def _frame_payload(frame: ContentFrame) -> str:
    return frame.model_dump_json(indent=2, exclude_none=True)


def _outline_payload(outline: ContentOutline) -> str:
    return outline.model_dump_json(indent=2, exclude_none=True)


def _draft_payload(draft: ContentDraft) -> str:
    return draft.model_dump_json(indent=2, exclude_none=True)


def _review_payload(review: ReviewReport) -> str:
    return review.model_dump_json(indent=2, exclude_none=True)


def build_frame_messages(request: ContentRequest) -> list[Message]:
    return [
        {"role": "system", "content": FRAME_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Create a content frame for the following request.\n"
                "Requirements:\n"
                "- Audience pains must name specific frictions, objections, or unmet needs.\n"
                "- Persuasion triggers must be concrete buying or trust signals.\n"
                "- Credibility requirements must specify what evidence or specificity "
                "the draft needs.\n"
                "- Tone rules must be directly usable during drafting.\n"
                "- Anti-patterns must describe phrases, structures, or habits to avoid.\n"
                "- Core angle must be a differentiated thesis, not a topic restatement.\n\n"
                f"Request:\n{_request_payload(request)}"
            ),
        },
    ]


def build_outline_messages(request: ContentRequest, frame: ContentFrame) -> list[Message]:
    return [
        {"role": "system", "content": OUTLINE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Build a content outline from the request and approved frame.\n"
                "Requirements:\n"
                "- The opening hook must create immediate relevance for the named audience.\n"
                "- Section purposes must be specific enough to guide drafting.\n"
                "- Evidence needs must name the kind of proof needed, not just say "
                "'add examples'.\n"
                "- Platform adaptations must mention execution details for the "
                "selected platform.\n\n"
                f"Request:\n{_request_payload(request)}\n\n"
                f"Frame:\n{_frame_payload(frame)}"
            ),
        },
    ]


def build_draft_messages(
    request: ContentRequest,
    frame: ContentFrame | None = None,
    outline: ContentOutline | None = None,
) -> list[Message]:
    mode_hint = "full" if outline else "guided"
    outline_blob = _outline_payload(outline) if outline else "null"
    frame_blob = _frame_payload(frame) if frame else "null"
    return [
        {"role": "system", "content": DRAFT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Write a {mode_hint}-mode draft.\n"
                "Requirements:\n"
                "- Keep the output ready for publication on the requested platform.\n"
                "- Use markdown in `body` when structure helps readability.\n"
                "- Keep the body aligned to the frame; do not drift into generic "
                "thought leadership.\n"
                "- Do not introduce unsupported certainty or invented evidence.\n"
                "- Do not mention the frame, outline, or internal steps.\n"
                "- If `include_cta` is false, keep `cta` null.\n\n"
                f"Request:\n{_request_payload(request)}\n\n"
                f"Frame:\n{frame_blob}\n\n"
                f"Outline:\n{outline_blob}"
            ),
        },
    ]


def build_direct_draft_messages(request: ContentRequest) -> list[Message]:
    return [
        {"role": "system", "content": DRAFT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Handle this as a direct, lightweight content task.\n"
                "Requirements:\n"
                "- Produce the most useful final output without exposing internal planning.\n"
                "- Keep it concise when the request implies a lightweight transform.\n"
                "- Return a credible, publishable result rather than generic filler.\n\n"
                f"Request:\n{_request_payload(request)}"
            ),
        },
    ]


def build_review_messages(
    request: ContentRequest,
    draft: ContentDraft,
    frame: ContentFrame | None = None,
    heuristics: ReviewReport | None = None,
) -> list[Message]:
    heuristic_blob = _review_payload(heuristics) if heuristics else "null"
    frame_blob = _frame_payload(frame) if frame else "null"
    return [
        {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Review the draft for publishability.\n"
                "Requirements:\n"
                "- Flag unsupported claims, repeated ideas, AI-sounding phrases, and "
                "audience mismatch.\n"
                "- A finding must cite the exact issue in the draft, not generic advice.\n"
                "- `passes` should be true only if the draft could be published with "
                "minor or no edits.\n"
                "- `publishability_score` should reflect both structure and credibility.\n\n"
                f"Request:\n{_request_payload(request)}\n\n"
                f"Frame:\n{frame_blob}\n\n"
                f"Draft:\n{_draft_payload(draft)}\n\n"
                f"Heuristic notes:\n{heuristic_blob}"
            ),
        },
    ]
