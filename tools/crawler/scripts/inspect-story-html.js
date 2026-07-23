const fs = require("node:fs");
const path = require("node:path");
const { BrowserManager } = require("../src/browser-manager");
const { WikiClient } = require("../src/wiki-client");
const { StoryParser } = require("../src/story-parser");

const HOME_URL = "https://f7d.huijiwiki.com/wiki/%E9%A6%96%E9%A1%B5";

// 仅用于人工核对剧情页面的原始 HTML 结构；不写入 raw、knowledge 或索引文件。
// 当页面使用非 nav-tabs 的折叠、模板或嵌套标签承载选择树时，可借此定位真实结构。
const commandArgs = process.argv.slice(2);
// 摘要模式避免大型剧情页输出数十万字符的调试结果；需要完整结构时可省略该参数。
const summaryMode = commandArgs.includes("--summary");
const title = commandArgs.filter((argument) => argument !== "--summary").join(" ").trim();

function readAttribute(tag, attributeName) {
  const escapedName = String(attributeName).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(`\\b${escapedName}\\s*=\\s*(?:\"([^\"]*)\"|'([^']*)'|([^\\s>]+))`, "i");
  const match = pattern.exec(String(tag || ""));
  return match ? match[1] || match[2] || match[3] || "" : "";
}

function compact(value, limit = 360) {
  const normalized = String(value || "")
    .replace(/\s+/g, " ")
    .replace(/&nbsp;/gi, " ")
    .trim();
  return normalized.length > limit ? `${normalized.slice(0, limit)}…` : normalized;
}

function stripTags(value) {
  return String(value || "")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/gi, " ")
    .replace(/&(?:quot|ldquo|rdquo);/gi, "\"")
    .replace(/&(?:#39|apos);/gi, "'")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/\s+/g, " ")
    .trim();
}

function findMatchingTag(html, startIndex, tagName) {
  const pattern = new RegExp(`<\\/?${tagName}\\b[^>]*>`, "gi");
  pattern.lastIndex = startIndex;
  let depth = 0;
  let match;

  while ((match = pattern.exec(html))) {
    if (/^<\//.test(match[0])) {
      depth -= 1;
      if (depth === 0) {
        return { start: startIndex, end: pattern.lastIndex };
      }
      continue;
    }
    if (!/\/>$/.test(match[0])) {
      depth += 1;
    }
  }
  return null;
}

function findStructuralCandidates(html) {
  const candidates = [];
  const tagPattern = /<(ul|ol|div|table|section|details|input|label|a)\b[^>]*>/gi;
  let match;

  while ((match = tagPattern.exec(html))) {
    const tag = match[0];
    const className = readAttribute(tag, "class");
    const role = readAttribute(tag, "role");
    const dataToggle = readAttribute(tag, "data-toggle") || readAttribute(tag, "data-bs-toggle");
    const href = readAttribute(tag, "href");
    const id = readAttribute(tag, "id");
    const name = readAttribute(tag, "name");
    const type = readAttribute(tag, "type");
    const structuralValue = [className, role, dataToggle, href, id, name, type].join(" ");

    if (!/(?:tab|choice|select|branch|collaps|condition|route|story|剧情战|结局)/i.test(structuralValue)) {
      continue;
    }

    const tagName = match[1].toLowerCase();
    const bounds = /^(?:ul|ol|div|table|section|details)$/i.test(tagName)
      ? findMatchingTag(html, match.index, tagName)
      : null;
    const fragment = bounds ? html.slice(bounds.start, bounds.end) : html.slice(match.index, match.index + 1200);
    const text = stripTags(fragment);

    candidates.push({
      index: match.index,
      tag: tagName,
      className,
      role,
      dataToggle,
      href,
      id,
      name,
      type,
      text: compact(text),
    });
  }

  return candidates;
}

function findKeywordContexts(html) {
  const keywords = ["剧情战胜利", "剧情战失败", "选择", "选项", "结局", "胜利", "失败", "黑核"];
  const contexts = [];

  for (const keyword of keywords) {
    let offset = 0;
    let count = 0;
    while (count < 12) {
      const index = html.indexOf(keyword, offset);
      if (index < 0) {
        break;
      }
      contexts.push({
        keyword,
        index,
        html: compact(html.slice(Math.max(0, index - 300), index + 900), 1100),
      });
      offset = index + keyword.length;
      count += 1;
    }
  }

  return contexts;
}

function safeFilename(value) {
  return String(value || "untitled").replace(/[<>:"/\\\\|?*\u0000-\u001F]/g, "_").trim();
}

async function main() {
  if (!title) {
    throw new Error("请提供要检查的 Wiki 剧情页面标题。");
  }

  const browser = new BrowserManager({
    // 复用已通过灰机 Wiki 验证的专用会话，确保可读取与采集器一致的页面 HTML。
    profileDir: path.resolve(__dirname, "..", ".playwright-profile", "f7d-chrome"),
    artifactDir: path.resolve(__dirname, "..", "artifacts"),
    headless: false,
  });

  try {
    await browser.start();
    await browser.goto(HOME_URL);
    await browser.wait_ready({ timeout: 60_000, settleMs: 800 });

    const page = await new WikiClient(browser).get_page(title);
    const candidates = findStructuralCandidates(page.html);
    const contexts = findKeywordContexts(page.html);
    const parserExtraction = new StoryParser().extractTabChoiceTrees(page.html);
    const parsedChoiceTrees = parserExtraction.choiceTrees.map((tree) => ({
      placeholder: tree.placeholder,
      options: tree.options,
      branch_type: tree.branch_type,
      repeatable: tree.repeatable,
      branch_previews: tree.branches.map((branch) => ({
        option: branch.option,
        response_preview: compact(branch.response, 260),
      })),
    }));

    const report = {
      title: page.title,
      source_url: page.sourceUrl,
      html_length: page.html.length,
      structural_candidate_count: candidates.length,
      keyword_context_count: contexts.length,
      parser_choice_tree_count: parsedChoiceTrees.length,
      parser_choice_trees: parsedChoiceTrees,
      structural_candidates: summaryMode
        ? candidates
            .filter((candidate) => candidate.tag === "ul" || candidate.role === "tabpanel")
            .slice(0, 24)
        : candidates,
      keyword_contexts: summaryMode
        ? contexts.slice(0, 24)
        : contexts,
    };

    // 调试报告仅保存到 crawler 的 artifacts；它不参与知识库、raw 或正式索引。
    const reportDir = path.resolve(__dirname, "..", "artifacts", "story-html-inspection");
    fs.mkdirSync(reportDir, { recursive: true });
    const reportPath = path.join(reportDir, `${safeFilename(page.title)}.json`);
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf8");
    console.log(`结构检查报告：${reportPath}`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error("剧情 HTML 结构检查失败：", error);
  process.exitCode = 1;
});
