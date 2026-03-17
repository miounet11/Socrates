"""Automated evergreen site-content generation for the public website."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from html import escape
from pathlib import Path
from textwrap import dedent

from pydantic import BaseModel, ConfigDict, Field

from socrates.client import Socrates
from socrates.exceptions import ProviderError
from socrates.models import ContentDraft, ContentRequest, ReviewReport

SITE_DOMAIN = "https://ixinxiang.xyz"
DEFAULT_STATE_PATH = Path("content/site_automation_state.json")
DEFAULT_TOPICS_PER_RUN = 2
DEFAULT_LOCALES = ("en-US", "zh-CN")

STATIC_URLS = [
    "/",
    "/product.html",
    "/use-cases.html",
    "/docs.html",
    "/faq.html",
    "/library/",
    "/zh/",
    "/zh/product.html",
    "/zh/use-cases.html",
    "/zh/docs.html",
    "/zh/faq.html",
    "/zh/library/",
]

AI_SEO_PHRASES = [
    "ultimate guide",
    "best tool",
    "guaranteed",
    "always works",
    "never fails",
    "game-changing",
    "revolutionary",
]

SITE_ARTICLE_SYSTEM_PROMPT = dedent(
    """
    You are Socrates, a senior editorial strategist for evergreen website content.
    You write original, useful, non-deceptive pages about AI content strategy,
    B2B messaging, content operations, and structured generation workflows.

    Hard requirements:
    - Produce educational, practical content only.
    - Do not plagiarize, imitate, or closely paraphrase other websites.
    - Do not fabricate statistics, case studies, rankings, or customer evidence.
    - Do not make legal, medical, financial, or safety claims.
    - Do not attack competitors or imply wrongdoing.
    - Avoid clickbait, thin affiliate-style copy, or keyword stuffing.
    - Keep the page specific to the supplied title, audience, and search intent.
    - The output must feel publishable for a professional product website.
    - Return only the structured JSON response.
    """
).strip()


@dataclass(frozen=True)
class TopicFamily:
    """A reusable evergreen content family."""

    key: str
    subject_en: str
    subject_zh: str
    audience_en: str
    audience_zh: str
    cluster_en: str
    cluster_zh: str
    keyword_en: str
    keyword_zh: str
    secondary_keywords_en: tuple[str, ...]
    secondary_keywords_zh: tuple[str, ...]


@dataclass(frozen=True)
class TopicPattern:
    """A reusable title and intent pattern."""

    key: str
    title_en: str
    title_zh: str
    intent_en: str
    intent_zh: str
    angle_en: str
    angle_zh: str


@dataclass(frozen=True)
class TopicSeed:
    """A fully resolved topic seed selected for generation."""

    key: str
    slug: str
    family_key: str
    pattern_key: str
    title_en: str
    title_zh: str
    audience_en: str
    audience_zh: str
    cluster_en: str
    cluster_zh: str
    keyword_en: str
    keyword_zh: str
    secondary_keywords_en: tuple[str, ...]
    secondary_keywords_zh: tuple[str, ...]
    intent_en: str
    intent_zh: str
    angle_en: str
    angle_zh: str


class SiteArticleSection(BaseModel):
    """A section rendered on a generated evergreen page."""

    model_config = ConfigDict(extra="forbid")

    heading: str
    paragraphs: list[str] = Field(min_length=2, max_length=4)
    bullets: list[str] = Field(default_factory=list, max_length=6)


class SiteArticleFaq(BaseModel):
    """FAQ entry appended to the end of the page."""

    model_config = ConfigDict(extra="forbid")

    question: str
    answer: str


class SiteArticlePayload(BaseModel):
    """Structured content payload used to render a public resource page."""

    model_config = ConfigDict(extra="forbid")

    meta_description: str
    summary: str
    intro: list[str] = Field(min_length=2, max_length=3)
    sections: list[SiteArticleSection] = Field(min_length=4, max_length=6)
    faq: list[SiteArticleFaq] = Field(min_length=3, max_length=4)
    cta_heading: str
    cta_body: str
    cta_label: str


class PublishedArticleRecord(BaseModel):
    """Metadata stored for generated resource pages."""

    model_config = ConfigDict(extra="forbid")

    seed_key: str
    slug: str
    locale: str
    title: str
    summary: str
    meta_description: str
    path: str
    url: str
    cluster: str
    published_at: str
    review_score: int
    primary_keyword: str


class SiteAutomationState(BaseModel):
    """Persistent state that prevents duplicate topic publication."""

    model_config = ConfigDict(extra="forbid")

    published_seed_keys: list[str] = Field(default_factory=list)
    articles: list[PublishedArticleRecord] = Field(default_factory=list)


class GeneratedPageBundle(BaseModel):
    """Write-ready page bundle for a single locale."""

    model_config = ConfigDict(extra="forbid")

    locale: str
    output_path: str
    html: str
    record: PublishedArticleRecord


class GenerationSummary(BaseModel):
    """High-level result for one generator run."""

    model_config = ConfigDict(extra="forbid")

    generated_seed_keys: list[str] = Field(default_factory=list)
    generated_pages: list[str] = Field(default_factory=list)
    skipped_seed_keys: list[str] = Field(default_factory=list)


TOPIC_FAMILIES = (
    TopicFamily(
        key="content_brief",
        subject_en="content brief",
        subject_zh="内容 brief",
        audience_en="content operators and product marketers",
        audience_zh="内容运营和产品营销团队",
        cluster_en="Content Operations",
        cluster_zh="内容运营",
        keyword_en="content brief",
        keyword_zh="内容 brief",
        secondary_keywords_en=("content workflow", "AI content system", "brief template"),
        secondary_keywords_zh=("内容工作流", "AI 内容系统", "brief 模板"),
    ),
    TopicFamily(
        key="content_frame",
        subject_en="content frame",
        subject_zh="内容 frame",
        audience_en="B2B content teams",
        audience_zh="B2B 内容团队",
        cluster_en="Strategy Layer",
        cluster_zh="策略层",
        keyword_en="content frame",
        keyword_zh="内容 frame",
        secondary_keywords_en=("rubric-guided generation", "content strategy", "audience fit"),
        secondary_keywords_zh=("判据驱动生成", "内容策略", "受众匹配"),
    ),
    TopicFamily(
        key="content_outline",
        subject_en="content outline workflow",
        subject_zh="内容大纲工作流",
        audience_en="teams publishing long-form B2B content",
        audience_zh="发布 B2B 长文的团队",
        cluster_en="Structure",
        cluster_zh="结构设计",
        keyword_en="content outline workflow",
        keyword_zh="内容大纲工作流",
        secondary_keywords_en=("long-form content", "section sequencing", "draft structure"),
        secondary_keywords_zh=("长文内容", "段落顺序", "草稿结构"),
    ),
    TopicFamily(
        key="publishability_review",
        subject_en="publishability review",
        subject_zh="发布前审稿",
        audience_en="editorial and brand teams",
        audience_zh="编辑团队和品牌团队",
        cluster_en="Review",
        cluster_zh="审稿",
        keyword_en="publishability review",
        keyword_zh="发布前审稿",
        secondary_keywords_en=("AI content QA", "editorial review", "content quality control"),
        secondary_keywords_zh=("AI 内容质检", "编辑审稿", "内容质量控制"),
    ),
    TopicFamily(
        key="value_proposition",
        subject_en="value proposition messaging",
        subject_zh="价值主张文案",
        audience_en="B2B SaaS marketers",
        audience_zh="B2B SaaS 营销团队",
        cluster_en="Messaging",
        cluster_zh="信息表达",
        keyword_en="value proposition messaging",
        keyword_zh="价值主张文案",
        secondary_keywords_en=("landing page messaging", "buyer pain", "positioning copy"),
        secondary_keywords_zh=("落地页文案", "买家痛点", "定位文案"),
    ),
    TopicFamily(
        key="brand_narrative",
        subject_en="brand narrative",
        subject_zh="品牌叙事",
        audience_en="founders and messaging leads",
        audience_zh="创始人和品牌负责人",
        cluster_en="Brand Strategy",
        cluster_zh="品牌策略",
        keyword_en="brand narrative",
        keyword_zh="品牌叙事",
        secondary_keywords_en=("positioning", "brand messaging", "category story"),
        secondary_keywords_zh=("品牌定位", "品牌表达", "类别叙事"),
    ),
    TopicFamily(
        key="content_calendar",
        subject_en="content calendar planning",
        subject_zh="内容日历规划",
        audience_en="content and demand generation teams",
        audience_zh="内容团队和需求增长团队",
        cluster_en="Planning",
        cluster_zh="规划",
        keyword_en="content calendar planning",
        keyword_zh="内容日历规划",
        secondary_keywords_en=("editorial planning", "campaign calendar", "content operations"),
        secondary_keywords_zh=("编辑规划", "活动日历", "内容运营"),
    ),
    TopicFamily(
        key="linkedin_workflow",
        subject_en="LinkedIn content workflow",
        subject_zh="LinkedIn 内容工作流",
        audience_en="founders and GTM teams",
        audience_zh="创始人和 GTM 团队",
        cluster_en="Social Publishing",
        cluster_zh="社媒发布",
        keyword_en="LinkedIn content workflow",
        keyword_zh="LinkedIn 内容工作流",
        secondary_keywords_en=("LinkedIn post structure", "founder content", "B2B social content"),
        secondary_keywords_zh=("LinkedIn 长帖结构", "创始人内容", "B2B 社媒内容"),
    ),
    TopicFamily(
        key="industry_analysis",
        subject_en="industry analysis workflow",
        subject_zh="行业分析工作流",
        audience_en="category marketers and product teams",
        audience_zh="品类营销团队和产品团队",
        cluster_en="Analysis",
        cluster_zh="分析",
        keyword_en="industry analysis workflow",
        keyword_zh="行业分析工作流",
        secondary_keywords_en=("thought leadership", "market analysis", "structured argument"),
        secondary_keywords_zh=("行业洞察", "市场分析", "结构化论证"),
    ),
    TopicFamily(
        key="multilingual_content",
        subject_en="multilingual content operations",
        subject_zh="多语言内容运营",
        audience_en="global marketing teams",
        audience_zh="全球化营销团队",
        cluster_en="Localization",
        cluster_zh="本地化",
        keyword_en="multilingual content operations",
        keyword_zh="多语言内容运营",
        secondary_keywords_en=("content localization", "bilingual SEO", "global publishing"),
        secondary_keywords_zh=("内容本地化", "双语 SEO", "全球发布"),
    ),
    TopicFamily(
        key="editorial_governance",
        subject_en="editorial governance",
        subject_zh="内容治理",
        audience_en="brand and content leaders",
        audience_zh="品牌和内容负责人",
        cluster_en="Governance",
        cluster_zh="治理",
        keyword_en="editorial governance",
        keyword_zh="内容治理",
        secondary_keywords_en=("content standards", "review policy", "quality controls"),
        secondary_keywords_zh=("内容标准", "审稿机制", "质量控制"),
    ),
    TopicFamily(
        key="programmatic_seo",
        subject_en="programmatic SEO for content systems",
        subject_zh="内容系统的程序化 SEO",
        audience_en="content operators and SEO leads",
        audience_zh="内容运营和 SEO 负责人",
        cluster_en="SEO Systems",
        cluster_zh="SEO 系统",
        keyword_en="programmatic SEO for content systems",
        keyword_zh="内容系统的程序化 SEO",
        secondary_keywords_en=("topic clusters", "evergreen traffic", "search intent"),
        secondary_keywords_zh=("主题集群", "长期流量", "搜索意图"),
    ),
)

TOPIC_PATTERNS = (
    TopicPattern(
        key="guide",
        title_en="What is {topic}? A practical guide for {audience}",
        title_zh="{topic} 是什么? 给 {audience} 的实用指南",
        intent_en="Informational guide for readers trying to understand the concept clearly.",
        intent_zh="帮助读者快速理解核心概念和使用边界的说明型页面。",
        angle_en=(
            "Define the concept clearly, explain why it matters, and show how teams use it."
        ),
        angle_zh="先定义概念, 再解释为什么重要, 最后说明团队如何真正使用它。",
    ),
    TopicPattern(
        key="checklist",
        title_en="{topic} checklist for teams that need publishable AI content",
        title_zh="面向可发布 AI 内容团队的 {topic} 检查清单",
        intent_en="Checklist intent for teams looking for an operational standard.",
        intent_zh="面向执行团队的检查清单型搜索意图。",
        angle_en=(
            "Turn the topic into a practical checklist with clear checkpoints and review cues."
        ),
        angle_zh="把主题拆成真正可执行的检查项和复核节点。",
    ),
    TopicPattern(
        key="template",
        title_en="{topic} template: a reusable starting point for {audience}",
        title_zh="{topic} 模板: 给 {audience} 的可复用起点",
        intent_en="Template intent for readers who want to start with a usable structure.",
        intent_zh="面向希望直接拿到可用结构的模板型搜索意图。",
        angle_en="Show a repeatable structure, explain each field, and note common mistakes.",
        angle_zh="给出可复用结构, 说明每个字段的作用, 并提醒常见误区。",
    ),
    TopicPattern(
        key="mistakes",
        title_en="{topic} mistakes that make AI content sound generic",
        title_zh="最容易让 AI 内容变空泛的 {topic} 误区",
        intent_en="Problem-solving intent for teams trying to avoid weak content.",
        intent_zh="面向想避免空洞内容的纠错型搜索意图。",
        angle_en="Name the highest-cost mistakes, explain why they happen, and show cleaner fixes.",
        angle_zh="指出代价最高的误区, 解释原因, 并给出更稳的替代做法。",
    ),
    TopicPattern(
        key="playbook",
        title_en="{topic} playbook for teams that publish high-stakes B2B content",
        title_zh="面向高价值 B2B 内容团队的 {topic} 操作手册",
        intent_en="Operational playbook intent for teams building repeatable workflows.",
        intent_zh="面向建立可复用流程团队的操作手册型搜索意图。",
        angle_en="Describe a workable process, role ownership, sequencing, and review points.",
        angle_zh="写清楚流程顺序、角色分工、执行节奏和审稿节点。",
    ),
    TopicPattern(
        key="examples",
        title_en="{topic} examples for teams building structured content systems",
        title_zh="给结构化内容系统团队的 {topic} 示例",
        intent_en="Example-driven intent for readers who learn fastest from concrete cases.",
        intent_zh="面向希望通过具体案例理解主题的示例型搜索意图。",
        angle_en=(
            "Use concrete scenarios and before/after examples instead of abstract explanation."
        ),
        angle_zh="优先写具体场景和前后对比, 而不是抽象解释。",
    ),
)

LOCALE_STRINGS = {
    "en-US": {
        "lang": "en",
        "og_locale": "en_US",
        "site_title": "Socrates",
        "eyebrow": "Resource Library",
        "library_title": "Evergreen resources for teams building serious content systems.",
        "library_description": (
            "These pages are generated through a guarded editorial workflow. "
            "They aim to answer real search intent around AI content operations, "
            "B2B messaging, and structured publishing."
        ),
        "library_button": "Read docs",
        "library_button_href": "../docs.html",
        "nav_home": "Home",
        "nav_product": "Product",
        "nav_use_cases": "Use Cases",
        "nav_library": "Library",
        "nav_docs": "Docs",
        "nav_faq": "FAQ",
        "footer_tagline": (
            "Strategy-first content generation for professional teams and AI builders."
        ),
        "library_brand": "Socrates Library",
        "article_eyebrow_prefix": "Evergreen",
        "faq_heading": "Frequently asked questions",
        "cta_eyebrow": "Next step",
        "cta_secondary_label": "Explore the library",
        "cta_secondary_href_article": "./index.html",
        "cta_secondary_href_index": "../docs.html",
        "back_to_library": "Back to library",
        "index_primary_cta": "Open the docs",
        "date_label": "Published",
        "score_label": "Review score",
        "no_pages_title": "No pages yet",
        "no_pages_body": "The daily generator has not published resource pages yet.",
    },
    "zh-CN": {
        "lang": "zh-CN",
        "og_locale": "zh_CN",
        "site_title": "Socrates",
        "eyebrow": "资源库",
        "library_title": "给专业内容系统团队准备的长期有效资源页。",
        "library_description": (
            "这些页面通过受控的编辑流程生成, 围绕 AI 内容运营、B2B 信息表达、"
            "多阶段发布工作流等真实搜索意图提供可读、可用的知识页面。"
        ),
        "library_button": "阅读文档",
        "library_button_href": "../docs.html",
        "nav_home": "首页",
        "nav_product": "产品",
        "nav_use_cases": "应用场景",
        "nav_library": "资源库",
        "nav_docs": "文档",
        "nav_faq": "FAQ",
        "footer_tagline": "面向专业团队和 AI Builder 的策略先行内容生成工作流。",
        "library_brand": "Socrates 资源库",
        "article_eyebrow_prefix": "长期内容",
        "faq_heading": "常见问题",
        "cta_eyebrow": "下一步",
        "cta_secondary_label": "查看资源库",
        "cta_secondary_href_article": "./index.html",
        "cta_secondary_href_index": "../docs.html",
        "back_to_library": "返回资源库",
        "index_primary_cta": "打开文档",
        "date_label": "发布时间",
        "score_label": "审稿分数",
        "no_pages_title": "暂无页面",
        "no_pages_body": "每日生成任务尚未发布新的资源页。",
    },
}


def build_topic_inventory() -> list[TopicSeed]:
    """Build the full evergreen topic inventory."""

    seeds: list[TopicSeed] = []
    for family in TOPIC_FAMILIES:
        for pattern in TOPIC_PATTERNS:
            seed_key = f"{family.key}:{pattern.key}"
            slug = f"{family.key}-{pattern.key}"
            seeds.append(
                TopicSeed(
                    key=seed_key,
                    slug=slug,
                    family_key=family.key,
                    pattern_key=pattern.key,
                    title_en=pattern.title_en.format(
                        topic=family.subject_en,
                        audience=family.audience_en,
                    ),
                    title_zh=pattern.title_zh.format(
                        topic=family.subject_zh,
                        audience=family.audience_zh,
                    ),
                    audience_en=family.audience_en,
                    audience_zh=family.audience_zh,
                    cluster_en=family.cluster_en,
                    cluster_zh=family.cluster_zh,
                    keyword_en=family.keyword_en,
                    keyword_zh=family.keyword_zh,
                    secondary_keywords_en=family.secondary_keywords_en,
                    secondary_keywords_zh=family.secondary_keywords_zh,
                    intent_en=pattern.intent_en,
                    intent_zh=pattern.intent_zh,
                    angle_en=pattern.angle_en,
                    angle_zh=pattern.angle_zh,
                )
            )
    return seeds


def load_state(path: Path) -> SiteAutomationState:
    """Load persistent generator state."""

    if not path.exists():
        return SiteAutomationState()
    return SiteAutomationState.model_validate_json(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: SiteAutomationState) -> None:
    """Persist generator state."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")


