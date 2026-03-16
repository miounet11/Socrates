const presets = {
  blog_post: {
    platform: "blog",
    content_type: "blog_post",
    mode: "guided",
    topic: "Why AI product messaging fails when it starts with capability",
    audience: "Product marketers at AI startups",
    goal: "Create a publishable draft with a clear point of view",
    constraints: ["Avoid generic thought leadership phrasing", "Use concrete examples"],
  },
  linkedin_long_post: {
    platform: "linkedin",
    content_type: "linkedin_long_post",
    mode: "guided",
    topic: "Most AI positioning fails because it leads with capability instead of business friction",
    audience: "Founders and GTM leads at AI startups",
    goal: "Create a LinkedIn post that feels sharp, specific, and credible",
    constraints: ["Keep paragraphs short", "Lead with a strong hook"],
  },
  value_prop: {
    platform: "web",
    content_type: "value_prop",
    mode: "guided",
    topic: "A workflow copilot for RevOps teams",
    audience: "Revenue operations leaders at mid-market SaaS companies",
    goal: "Create landing-page value proposition copy that can ship",
    constraints: ["Avoid empty efficiency claims", "Emphasize buyer pain"],
  },
  content_calendar: {
    platform: "multi-platform",
    content_type: "content_calendar",
    mode: "full",
    topic: "A 30-day content calendar for a compliance automation platform",
    audience: "Security and compliance leaders at mid-market companies",
    goal: "Create a differentiated 30-day calendar across blog, LinkedIn, and email",
    constraints: ["Balance educational and commercial intent", "Avoid repeated angles"],
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

function toYaml(payload) {
  const lines = [
    `topic: "${payload.topic}"`,
    `audience: "${payload.audience}"`,
    `goal: "${payload.goal}"`,
    `platform: "${payload.platform}"`,
    `content_type: "${payload.content_type}"`,
    "constraints:",
    ...payload.constraints.map((item) => `  - "${item}"`),
    "voice_notes:",
    '  - "Specific over abstract"',
    '  - "Credible over hypey"',
    "keywords:",
    '  - "AI messaging"',
    '  - "content strategy"',
    "include_cta: true",
    'cta_goal: "Invite the reader into a next step"',
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
  await navigator.clipboard.writeText(text);
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

