const locale = document.documentElement.lang.startsWith("zh") ? "zh-CN" : "en-US";

const localeContent = {
  "en-US": {
    copiedLabel: "Copied",
    localeCode: "en-US",
    presets: {
      blog_post: {
        platform: "blog",
        content_type: "blog_post",
        mode: "guided",
        topic: "Why AI product messaging fails when it starts with capability",
        audience: "Product marketers at AI startups",
        goal: "Create a publishable draft with a clear point of view",
        length_hint: "1200-1600 words",
        constraints: ["Avoid generic thought leadership phrasing", "Use concrete examples"],
        voice_notes: ["Specific", "Credible", "Sharp"],
        keywords: ["AI messaging", "content strategy", "B2B SaaS"],
        cta_goal: "Invite the reader into a next step",
      },
      linkedin_long_post: {
        platform: "linkedin",
        content_type: "linkedin_long_post",
        mode: "guided",
        topic:
          "Most AI positioning fails because it leads with capability instead of business friction",
        audience: "Founders and GTM leads at AI startups",
        goal: "Create a LinkedIn post that feels sharp, specific, and credible",
        length_hint: "700-900 words",
        constraints: ["Keep paragraphs short", "Lead with a strong hook"],
        voice_notes: ["Operator tone", "Clear point of view"],
        keywords: ["AI positioning", "go-to-market", "LinkedIn"],
        cta_goal: "Drive comments or a qualified conversation",
      },
      value_prop: {
        platform: "web",
        content_type: "value_prop",
        mode: "guided",
        topic: "A workflow copilot for RevOps teams",
        audience: "Revenue operations leaders at mid-market SaaS companies",
        goal: "Create landing-page value proposition copy that can ship",
        length_hint: "Short landing page section",
        constraints: ["Avoid empty efficiency claims", "Emphasize buyer pain"],
        voice_notes: ["Confident", "Buyer-aware"],
        keywords: ["RevOps", "workflow copilot", "landing page"],
        cta_goal: "Push the reader toward a demo or product evaluation",
      },
      industry_analysis: {
        platform: "blog",
        content_type: "industry_analysis",
        mode: "full",
        topic: "What buyers actually expect from AI workflow products in 2026",
        audience: "Product marketers and founders in B2B AI software",
        goal: "Create a publishable analysis with differentiated conclusions and a credible tone",
        length_hint: "1800-2500 words",
        constraints: [
          "Avoid inflated certainty",
          "Map claims to the evidence they would require",
        ],
        voice_notes: ["Analytical", "Measured", "Specific"],
        keywords: ["industry analysis", "AI software", "buyer expectations"],
        cta_goal: "Prompt the reader to evaluate their own category assumptions",
      },
      content_calendar: {
        platform: "multi-platform",
        content_type: "content_calendar",
        mode: "full",
        topic: "A 30-day content calendar for a compliance automation platform",
        audience: "Security and compliance leaders at mid-market companies",
        goal: "Create a differentiated 30-day calendar across blog, LinkedIn, and email",
        length_hint: "30 entries",
        constraints: ["Balance educational and commercial intent", "Avoid repeated angles"],
        voice_notes: ["Expert", "Practical"],
        keywords: ["content calendar", "compliance automation", "editorial planning"],
        cta_goal: "Create a series that moves readers toward qualified demand",
      },
      brand_narrative: {
        platform: "web",
        content_type: "brand_narrative",
        mode: "full",
        topic: "Why workflow software should feel like decision support, not dashboard sprawl",
        audience: "Operators evaluating modern workflow products",
        goal: "Create a clear brand narrative with a distinct thesis and controlled tone",
        length_hint: "900-1400 words",
        constraints: [
          "Avoid inspirational cliches",
          "Make the core angle unmistakably differentiated",
        ],
        voice_notes: ["Intentional", "Strategic", "Direct"],
        keywords: ["brand narrative", "positioning", "messaging"],
        cta_goal: "Move the reader toward a clearer understanding of the product thesis",
      },
    },
  },
  "zh-CN": {
    copiedLabel: "已复制",
    localeCode: "zh-CN",
    presets: {
      blog_post: {
        platform: "blog",
        content_type: "blog_post",
        mode: "guided",
        topic: "为什么 AI 产品营销一上来就讲能力，往往会让内容失去说服力",
        audience: "AI 创业公司的产品营销负责人",
        goal: "产出一篇可直接发布、观点鲜明的博客初稿",
        length_hint: "1200-1600 words",
        constraints: ["避免空泛的行业黑话", "尽量给出具体场景或例子"],
        voice_notes: ["具体", "可信", "有判断力"],
        keywords: ["AI 营销", "内容策略", "B2B SaaS"],
        cta_goal: "引导读者进入下一步沟通或行动",
      },
      linkedin_long_post: {
        platform: "linkedin",
        content_type: "linkedin_long_post",
        mode: "guided",
        topic: "多数 AI 定位失败，不是能力不够，而是把业务摩擦讲得太晚",
        audience: "AI 创业公司的创始人和增长负责人",
        goal: "产出一条适合 LinkedIn 发布的长帖，开头有钩子，结尾有力度",
        length_hint: "700-900 words",
        constraints: ["段落保持简短", "开头先给观点或冲突，不要先铺背景"],
        voice_notes: ["像一线操盘者", "有明确立场"],
        keywords: ["AI 定位", "GTM", "LinkedIn"],
        cta_goal: "促使读者评论、私信，或继续讨论",
      },
      value_prop: {
        platform: "web",
        content_type: "value_prop",
        mode: "guided",
        topic: "一款面向 RevOps 团队的工作流 Copilot",
        audience: "正在评估自动化平台的中型 SaaS 企业 RevOps 负责人",
        goal: "生成一版可以直接进入落地页的价值主张文案",
        length_hint: "Short landing page section",
        constraints: ["避免空洞的效率承诺", "优先写买家痛点和可信信号"],
        voice_notes: ["自信", "贴近买家"],
        keywords: ["RevOps", "工作流 Copilot", "落地页"],
        cta_goal: "推动读者进入演示申请或产品评估",
      },
      industry_analysis: {
        platform: "blog",
        content_type: "industry_analysis",
        mode: "full",
        topic: "2026 年买家对 AI 工作流产品的真正期待是什么",
        audience: "B2B AI 软件公司的创始人和产品营销团队",
        goal: "产出一篇结构完整、结论有区分度的行业分析文章",
        length_hint: "1800-2500 words",
        constraints: ["避免夸大确定性", "每个关键判断都说明需要什么证据支撑"],
        voice_notes: ["分析型", "克制", "具体"],
        keywords: ["行业分析", "AI 软件", "买家预期"],
        cta_goal: "让读者重新审视自己的类别判断和叙事方式",
      },
      content_calendar: {
        platform: "multi-platform",
        content_type: "content_calendar",
        mode: "full",
        topic: "为合规自动化平台设计一份 30 天内容日历",
        audience: "中型企业中的安全与合规负责人",
        goal: "规划一套覆盖博客、LinkedIn 和邮件的差异化 30 天内容安排",
        length_hint: "30 entries",
        constraints: ["兼顾教育价值与商业意图", "避免连续几天角度重复"],
        voice_notes: ["专业", "务实"],
        keywords: ["内容日历", "合规自动化", "编辑规划"],
        cta_goal: "把内容计划真正转化为可执行的增长动作",
      },
      brand_narrative: {
        platform: "web",
        content_type: "brand_narrative",
        mode: "full",
        topic: "为什么好的工作流软件应该像决策支持，而不是另一个仪表盘堆栈",
        audience: "正在评估现代工作流产品的业务运营团队",
        goal: "生成一版清晰、有辨识度的品牌叙事初稿",
        length_hint: "900-1400 words",
        constraints: ["避免空泛的品牌口号", "核心角度必须足够清晰且可区分"],
        voice_notes: ["克制", "战略感", "直接"],
        keywords: ["品牌叙事", "定位", "信息表达"],
        cta_goal: "帮助读者快速理解产品主张并产生继续了解的意愿",
      },
    },
  },
};