def select_next_topics(state: SiteAutomationState, *, count: int) -> list[TopicSeed]:
    """Pick the next unpublished evergreen topics in deterministic order."""

    selected: list[TopicSeed] = []
    published = set(state.published_seed_keys)
    for seed in build_topic_inventory():
        if seed.key in published:
            continue
        selected.append(seed)
        if len(selected) >= count:
            break
    return selected


def _seed_title(seed: TopicSeed, locale: str) -> str:
    return seed.title_zh if locale == "zh-CN" else seed.title_en


def _seed_audience(seed: TopicSeed, locale: str) -> str:
    return seed.audience_zh if locale == "zh-CN" else seed.audience_en


def _seed_cluster(seed: TopicSeed, locale: str) -> str:
    return seed.cluster_zh if locale == "zh-CN" else seed.cluster_en


def _seed_keyword(seed: TopicSeed, locale: str) -> str:
    return seed.keyword_zh if locale == "zh-CN" else seed.keyword_en


def _seed_keywords(seed: TopicSeed, locale: str) -> tuple[str, ...]:
    if locale == "zh-CN":
        return (seed.keyword_zh, *seed.secondary_keywords_zh)
    return (seed.keyword_en, *seed.secondary_keywords_en)


def _seed_intent(seed: TopicSeed, locale: str) -> str:
    return seed.intent_zh if locale == "zh-CN" else seed.intent_en


