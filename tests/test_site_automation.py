from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from socrates.client import Socrates
from socrates.config import SocratesConfig
from socrates.exceptions import ProviderError
from socrates.providers.base import LLMProvider, Message, T
from socrates.site_automation import (
    GenerationSummary,
    SiteAutomationState,
    build_topic_inventory,
    generate_daily_site_content,
    generate_site_article,
    load_state,
    select_next_topics,
)
from tests.conftest import StubProvider


def _english_article() -> dict[str, object]:
    return {
        "meta_description": (
            "A practical guide to content briefs for AI and B2B teams that need clearer"
            " standards, better structure, and publishable drafts."
        ),
        "summary": "A content brief becomes useful when it makes the editorial standard explicit.",
        "intro": [
            (
                "Most content briefs fail because they summarize a topic without defining "
                "the standard for success."
            ),
            (
                "A strong brief tells a writer what must be persuasive, what evidence is "
                "required, and what language should be avoided."
            ),
        ],
        "sections": [
            {
                "heading": "Start with the decision behind the page",
                "paragraphs": [
                    (
                        "The brief should identify the business decision the page is trying "
                        "to influence."
                    ),
                    (
                        "That keeps the draft focused on audience friction instead of "
                        "generic explanation."
                    ),
                ],
                "bullets": [
                    "State the intended reader",
                    "Name the operational pain",
                    "Define the desired takeaway",
                ],
            },
            {
                "heading": "Make credibility requirements explicit",
                "paragraphs": [
                    (
                        "Writers need to know what kind of proof or examples are expected "
                        "before drafting starts."
                    ),
                    "This is the fastest way to avoid polished copy that still feels empty.",
                ],
                "bullets": [
                    "Require grounded examples",
                    "Note unsupported claim patterns",
                ],
            },
            {
                "heading": "Translate strategy into structure",
                "paragraphs": [
                    "A useful brief suggests how the argument should unfold across the page.",
                    "That gives the draft a stronger rhythm and reduces repetitive sections.",
                ],
                "bullets": [
                    "Define the opening hook",
                    "Call out priority sections",
                ],
            },
            {
                "heading": "Review for publishability before shipping",
                "paragraphs": [
                    (
                        "The brief should make it easy to review for clarity, tone, and "
                        "unsupported certainty."
                    ),
                    "Teams that define review cues early produce cleaner pages faster.",
                ],
                "bullets": [
                    "Check for filler phrasing",
                    "Verify the CTA fits the audience stage",
                ],
            },
        ],
        "faq": [
            {
                "question": "When is a content brief worth the extra effort?",
                "answer": (
                    "It matters most when the page is tied to positioning, pipeline "
                    "influence, or long-term search traffic."
                ),
            },
            {
                "question": "What makes a brief weak?",
                "answer": (
                    "A weak brief stays abstract and never defines the signals that make "
                    "the final page credible."
                ),
            },
            {
                "question": "Should the brief include a CTA?",
                "answer": (
                    "Yes, but it should match the reader's stage and feel like a logical "
                    "next step."
                ),
            },
        ],
        "cta_heading": "Turn your standards into a reusable workflow",
        "cta_body": (
            "Use the docs to model briefs, frames, and review steps as part of a "
            "repeatable content system."
        ),
        "cta_label": "Read the docs",
    }


def _chinese_article() -> dict[str, object]:
    return {
        "meta_description": (
            "面向 AI 与 B2B 团队的内容 brief 指南, 帮你建立更清晰的标准、结构与发布质量。"
        ),
        "summary": "真正有用的内容 brief, 不是描述主题, 而是先把标准写清楚。",
        "intro": [
            "很多 brief 看起来完整, 但没有说明这篇内容为什么值得读, 结果写作只能回到套话。",
            "好的 brief 会提前定义受众痛点、可信度要求、结构节奏和必须避免的表达。",
        ],
        "sections": [
            {
                "heading": "先写清楚页面要推动什么判断",
                "paragraphs": [
                    "brief 应该先说明页面希望影响读者做出什么判断或下一步动作。",
                    "这会让整篇内容围绕真实业务问题展开, 而不是堆叠常识。",
                ],
                "bullets": ["说明目标读者", "指出关键痛点", "写明希望带走的判断"],
            },
            {
                "heading": "把可信度要求提前说清楚",
                "paragraphs": [
                    "如果没有提前说明需要什么例子和证据, 草稿很容易写得工整却没有说服力。",
                    "团队越早定义可信度信号, 后续审稿越稳定。",
                ],
                "bullets": ["要求具体例子", "标出不能夸大的说法"],
            },
            {
                "heading": "把策略翻译成结构",
                "paragraphs": [
                    "brief 不一定要写成完整大纲, 但至少要说明论证顺序和重点段落。",
                    "这样写作时更容易保持节奏, 也能减少重复内容。",
                ],
                "bullets": ["定义开头切入点", "说明重点部分顺序"],
            },
            {
                "heading": "发布前按标准复核",
                "paragraphs": [
                    "brief 还应该提前告诉团队, 审稿时重点检查哪些风险。",
                    "这会让最终页面更具体, 也更接近真正可发布的质量。",
                ],
                "bullets": ["检查空话", "检查 CTA 是否匹配读者阶段"],
            },
        ],
        "faq": [
            {
                "question": "什么情况下值得认真写 brief?",
                "answer": "当页面关系到品牌表达、转化路径或长期搜索流量时, brief 很值得投入。",
            },
            {
                "question": "brief 最常见的问题是什么?",
                "answer": "最常见的问题是只有主题, 没有标准, 导致写作者只能靠猜。",
            },
            {
                "question": "brief 里要不要写 CTA?",
                "answer": "要, 但 CTA 应该和读者所处阶段匹配, 不能显得生硬。",
            },
        ],
        "cta_heading": "把标准前置成稳定流程",
        "cta_body": "查看文档, 用 frame、outline 和 review 组成可复用的内容系统。",
        "cta_label": "阅读文档",
    }


