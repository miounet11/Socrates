const presets = {
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
    topic: "Most AI positioning fails because it leads with capability instead of business friction",
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
    constraints: ["Avoid inflated certainty", "Map claims to the evidence they would require"],
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
    constraints: ["Avoid inspirational cliches", "Make the core angle unmistakably differentiated"],
    voice_notes: ["Intentional", "Strategic", "Direct"],
    keywords: ["brand narrative", "positioning", "messaging"],
    cta_goal: "Move the reader toward a clearer understanding of the product thesis",
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
    'locale: "en-US"',
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
  copyCommandButton.textContent = "Copied";
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