def _seed_angle(seed: TopicSeed, locale: str) -> str:
    return seed.angle_zh if locale == "zh-CN" else seed.angle_en


def build_site_article_messages(
    seed: TopicSeed,
    *,
    locale: str,
    revision_notes: str | None = None,
) -> list[dict[str, str]]:
    """Build generation messages for a public evergreen page."""

    title = _seed_title(seed, locale)
    audience = _seed_audience(seed, locale)
    primary_keyword = _seed_keyword(seed, locale)
    keywords = ", ".join(_seed_keywords(seed, locale))
    search_intent = _seed_intent(seed, locale)
    angle = _seed_angle(seed, locale)
    notes = revision_notes or "None."
    locale_name = "Simplified Chinese" if locale == "zh-CN" else "English"
    return [
        {"role": "system", "content": SITE_ARTICLE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Create a publishable evergreen resource page in {locale_name}.\n"
                "Use the title exactly as supplied.\n"
                "Requirements:\n"
                "- The page must satisfy real search intent, not fake-search boilerplate.\n"
                "- Keep the explanation specific to B2B teams, AI content systems, or "
                "structured publishing workflows.\n"
                "- Use practical sections, examples, checklists, and execution cues.\n"
                "- Meta description must be concise and realistic.\n"
                "- FAQs must answer likely follow-up questions, not repeat headings.\n"
                "- CTA should point readers toward a thoughtful next step, not a hypey sell.\n"
                "- Avoid legal, medical, financial, or unsafe advice.\n"
                "- Avoid naming competitors unless absolutely required; prefer category-level "
                "discussion.\n\n"
                f"Title: {title}\n"
                f"Audience: {audience}\n"
                f"Cluster: {_seed_cluster(seed, locale)}\n"
                f"Primary keyword: {primary_keyword}\n"
                f"Supporting keywords: {keywords}\n"
                f"Search intent: {search_intent}\n"
                f"Angle: {angle}\n"
                f"Revision notes from prior review: {notes}"
            ),
        },
    ]