const presetInput = document.querySelector("#preset");
const topicInput = document.querySelector("#topic");
const audienceInput = document.querySelector("#audience");
const goalInput = document.querySelector("#goal");
const yamlOutput = document.querySelector("#yaml-output");
const commandOutput = document.querySelector("#command-output");
const modeOutput = document.querySelector("#mode-output");
const copyCommandButton = document.querySelector("#copy-command");

if (
  !presetInput ||
  !topicInput ||
  !audienceInput ||
  !goalInput ||
  !yamlOutput ||
  !commandOutput ||
  !modeOutput ||
  !copyCommandButton
) {
  // This script is reused across locales and only activates on planner pages.
} else {
  const content = localeContent[locale];
  const presets = content.presets;

  function quote(value) {
    return `"${String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
  }

  function yamlList(key, values) {
    if (!values.length) {
      return `${key}: []`;
    }

    return [`${key}:`, ...values.map((item) => `  - ${quote(item)}`)].join("\n");
  }

  function toYaml(payload) {
    const lines = [
      `topic: ${quote(payload.topic)}`,
      `audience: ${quote(payload.audience)}`,
      `goal: ${quote(payload.goal)}`,
      `platform: ${quote(payload.platform)}`,
      `content_type: ${quote(payload.content_type)}`,
      yamlList("constraints", payload.constraints),
      yamlList("voice_notes", payload.voice_notes),
      yamlList("keywords", payload.keywords),
      `length_hint: ${quote(payload.length_hint)}`,
      `locale: ${quote(content.localeCode)}`,
      "include_cta: true",
      `cta_goal: ${quote(payload.cta_goal)}`,
    ];
    return lines.join("\n");
  }

  function render() {
    const preset = presets[presetInput.value];
    const payload = {
      ...preset,
      topic: topicInput.value.trim(),
      audience: audienceInput.value.trim(),
      goal: goalInput.value.trim(),
    };

    modeOutput.textContent = payload.mode;
    yamlOutput.textContent = toYaml(payload);
    commandOutput.textContent =
      `socrates generate request.yaml --mode ${payload.mode} --format markdown`;
  }

  function applyPreset() {
    const preset = presets[presetInput.value];
    topicInput.value = preset.topic;
    audienceInput.value = preset.audience;
    goalInput.value = preset.goal;
    render();
  }

  async function copyCommand() {
    const text = commandOutput.textContent ?? "";
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "readonly");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
    } catch (_error) {
      return;
    }

    const original = copyCommandButton.textContent;
    copyCommandButton.textContent = content.copiedLabel;
    setTimeout(() => {
      copyCommandButton.textContent = original;
    }, 1200);
  }

  presetInput.addEventListener("change", applyPreset);
  topicInput.addEventListener("input", render);
  audienceInput.addEventListener("input", render);
  goalInput.addEventListener("input", render);
  copyCommandButton.addEventListener("click", copyCommand);

  render();
}