def _review_payload() -> dict[str, object]:
    return {
        "publishability_score": 90,
        "summary": "Publishable with solid specificity and structure.",
        "findings": [],
        "unsupported_claims": [],
        "repetition_flags": [],
        "ai_tone_flags": [],
        "passes": True,
    }


class FailingProvider(LLMProvider):
    def structured_completion(
        self,
        *,
        messages: list[Message],
        response_model: type[T],
        model: str,
        temperature: float,
    ) -> T:
        raise ProviderError("simulated provider failure")


def test_build_topic_inventory_is_unique() -> None:
    seeds = build_topic_inventory()

    assert seeds
    assert len({seed.key for seed in seeds}) == len(seeds)
    assert len({seed.slug for seed in seeds}) == len(seeds)


def test_select_next_topics_skips_published_seeds() -> None:
    seeds = build_topic_inventory()
    state = SiteAutomationState(published_seed_keys=[seeds[0].key])

    selected = select_next_topics(state, count=2)

    assert len(selected) == 2
    assert selected[0].key == seeds[1].key
    assert all(seed.key != seeds[0].key for seed in selected)


def test_generate_daily_site_content_writes_pages_indexes_and_sitemap(tmp_path: Path) -> None:
    publish_dir = tmp_path / "publish"
    state_path = tmp_path / "state" / "site_automation_state.json"
    provider = StubProvider(
        [
            _english_article(),
            _review_payload(),
            _chinese_article(),
            _review_payload(),
        ]
    )
    client = Socrates(provider, config=SocratesConfig())

    summary = generate_daily_site_content(
        client,
        publish_dir=publish_dir,
        state_path=state_path,
        topics_per_run=1,
        locales=("en-US", "zh-CN"),
        now=datetime(2026, 3, 16, 8, 0, tzinfo=UTC),
    )

    assert summary.generated_seed_keys == ["content_brief:guide"]
    assert summary.skipped_seed_keys == []
    assert sorted(summary.generated_pages) == [
        "library/content_brief-guide.html",
        "zh/library/content_brief-guide.html",
    ]

    en_article = publish_dir / "library" / "content_brief-guide.html"
    zh_article = publish_dir / "zh" / "library" / "content_brief-guide.html"
    en_index = publish_dir / "library" / "index.html"
    zh_index = publish_dir / "zh" / "library" / "index.html"
    sitemap = publish_dir / "sitemap.xml"

    assert en_article.exists()
    assert zh_article.exists()
    assert en_index.exists()
    assert zh_index.exists()
    assert sitemap.exists()

    en_html = en_article.read_text(encoding="utf-8")
    zh_html = zh_article.read_text(encoding="utf-8")

    assert "Socrates Library" in en_html
    assert 'lang-link lang-link-active" href="./content_brief-guide.html">EN<' in en_html
    assert 'href="../../zh/library/content_brief-guide.html">中文<' in en_html
    assert "Socrates 资源库" in zh_html
    assert 'href="../../library/content_brief-guide.html">EN<' in zh_html
    assert "content_brief-guide.html" in en_index.read_text(encoding="utf-8")
    assert "https://ixinxiang.xyz/library/" in sitemap.read_text(encoding="utf-8")

    state = load_state(state_path)
    assert state.published_seed_keys == ["content_brief:guide"]
    assert len(state.articles) == 2


def test_generation_summary_model_defaults() -> None:
    summary = GenerationSummary()

    assert summary.generated_seed_keys == []
    assert summary.generated_pages == []
    assert summary.skipped_seed_keys == []


def test_generate_site_article_uses_fallback_when_provider_fails() -> None:
    client = Socrates(FailingProvider(), config=SocratesConfig())
    seed = build_topic_inventory()[2]

    article, score = generate_site_article(client, seed, locale="en-US")

    assert score >= 75
    assert article.meta_description
    assert len(article.sections) == 4
    assert len(article.faq) == 3