def _article_to_markdown(title: str, article: SiteArticlePayload) -> str:
    parts = [f"# {title}", ""]
    for paragraph in article.intro:
        parts.append(paragraph.strip())
        parts.append("")
    for section in article.sections:
        parts.append(f"## {section.heading.strip()}")
        parts.append("")
        for paragraph in section.paragraphs:
            parts.append(paragraph.strip())
            parts.append("")
        if section.bullets:
            parts.extend(f"- {bullet.strip()}" for bullet in section.bullets)
            parts.append("")
    parts.append("## FAQ")
    parts.append("")
    for item in article.faq:
        parts.append(f"### {item.question.strip()}")
        parts.append("")
        parts.append(item.answer.strip())
        parts.append("")
    return "\n".join(parts).strip()


def _keyword_stuffing_hits(text: str, keyword: str) -> int:
    pattern = re.escape(keyword.lower())
    return len(re.findall(pattern, text.lower()))


def validate_site_article(
    title: str,
    article: SiteArticlePayload,
    *,
    locale: str,
    keyword: str,
) -> list[str]:
    """Run local anti-spam and thin-content checks."""

    issues: list[str] = []
    combined_text = " ".join(
        [
            title,
            article.meta_description,
            article.summary,
            *article.intro,
            *(paragraph for section in article.sections for paragraph in section.paragraphs),
            *(bullet for section in article.sections for bullet in section.bullets),
            *(item.question for item in article.faq),
            *(item.answer for item in article.faq),
            article.cta_heading,
            article.cta_body,
        ]
    )
    lowered = combined_text.lower()
    for phrase in AI_SEO_PHRASES:
        if phrase in lowered:
            issues.append(f"Contains risky SEO phrase: {phrase}")

    if locale == "zh-CN":
        meta_len = len(article.meta_description)
        if meta_len < 35 or meta_len > 100:
            issues.append("Chinese meta description length is outside the expected range.")
    else:
        meta_len = len(article.meta_description)
        if meta_len < 80 or meta_len > 170:
            issues.append("English meta description length is outside the expected range.")

    heading_set = {section.heading.strip().lower() for section in article.sections}
    if len(heading_set) != len(article.sections):
        issues.append("Section headings are duplicated.")

    keyword_hits = _keyword_stuffing_hits(combined_text, keyword)
    if keyword_hits > 12:
        issues.append("Primary keyword appears too often and may look stuffed.")

    if any(len(section.paragraphs) < 2 for section in article.sections):
        issues.append("Each section must have at least two paragraphs.")

    if len(article.faq) < 3:
        issues.append("FAQ coverage is too thin.")

    return issues


def _review_site_article(
    client: Socrates,
    seed: TopicSeed,
    article: SiteArticlePayload,
    *,
    locale: str,
) -> ReviewReport:
    request = ContentRequest(
        topic=_seed_title(seed, locale),
        audience=_seed_audience(seed, locale),
        goal="Publish a useful evergreen resource page for the public website",
        platform="web",
        content_type="industry_analysis",
        constraints=[
            "Keep the page educational and original",
            "Avoid fabricated certainty and unsupported claims",
            "Avoid clickbait or affiliate-style SEO copy",
        ],
        voice_notes=["Specific", "Credible", "Practical"],
        keywords=list(_seed_keywords(seed, locale)),
        locale=locale,
        include_cta=True,
        cta_goal="Move the reader into docs or deeper product understanding",
    )
    draft = ContentDraft(
        title=_seed_title(seed, locale),
        body=_article_to_markdown(_seed_title(seed, locale), article),
        summary=article.summary,
        cta=article.cta_body,
    )
    return client.review(request, draft)


def _fallback_meta_description(seed: TopicSeed, locale: str) -> str:
    keyword = _seed_keyword(seed, locale)
    audience = _seed_audience(seed, locale)
    if locale == "zh-CN":
        return (
            f"面向{audience}的{keyword}实用页面, 说明团队如何用更清晰的结构、"
            "可信度和发布标准完成专业内容。"
        )
    return (
        f"A practical page on {keyword} for {audience}, showing how teams improve "
        "structure, credibility, and publishable output."
    )


def _fallback_summary(seed: TopicSeed, locale: str) -> str:
    keyword = _seed_keyword(seed, locale)
    audience = _seed_audience(seed, locale)
    if locale == "zh-CN":
        return (
            f"{keyword}真正有价值的地方, 不只是帮助团队写得更快, 而是帮助{audience}"
            "先把标准、结构和受众匹配关系说清楚。"
        )
    return (
        f"{keyword} matters because it helps {audience} clarify standards, structure, "
        "and audience fit before publishing."
    )


def _fallback_intro(seed: TopicSeed, locale: str) -> list[str]:
    keyword = _seed_keyword(seed, locale)
    audience = _seed_audience(seed, locale)
    cluster = _seed_cluster(seed, locale)
    angle = _seed_angle(seed, locale)
    if locale == "zh-CN":
        return [
            (
                f"很多团队讨论{keyword}时, 只把它当成写作技巧或提示词问题。真正重要的,"
                f" 是它如何帮助{audience}在{cluster}层面建立更稳定的内容判断。"
            ),
            (
                f"这也是这类页面值得单独解释的原因: {angle}。当标准先于正文被明确,"
                " 后续起草、审稿和发布都会更稳。"
            ),
        ]
    return [
        (
            f"Teams often talk about {keyword} as if it were only a writing tactic. The "
            f"real value is how it helps {audience} create stronger standards inside "
            f"{cluster} work."
        ),
        (
            f"That is why this topic deserves a dedicated page: {angle} Once the standard "
            "is explicit, drafting, review, and publishing become far more reliable."
        ),
    ]


