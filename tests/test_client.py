from socrates.client import Socrates
from socrates.config import SocratesConfig
from socrates.models import GenerationMode
from tests.conftest import StubProvider


def test_generate_guided_returns_frame_and_draft(content_request) -> None:
    provider = StubProvider(
        [
            {
                "audience_pains": ["They lead with features, not pains."],
                "desired_takeaway": "Position around business friction.",
                "persuasion_triggers": ["Credible examples"],
                "credibility_requirements": ["Concrete examples"],
                "tone_rules": ["Be specific"],
                "anti_patterns": ["Do not say game-changing"],
                "core_angle": "Positioning should start with operational pain.",
            },
            {
                "title": "AI product messaging fails when it starts with capability",
                "body": (
                    "Most teams describe what the model can do before they explain why "
                    "the buyer should care."
                ),
                "summary": "A publishable draft",
                "cta": "Audit your current homepage copy.",
                "metadata": {},
            },
        ]
    )
    client = Socrates(provider, config=SocratesConfig())

    result = client.generate(content_request, mode=GenerationMode.GUIDED)

    assert result.mode == GenerationMode.GUIDED
    assert result.frame is not None
    assert result.outline is None
    assert result.review is None
    assert result.draft.title.startswith("AI product messaging")
    assert len(provider.calls) == 2


def test_generate_full_merges_heuristic_review_flags(content_request) -> None:
    provider = StubProvider(
        [
            {
                "audience_pains": ["They lead with features, not pains."],
                "desired_takeaway": "Position around business friction.",
                "persuasion_triggers": ["Credible examples"],
                "credibility_requirements": ["Concrete examples"],
                "tone_rules": ["Be specific"],
                "anti_patterns": ["Do not say game-changing"],
                "core_angle": "Positioning should start with operational pain.",
            },
            {
                "opening_hook": "Most AI messaging loses the buyer in the first sentence.",
                "thesis": "Start with operational pain, not model capability.",
                "sections": [
                    {
                        "heading": "Lead with pain",
                        "purpose": "Make the buyer feel seen",
                        "key_points": ["Capability-first copy is too abstract"],
                        "evidence_needs": ["Homepage example"],
                        "cta_hint": "Invite a copy audit",
                    }
                ],
                "closing_cta": "Book a messaging review",
                "platform_adaptations": ["Use short subheads"],
            },
            {
                "title": "Capability-first messaging keeps buyers cold",
                "body": (
                    "This game-changing approach will always transform your funnel.\n\n"
                    "This game-changing approach will always transform your funnel."
                ),
                "summary": "A publishable draft",
                "cta": "Book a messaging review.",
                "metadata": {},
            },
            {
                "publishability_score": 82,
                "summary": "Needs claim tightening.",
                "findings": [],
                "unsupported_claims": [],
                "repetition_flags": [],
                "ai_tone_flags": [],
                "passes": True,
            },
        ]
    )
    client = Socrates(provider, config=SocratesConfig())

    result = client.generate(content_request, mode=GenerationMode.FULL)

    assert result.outline is not None
    assert result.review is not None
    assert "game-changing" in result.review.ai_tone_flags
    assert any(flag == "always" for flag in result.review.unsupported_claims)
    assert result.review.passes is False