def _fallback_pattern_section(seed: TopicSeed, locale: str) -> SiteArticleSection:
    keyword = _seed_keyword(seed, locale)
    audience = _seed_audience(seed, locale)
    pattern = seed.pattern_key
    if locale == "zh-CN":
        section_map = {
            "guide": (
                f"{keyword}的实用工作流",
                [
                    (
                        "先说明目标读者、页面目标和核心结论, 再决定信息顺序和例子位置。"
                        " 这样内容会更像面向真实业务场景的页面, 而不是泛泛解释。"
                    ),
                    (
                        f"对{audience}来说, 关键不是把所有信息都塞进去, 而是按读者最关心的"
                        "问题组织内容。"
                    ),
                ],
                ["先明确目标", "再安排结构", "最后对照标准复核"],
            ),
            "checklist": (
                f"{keyword}检查清单",
                [
                    (
                        "把页面拆成可复核的检查项, 比把要求写成一段抽象说明更稳。"
                        " 团队可以在起草前后都使用同一套标准。"
                    ),
                    (
                        "这类清单通常应覆盖读者定位、可信度要求、结构节奏和 CTA 匹配度。"
                    ),
                ],
                ["读者是否明确", "关键信号是否具体", "CTA 是否顺着读者意图"],
            ),
            "template": (
                f"{keyword}模板结构",
                [
                    (
                        "模板最有价值的地方不是节省打字, 而是让团队以同一种结构开始工作。"
                    ),
                    (
                        "只要字段设计围绕真实判断点展开, 模板就能减少空话和结构漂移。"
                    ),
                ],
                ["保留核心字段", "为每个字段写明用途", "标注常见误填方式"],
            ),
            "mistakes": (
                f"{keyword}最常见的误区",
                [
                    (
                        "大多数失败并不是因为团队不会写, 而是因为它们把重点放在表面流畅,"
                        " 忽略了真正影响读者判断的顺序和证据。"
                    ),
                    (
                        "一旦误区被提前写明, 后续生成和审稿就更容易保持一致。"
                    ),
                ],
                ["不要先堆功能", "不要省略可信度信号", "不要用空泛 CTA 收尾"],
            ),
            "playbook": (
                f"{keyword}操作手册",
                [
                    (
                        "把主题写成 playbook, 可以帮助团队明确谁负责什么、按什么顺序执行,"
                        " 以及哪些节点必须复核。"
                    ),
                    (
                        "这类页面最适合高价值内容, 因为它会把流程拆成真正可执行的动作。"
                    ),
                ],
                ["定义角色", "定义顺序", "定义复核点"],
            ),
            "examples": (
                f"{keyword}示例拆解",
                [
                    (
                        "示例页面应该优先展示真实情境中的前后差异, 而不是只重复定义。"
                    ),
                    (
                        f"对{audience}来说, 具体示例通常比抽象理论更能帮助执行。"
                    ),
                ],
                ["展示场景", "说明变化原因", "给出可迁移做法"],
            ),
        }
    else:
        section_map = {
            "guide": (
                f"A practical workflow for {keyword}",
                [
                    (
                        "Start by naming the reader, the page goal, and the takeaway the "
                        "content needs to create. That gives the page a working structure "
                        "instead of a loose collection of points."
                    ),
                    (
                        f"For {audience}, the priority is not adding every possible detail. "
                        "It is sequencing the information around the questions that matter most."
                    ),
                ],
                [
                    "Clarify the objective first",
                    "Sequence the argument second",
                    "Review against the standard before publishing",
                ],
            ),
            "checklist": (
                f"A working checklist for {keyword}",
                [
                    (
                        "Turning the topic into checkpoints is often more useful than writing "
                        "a long abstract explanation. Teams can use the same list before and "
                        "after drafting."
                    ),
                    (
                        "The best checklists cover audience clarity, credibility signals, "
                        "structural pacing, and CTA alignment."
                    ),
                ],
                [
                    "Is the reader clearly defined?",
                    "Are the proof signals specific enough?",
                    "Does the CTA follow reader intent?",
                ],
            ),
            "template": (
                f"A reusable template for {keyword}",
                [
                    (
                        "Templates matter when they make teams start from the same decision "
                        "structure rather than from the same empty page."
                    ),
                    (
                        "If every field exists for a reason, the template reduces drift and "
                        "keeps drafts closer to the intended audience outcome."
                    ),
                ],
                [
                    "Keep only decision-relevant fields",
                    "Explain what each field controls",
                    "Show what a weak fill-in looks like",
                ],
            ),
            "mistakes": (
                f"Common mistakes around {keyword}",
                [
                    (
                        "Most teams do not fail because they cannot write. They fail because "
                        "they optimize for surface fluency while skipping structure, proof, "
                        "and reader sequencing."
                    ),
                    (
                        "Documenting the mistakes early makes generation and review far more "
                        "consistent."
                    ),
                ],
                [
                    "Do not lead with features alone",
                    "Do not skip credibility signals",
                    "Do not end with a generic CTA",
                ],
            ),
            "playbook": (
                f"A repeatable playbook for {keyword}",
                [
                    (
                        "A playbook turns the topic into role ownership, sequence, and review "
                        "points. That is what makes it operational instead of purely conceptual."
                    ),
                    (
                        "This format is most useful for high-value content where repeatability "
                        "matters as much as the draft itself."
                    ),
                ],
                [
                    "Assign ownership clearly",
                    "Define execution order",
                    "Document the review gates",
                ],
            ),
            "examples": (
                f"Examples that make {keyword} easier to apply",
                [
                    (
                        "Example-driven pages work best when they show before-and-after choices "
                        "instead of repeating definitions in new words."
                    ),
                    (
                        f"For {audience}, concrete scenarios usually travel further than "
                        "abstract advice."
                    ),
                ],
                [
                    "Show the context",
                    "Explain what changed",
                    "Extract a reusable lesson",
                ],
            ),
        }
    heading, paragraphs, bullets = section_map[pattern]
    return SiteArticleSection(heading=heading, paragraphs=paragraphs, bullets=bullets)


def _fallback_review_section(seed: TopicSeed, locale: str) -> SiteArticleSection:
    audience = _seed_audience(seed, locale)
    if locale == "zh-CN":
        return SiteArticleSection(
            heading="发布前应该重点复核什么",
            paragraphs=[
                (
                    "真正影响页面质量的, 往往不是错别字, 而是有没有重复、有没有无支撑的判断、"
                    "以及结构是否真的服务读者问题。"
                ),
                (
                    f"对{audience}这类专业读者来说, 具体、克制和顺序正确, 往往比口号式表达"
                    "更重要。"
                ),
            ],
            bullets=[
                "检查是否存在空话和重复",
                "检查关键判断是否有具体支撑",
                "检查 CTA 是否符合页面阶段",
            ],
        )
    return SiteArticleSection(
        heading="What to review before the page goes live",
        paragraphs=[
            (
                "The quality risks that matter most are usually not grammar mistakes. They are "
                "repetition, unsupported certainty, and structures that do not fully answer the "
                "reader's real question."
            ),
            (
                f"For professional readers like {audience}, specificity, restraint, and clean "
                "sequencing usually matter more than high-energy phrasing."
            ),
        ],
        bullets=[
            "Check for filler and repetition",
            "Verify that the key claims are grounded",
            "Make sure the CTA fits the stage of the page",
        ],
    )


def _fallback_foundation_section(seed: TopicSeed, locale: str) -> SiteArticleSection:
    keyword = _seed_keyword(seed, locale)
    audience = _seed_audience(seed, locale)
    search_intent = _seed_intent(seed, locale)
    if locale == "zh-CN":
        return SiteArticleSection(
            heading=f"{keyword}真正解决的是什么问题",
            paragraphs=[
                (
                    f"从搜索意图看, 这类页面通常是在回答这样的问题: {search_intent}"
                ),
                (
                    f"对{audience}来说, 重点不是把概念说得多复杂, 而是明确它如何影响团队的"
                    "内容判断、结构安排和发布质量。"
                ),
            ],
            bullets=[
                "先定义问题边界",
                "再解释为什么值得关注",
                "最后连接到实际工作流",
            ],
        )
    return SiteArticleSection(
        heading=f"What teams are actually solving with {keyword}",
        paragraphs=[
            (
                "At the search-intent level, this page is answering a simple question: "
                f"{search_intent}"
            ),
            (
                f"For {audience}, the practical concern is not a more abstract definition. "
                "It is understanding how the concept changes standards, structure, and "
                "publishability in real work."
            ),
        ],
        bullets=[
            "Define the boundary of the topic",
            "Explain why it matters in practice",
            "Connect it to an actual workflow",
        ],
    )


def _fallback_audience_section(seed: TopicSeed, locale: str) -> SiteArticleSection:
    audience = _seed_audience(seed, locale)
    cluster = _seed_cluster(seed, locale)
    angle = _seed_angle(seed, locale)
    if locale == "zh-CN":
        return SiteArticleSection(
            heading=f"为什么{audience}特别需要这类能力",
            paragraphs=[
                (
                    f"{audience}面对的核心难题, 往往不是信息不够, 而是如何在{cluster}工作里"
                    "做出稳定、可解释的判断。"
                ),
                (
                    f"这正是本页强调的角度: {angle}。当角度被明确后, 团队更容易把内容写得"
                    "具体、可信、并且适合发布。"
                ),
            ],
            bullets=[
                "围绕读者问题建立判断",
                "把可信度要求前置",
                "让结构服务于最终结论",
            ],
        )
    return SiteArticleSection(
        heading=f"Why this matters for {audience}",
        paragraphs=[
            (
                f"The hard part for {audience} is rarely a lack of information. It is making "
                f"stable, explainable decisions inside {cluster} work."
            ),
            (
                f"That is the angle this page emphasizes: {angle} Once the angle is explicit, "
                "teams can produce content that feels more specific, credible, and publishable."
            ),
        ],
        bullets=[
            "Anchor decisions in the reader problem",
            "Define credibility requirements early",
            "Let structure serve the final takeaway",
        ],
    )


def _fallback_faq(seed: TopicSeed, locale: str) -> list[SiteArticleFaq]:
    keyword = _seed_keyword(seed, locale)
    audience = _seed_audience(seed, locale)
    if locale == "zh-CN":
        return [
            SiteArticleFaq(
                question=f"{keyword}最适合用在哪些内容上?",
                answer=(
                    f"最适合高价值、需要结构和受众匹配的内容, 尤其适合{audience}"
                    "面对的发布级页面。"
                ),
            ),
            SiteArticleFaq(
                question=f"团队刚开始使用{keyword}时最该避免什么?",
                answer="最该避免的是只把它当成写作技巧, 却不把标准、证据和顺序写清楚。",
            ),
            SiteArticleFaq(
                question=f"{keyword}应该如何进入实际工作流?",
                answer=(
                    "最稳的方式是把它放到 brief、结构设计和审稿节点里, 而不是只放在"
                    "最终写作提示里。"
                ),
            ),
        ]
    return [
        SiteArticleFaq(
            question=f"What kinds of pages benefit most from {keyword}?",
            answer=(
                f"It adds the most value to high-stakes pages where {audience} need clearer "
                "structure, stronger audience fit, and a cleaner review path."
            ),
        ),
        SiteArticleFaq(
            question=f"What should teams avoid when adopting {keyword}?",
            answer=(
                "The biggest mistake is treating it as a writing trick while leaving standards, "
                "evidence, and sequencing undefined."
            ),
        ),
        SiteArticleFaq(
            question=f"How should {keyword} fit into a real workflow?",
            answer=(
                "The safest approach is to place it inside the brief, structure, and review "
                "stages instead of leaving it only in the final drafting prompt."
            ),
        ),
    ]


def build_fallback_site_article(seed: TopicSeed, *, locale: str) -> SiteArticlePayload:
    """Build a deterministic article payload when the live provider is unavailable."""

    sections = [
        _fallback_foundation_section(seed, locale),
        _fallback_audience_section(seed, locale),
        _fallback_pattern_section(seed, locale),
        _fallback_review_section(seed, locale),
    ]
    if locale == "zh-CN":
        return SiteArticlePayload(
            meta_description=_fallback_meta_description(seed, locale),
            summary=_fallback_summary(seed, locale),
            intro=_fallback_intro(seed, locale),
            sections=sections,
            faq=_fallback_faq(seed, locale),
            cta_heading="把这个主题接进稳定的内容系统",
            cta_body="查看文档, 用 frame、outline、draft 和 review 组成更稳的发布工作流。",
            cta_label="阅读文档",
        )
    return SiteArticlePayload(
        meta_description=_fallback_meta_description(seed, locale),
        summary=_fallback_summary(seed, locale),
        intro=_fallback_intro(seed, locale),
        sections=sections,
        faq=_fallback_faq(seed, locale),
        cta_heading="Turn this topic into a repeatable publishing asset",
        cta_body=(
            "Open the docs to connect frames, outlines, drafts, and review checks into a more "
            "reliable publishing workflow."
        ),
        cta_label="Read the docs",
    )


def generate_site_article(
    client: Socrates,
    seed: TopicSeed,
    *,
    locale: str,
    max_attempts: int = 2,
) -> tuple[SiteArticlePayload, int]:
    """Generate and review a site article, retrying once if needed."""

    notes: str | None = None
    provider_failed = False
    for attempt in range(1, max_attempts + 1):
        try:
            article = client.provider.structured_completion(
                messages=build_site_article_messages(seed, locale=locale, revision_notes=notes),
                response_model=SiteArticlePayload,
                model=client.config.models.resolve("draft"),
                temperature=client.config.models.temperature,
            )
            issues = validate_site_article(
                _seed_title(seed, locale),
                article,
                locale=locale,
                keyword=_seed_keyword(seed, locale),
            )
            review = _review_site_article(client, seed, article, locale=locale)
            if not issues and review.passes and review.publishability_score >= 78:
                return article, review.publishability_score

            findings = "; ".join(f.evidence for f in review.findings[:4]) or review.summary
            issue_blob = "; ".join(issues) or "No local issues captured."
            notes = (
                f"Attempt {attempt} failed review. Local issues: {issue_blob}. "
                f"Review summary: {review.summary}. Findings: {findings}."
            )
        except ProviderError as exc:
            notes = f"Attempt {attempt} hit a provider error: {exc}."
            provider_failed = True
            break

    fallback_article = build_fallback_site_article(seed, locale=locale)
    fallback_issues = validate_site_article(
        _seed_title(seed, locale),
        fallback_article,
        locale=locale,
        keyword=_seed_keyword(seed, locale),
    )
    fallback_review = _review_site_article(client, seed, fallback_article, locale=locale)
    if (
        not fallback_issues
        and fallback_review.passes
        and fallback_review.publishability_score >= 78
    ):
        return fallback_article, fallback_review.publishability_score

    reason = "provider failure" if provider_failed else "review failure"
    raise RuntimeError(
        f"Could not generate a safe publishable article for {seed.key} ({locale}) after {reason}."
    )


def _article_relative_path(locale: str, slug: str) -> str:
    if locale == "zh-CN":
        return f"zh/library/{slug}.html"
    return f"library/{slug}.html"


def _canonical_url(path: str) -> str:
    return f"{SITE_DOMAIN}/{path}".replace("//zh", "/zh").replace(".xyz//", ".xyz/")


def _locale_roots(locale: str) -> dict[str, str]:
    if locale == "zh-CN":
        return {
            "asset_prefix": "../../",
            "section_prefix": "../",
            "english_switch": "../../index.html",
            "local_switch": "./index.html",
            "home_href": "../index.html",
            "product_href": "../product.html",
            "use_cases_href": "../use-cases.html",
            "library_href": "./index.html",
            "docs_href": "../docs.html",
            "faq_href": "../faq.html",
            "other_locale_href": "../../library/",
        }
    return {
        "asset_prefix": "../",
        "section_prefix": "../",
        "english_switch": "./index.html",
        "local_switch": "./index.html",
        "home_href": "../index.html",
        "product_href": "../product.html",
        "use_cases_href": "../use-cases.html",
        "library_href": "./index.html",
        "docs_href": "../docs.html",
        "faq_href": "../faq.html",
        "other_locale_href": "../../zh/library/",
    }


def _language_switch(locale: str, path: str) -> tuple[str, str]:
    slug = Path(path).name
    if locale == "zh-CN":
        return f"../../library/{slug}", f"./{slug}"
    return f"./{slug}", f"../../zh/library/{slug}"


def _render_header(locale: str, *, current: str, article_path: str | None = None) -> str:
    strings = LOCALE_STRINGS[locale]
    roots = _locale_roots(locale)
    if article_path is None:
        if current == "library":
            en_href = "../../library/index.html" if locale == "zh-CN" else "./index.html"
            zh_href = "./index.html" if locale == "zh-CN" else "../../zh/library/index.html"
        else:
            en_href = "../index.html"
            zh_href = "./index.html" if locale == "zh-CN" else "../../zh/index.html"
    else:
        en_href, zh_href = _language_switch(locale, article_path)

    if locale == "zh-CN":
        lang_a = f'<a class="lang-link" href="{en_href}">EN</a>'
        lang_b = f'<a class="lang-link lang-link-active" href="{zh_href}">中文</a>'
    else:
        lang_a = f'<a class="lang-link lang-link-active" href="{en_href}">EN</a>'
        lang_b = f'<a class="lang-link" href="{zh_href}">中文</a>'

    nav_map = {
        "product": roots["product_href"],
        "use_cases": roots["use_cases_href"],
        "library": roots["library_href"],
        "docs": roots["docs_href"],
        "faq": roots["faq_href"],
    }
    links = [
        f'<a href="{nav_map["product"]}">{strings["nav_product"]}</a>',
        f'<a href="{nav_map["use_cases"]}">{strings["nav_use_cases"]}</a>',
        f'<a href="{nav_map["library"]}">{strings["nav_library"]}</a>',
        f'<a href="{nav_map["docs"]}">{strings["nav_docs"]}</a>',
        f'<a href="{nav_map["faq"]}">{strings["nav_faq"]}</a>',
    ]
    return dedent(
        f"""
        <header class="topbar">
          <a class="brand" href="{roots["home_href"]}">
            <span class="brand-mark">S</span>
            <span>Socrates</span>
          </a>
          <nav class="nav">
            {' '.join(links)}
          </nav>
          <div class="topbar-actions">
            <div class="lang-switch" aria-label="Language switcher">
              {lang_a}
              {lang_b}
            </div>
            <a class="button button-ghost" href="https://github.com/miounet11/Socrates">GitHub</a>
          </div>
        </header>
        """
    ).strip()


def _render_footer(locale: str) -> str:
    strings = LOCALE_STRINGS[locale]
    roots = _locale_roots(locale)
    return dedent(
        f"""
        <footer class="footer footer-grid">
          <div>
            <strong>Socrates</strong>
            <p>{escape(strings["footer_tagline"])}</p>
          </div>
          <div class="footer-links">
            <a href="{roots["home_href"]}">{strings["nav_home"]}</a>
            <a href="{roots["product_href"]}">{strings["nav_product"]}</a>
            <a href="{roots["library_href"]}">{strings["nav_library"]}</a>
            <a href="{roots["docs_href"]}">{strings["nav_docs"]}</a>
            <a href="{roots["faq_href"]}">{strings["nav_faq"]}</a>
          </div>
        </footer>
        """
    ).strip()


def _json_ld_article(record: PublishedArticleRecord, article: SiteArticlePayload) -> str:
    article_object = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": record.title,
        "description": record.meta_description,
        "datePublished": record.published_at,
        "dateModified": record.published_at,
        "author": {"@type": "Organization", "name": "Socrates"},
        "publisher": {"@type": "Organization", "name": "Socrates"},
        "mainEntityOfPage": record.url,
    }
    faq_object = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item.question,
                "acceptedAnswer": {"@type": "Answer", "text": item.answer},
            }
            for item in article.faq
        ],
    }
    return (
        '<script type="application/ld+json">'
        + json.dumps(article_object, ensure_ascii=False)
        + "</script>\n"
        + '<script type="application/ld+json">'
        + json.dumps(faq_object, ensure_ascii=False)
        + "</script>"
    )


def _article_alternate_urls(slug: str) -> tuple[str, str]:
    return (
        _canonical_url(f"library/{slug}.html"),
        _canonical_url(f"zh/library/{slug}.html"),
    )


def render_article_html(article: SiteArticlePayload, record: PublishedArticleRecord) -> str:
    """Render a generated article page to HTML."""

    locale = record.locale
    strings = LOCALE_STRINGS[locale]
    roots = _locale_roots(locale)
    en_url, zh_url = _article_alternate_urls(record.slug)
    title_suffix = escape(strings["library_brand"])
    title = escape(record.title)
    summary = escape(article.summary)
    intro_html = "\n".join(f"<p>{escape(paragraph)}</p>" for paragraph in article.intro)

    sections_html: list[str] = []
    for section in article.sections:
        paragraphs_html = "\n".join(
            f"<p>{escape(paragraph)}</p>" for paragraph in section.paragraphs
        )
        bullets_html = ""
        if section.bullets:
            bullets = "\n".join(f"<li>{escape(item)}</li>" for item in section.bullets)
            bullets_html = f'\n<ul class="check-list">\n{bullets}\n</ul>'
        sections_html.append(
            dedent(
                f"""
                <article class="page-card">
                  <h3>{escape(section.heading)}</h3>
                  {paragraphs_html}{bullets_html}
                </article>
                """
            ).strip()
        )

    faq_html = "\n".join(
        dedent(
            f"""
            <details>
              <summary>{escape(item.question)}</summary>
              <p>{escape(item.answer)}</p>
            </details>
            """
        ).strip()
        for item in article.faq
    )

    return dedent(
        f"""
        <!doctype html>
        <html lang="{strings["lang"]}">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>{title} | {title_suffix}</title>
            <meta name="description" content="{escape(record.meta_description)}" />
            <link rel="canonical" href="{record.url}" />
            <link rel="alternate" hreflang="en" href="{en_url}" />
            <link rel="alternate" hreflang="zh-CN" href="{zh_url}" />
            <link rel="alternate" hreflang="x-default" href="{en_url}" />
            <meta property="og:type" content="article" />
            <meta property="og:locale" content="{strings["og_locale"]}" />
            <meta property="og:title" content="{title} | {title_suffix}" />
            <meta property="og:description" content="{escape(record.meta_description)}" />
            <meta property="og:url" content="{record.url}" />
            <meta property="og:image" content="{SITE_DOMAIN}/og.svg" />
            <meta name="twitter:card" content="summary_large_image" />
            <meta name="twitter:title" content="{title} | {title_suffix}" />
            <meta name="twitter:description" content="{escape(record.meta_description)}" />
            <meta name="twitter:image" content="{SITE_DOMAIN}/og.svg" />
            <meta name="theme-color" content="#f4efe5" />
            <link rel="icon" href="{roots["asset_prefix"]}favicon.svg" type="image/svg+xml" />
            <link rel="stylesheet" href="{roots["asset_prefix"]}styles.css" />
            {_json_ld_article(record, article)}
          </head>
          <body>
            <div class="page-shell">
              {_render_header(locale, current="library", article_path=record.path)}

              <main>
                <section class="page-hero">
                  <p class="eyebrow">
                    {escape(strings["article_eyebrow_prefix"])} · {escape(record.cluster)}
                  </p>
                  <h1>{title}</h1>
                  <p class="hero-text">{summary}</p>
                  <ul class="hero-proof">
                    <li>{escape(strings["date_label"])}: {escape(record.published_at[:10])}</li>
                    <li>{escape(strings["score_label"])}: {record.review_score}</li>
                    <li>{escape(record.primary_keyword)}</li>
                  </ul>
                </section>

                <section class="section-tight">
                  <div class="narrative">
                    {intro_html}
                  </div>
                </section>

                <section class="section">
                  <div class="section-head">
                    <p class="eyebrow">{escape(strings["eyebrow"])}</p>
                    <h2>{title}</h2>
                  </div>
                  <div class="feature-grid">
                    {' '.join(sections_html)}
                  </div>
                </section>

                <section class="section section-accent">
                  <div class="section-head">
                    <p class="eyebrow">FAQ</p>
                    <h2>{escape(strings["faq_heading"])}</h2>
                  </div>
                  <div class="faq-list">
                    {faq_html}
                  </div>
                </section>

                <section class="section cta-band">
                  <div>
                    <p class="eyebrow">{escape(strings["cta_eyebrow"])}</p>
                    <h2>{escape(article.cta_heading)}</h2>
                    <p>{escape(article.cta_body)}</p>
                  </div>
                  <div class="hero-actions">
                    <a class="button" href="{roots["docs_href"]}">{escape(article.cta_label)}</a>
                    <a class="button button-ghost" href="./index.html">
                      {escape(strings["back_to_library"])}
                    </a>
                  </div>
                </section>
              </main>

              {_render_footer(locale)}
            </div>
          </body>
        </html>
        """
    ).strip()


def render_library_index_html(locale: str, records: list[PublishedArticleRecord]) -> str:
    """Render the library index page for one locale."""

    strings = LOCALE_STRINGS[locale]
    roots = _locale_roots(locale)
    if locale == "zh-CN":
        title = "Socrates 资源库 | 面向 AI 内容系统的长期知识页"
        description = (
            "浏览围绕 AI 内容运营、B2B 信息表达、结构化内容工作流生成的长期资源页。"
        )
        canonical = f"{SITE_DOMAIN}/zh/library/"
    else:
        title = "Socrates Library | Evergreen guides for AI content systems"
        description = (
            "Browse evergreen resource pages about AI content operations, B2B messaging, "
            "content governance, and structured publishing workflows."
        )
        canonical = f"{SITE_DOMAIN}/library/"

    cards = []
    for record in sorted(records, key=lambda item: item.published_at, reverse=True):
        href = f"./{record.slug}.html"
        cards.append(
            dedent(
                f"""
                <a class="resource-card" href="{href}">
                  <h3>{escape(record.title)}</h3>
                  <p>{escape(record.summary)}</p>
                  <p>
                    <strong>{escape(record.cluster)}</strong> · {escape(record.published_at[:10])}
                  </p>
                </a>
                """
            ).strip()
        )
    if not cards:
        cards.append(
            '<article class="resource-card">'
            f'<h3>{escape(strings["no_pages_title"])}</h3>'
            f'<p>{escape(strings["no_pages_body"])}</p>'
            "</article>"
        )

    return dedent(
        f"""
        <!doctype html>
        <html lang="{strings["lang"]}">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>{escape(title)}</title>
            <meta name="description" content="{escape(description)}" />
            <link rel="canonical" href="{canonical}" />
            <link rel="alternate" hreflang="en" href="{SITE_DOMAIN}/library/" />
            <link rel="alternate" hreflang="zh-CN" href="{SITE_DOMAIN}/zh/library/" />
            <link rel="alternate" hreflang="x-default" href="{SITE_DOMAIN}/library/" />
            <meta property="og:type" content="website" />
            <meta property="og:locale" content="{strings["og_locale"]}" />
            <meta property="og:title" content="{escape(title)}" />
            <meta property="og:description" content="{escape(description)}" />
            <meta property="og:url" content="{canonical}" />
            <meta property="og:image" content="{SITE_DOMAIN}/og.svg" />
            <meta name="twitter:card" content="summary_large_image" />
            <meta name="twitter:title" content="{escape(title)}" />
            <meta name="twitter:description" content="{escape(description)}" />
            <meta name="twitter:image" content="{SITE_DOMAIN}/og.svg" />
            <meta name="theme-color" content="#f4efe5" />
            <link rel="icon" href="{roots["asset_prefix"]}favicon.svg" type="image/svg+xml" />
            <link rel="stylesheet" href="{roots["asset_prefix"]}styles.css" />
          </head>
          <body>
            <div class="page-shell">
              {_render_header(locale, current="library")}

              <main>
                <section class="page-hero">
                  <p class="eyebrow">{escape(strings["eyebrow"])}</p>
                  <h1>{escape(strings["library_title"])}</h1>
                  <p class="hero-text">{escape(strings["library_description"])}</p>
                  <div class="hero-actions">
                    <a class="button" href="{strings["library_button_href"]}">
                      {escape(strings["index_primary_cta"])}
                    </a>
                  </div>
                </section>

                <section class="section-tight">
                  <div class="resource-grid">
                    {' '.join(cards)}
                  </div>
                </section>
              </main>

              {_render_footer(locale)}
            </div>
          </body>
        </html>
        """
    ).strip()


def rebuild_sitemap(publish_dir: Path, state: SiteAutomationState) -> None:
    """Rebuild the sitemap from static pages and generated article records."""

    urls = [
        {
            "loc": f"{SITE_DOMAIN}{path}",
            "priority": "1.0" if path == "/" else "0.9",
        }
        for path in STATIC_URLS
    ]
    for record in sorted(state.articles, key=lambda item: item.published_at):
        urls.append({"loc": record.url, "priority": "0.7"})

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for item in urls:
        lines.extend(
            [
                "  <url>",
                f"    <loc>{escape(item['loc'])}</loc>",
                f"    <lastmod>{date.today().isoformat()}</lastmod>",
                "    <changefreq>weekly</changefreq>",
                f"    <priority>{item['priority']}</priority>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    (publish_dir / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def rebuild_library_indexes(publish_dir: Path, state: SiteAutomationState) -> None:
    """Render the English and Chinese library hub pages."""

    en_records = [record for record in state.articles if record.locale == "en-US"]
    zh_records = [record for record in state.articles if record.locale == "zh-CN"]
    library_dir = publish_dir / "library"
    zh_library_dir = publish_dir / "zh" / "library"
    library_dir.mkdir(parents=True, exist_ok=True)
    zh_library_dir.mkdir(parents=True, exist_ok=True)
    (library_dir / "index.html").write_text(
        render_library_index_html("en-US", en_records),
        encoding="utf-8",
    )
    (zh_library_dir / "index.html").write_text(
        render_library_index_html("zh-CN", zh_records),
        encoding="utf-8",
    )


def generate_daily_site_content(
    client: Socrates,
    *,
    publish_dir: Path,
    state_path: Path = DEFAULT_STATE_PATH,
    topics_per_run: int = DEFAULT_TOPICS_PER_RUN,
    locales: tuple[str, ...] = DEFAULT_LOCALES,
    now: datetime | None = None,
) -> GenerationSummary:
    """Generate the next batch of evergreen resource pages and update the website."""

    current_time = now or datetime.now(tz=UTC)
    publish_dir.mkdir(parents=True, exist_ok=True)
    state = load_state(state_path)
    seeds = select_next_topics(state, count=topics_per_run)
    summary = GenerationSummary()

    for seed in seeds:
        bundles: list[GeneratedPageBundle] = []
        try:
            for locale in locales:
                article, review_score = generate_site_article(client, seed, locale=locale)
                relative_path = _article_relative_path(locale, seed.slug)
                record = PublishedArticleRecord(
                    seed_key=seed.key,
                    slug=seed.slug,
                    locale=locale,
                    title=_seed_title(seed, locale),
                    summary=article.summary,
                    meta_description=article.meta_description,
                    path=relative_path,
                    url=_canonical_url(relative_path),
                    cluster=_seed_cluster(seed, locale),
                    published_at=current_time.isoformat(),
                    review_score=review_score,
                    primary_keyword=_seed_keyword(seed, locale),
                )
                html = render_article_html(article, record)
                bundles.append(
                    GeneratedPageBundle(
                        locale=locale,
                        output_path=relative_path,
                        html=html,
                        record=record,
                    )
                )
        except RuntimeError:
            summary.skipped_seed_keys.append(seed.key)
            continue

        for bundle in bundles:
            target = publish_dir / bundle.output_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(bundle.html, encoding="utf-8")
            state.articles = [
                record for record in state.articles if record.path != bundle.record.path
            ]
            state.articles.append(bundle.record)
            summary.generated_pages.append(bundle.output_path)

        state.published_seed_keys.append(seed.key)
        state.published_seed_keys = sorted(set(state.published_seed_keys))
        summary.generated_seed_keys.append(seed.key)

    state.articles = sorted(
        state.articles,
        key=lambda item: (item.locale, item.published_at, item.slug),
    )
    rebuild_library_indexes(publish_dir, state)
    rebuild_sitemap(publish_dir, state)
    save_state(state_path, state)
    return summary
