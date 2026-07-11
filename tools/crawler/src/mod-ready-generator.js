const fs = require("node:fs");
const path = require("node:path");

const REQUIRED_SECTIONS = [
  "角色定位",
  "原作核心要素",
  "神器设定",
  "能力关键词",
  "Stellaris 领袖职业建议",
  "可转化机制",
  "可转化事件方向",
  "可转化建筑 / 法令 / 科技方向",
  "不建议直接照搬的内容",
  "人工确认事项",
];

class ModReadyGenerator {
  generateFromCleanMarkdown(markdown) {
    const frontmatter = this.parseFrontmatter(markdown);
    const sections = this.parseSections(markdown);
    const facts = this.extractFacts(frontmatter, sections);

    const blocks = [
      this.buildFrontmatter(frontmatter),
      `# 角色定位\n\n${this.buildRolePosition(facts)}`,
      `# 原作核心要素\n\n${this.buildCoreElements(facts, sections)}`,
      `# 神器设定\n\n${this.buildArtifactSetting(facts, sections)}`,
      `# 能力关键词\n\n${this.buildAbilityKeywords(facts, sections)}`,
      `# Stellaris 领袖职业建议\n\n${this.buildLeaderSuggestions(facts, sections)}`,
      `# 可转化机制\n\n${this.buildConvertibleMechanics(facts, sections)}`,
      `# 可转化事件方向\n\n${this.buildEventDirections(facts, sections)}`,
      `# 可转化建筑 / 法令 / 科技方向\n\n${this.buildBuildEdictTechDirections(facts, sections)}`,
      `# 不建议直接照搬的内容\n\n${this.buildDoNotCopy(facts, sections)}`,
      `# 人工确认事项\n\n${this.buildManualChecks(facts, sections)}`,
    ];

    return `${blocks.join("\n\n").trim()}\n`;
  }

  parseFrontmatter(markdown) {
    const match = /^---\n([\s\S]*?)\n---/.exec(markdown);
    if (!match) {
      return {};
    }

    const data = {};
    for (const line of match[1].split(/\r?\n/)) {
      const pair = /^([A-Za-z0-9_]+):\s*(.*)$/.exec(line);
      if (!pair) {
        continue;
      }

      const key = pair[1];
      const rawValue = pair[2].trim();
      if (!rawValue || rawValue === "[]") {
        data[key] = rawValue === "[]" ? [] : "";
        continue;
      }

      try {
        data[key] = JSON.parse(rawValue);
      } catch {
        data[key] = rawValue.replace(/^"|"$/g, "");
      }
    }

    return data;
  }

  parseSections(markdown) {
    const withoutFrontmatter = markdown.replace(/^---\n[\s\S]*?\n---\n*/, "");
    const lines = withoutFrontmatter.split(/\r?\n/);
    const sections = {};
    let current = null;

    for (const line of lines) {
      const heading = /^#\s+(.+)$/.exec(line);
      if (heading) {
        current = heading[1].trim();
        sections[current] = [];
        continue;
      }

      if (current) {
        sections[current].push(line);
      }
    }

    for (const [key, value] of Object.entries(sections)) {
      sections[key] = this.cleanBlock(value.join("\n"));
    }

    return sections;
  }

  extractFacts(frontmatter, sections) {
    return {
      title: frontmatter.title || this.readListValue(sections["基本资料"], "标题"),
      rarity: frontmatter.rarity || this.readListValue(sections["基本资料"], "稀有度"),
      attribute: frontmatter.attribute || this.readListValue(sections["基本资料"], "属性"),
      className: frontmatter.class || this.readListValue(sections["基本资料"], "职业"),
      damageType: frontmatter.damage_type || this.readListValue(sections["基本资料"], "伤害类型"),
      artifact: frontmatter.artifact || this.readListValue(sections["基本资料"], "神器"),
      ability: frontmatter.ability || this.readListValue(sections["基本资料"], "能力"),
      source: frontmatter.source || ["Huiji Wiki"],
      lastSync: frontmatter.last_sync || "",
    };
  }

  buildFrontmatter(source) {
    const lines = ["---"];
    lines.push(`title: ${this.yamlScalar(source.title || "")}`);
    lines.push(`type: "mod_ready_character"`);
    lines.push("source:");
    lines.push(`  - "knowledge/characters"`);
    lines.push(`last_sync: ${this.yamlScalar(new Date().toISOString())}`);
    lines.push(`source_last_sync: ${this.yamlScalar(source.last_sync || "")}`);
    lines.push("---");
    return lines.join("\n");
  }

  buildRolePosition(facts) {
    return [
      `- 角色：${facts.title || "未知"}`,
      `- 原作定位：${[facts.rarity, facts.attribute && `${facts.attribute}属性`, facts.className, facts.damageType].filter(Boolean).join(" / ") || "未知"}`,
      `- 神器：${facts.artifact || "未知"}`,
      `- 能力：${facts.ability || "未知"}`,
    ].join("\n");
  }

  buildCoreElements(facts, sections) {
    const intro = this.limitText(sections["简介"], 700);
    const daily = this.limitText(sections["日常故事"], 900);
    const bond = this.limitText(sections["羁绊片段"], 900);
    const memory = this.limitText(sections["回忆片段"], 700);

    return this.joinNonEmpty([
      intro && `## 简介摘录\n\n${intro}`,
      daily && `## 日常故事摘录\n\n${daily}`,
      bond && `## 羁绊片段摘录\n\n${bond}`,
      memory && `## 回忆片段摘录\n\n${memory}`,
    ]);
  }

  buildArtifactSetting(facts, sections) {
    return this.joinNonEmpty([
      `- 神器名称：${facts.artifact || "未知"}`,
      sections["神器"] && `## 神器页面摘录\n\n${this.limitText(sections["神器"], 1000)}`,
      sections["神器故事"] && `## 神器故事摘录\n\n${this.limitText(sections["神器故事"], 1200)}`,
    ]);
  }

  buildAbilityKeywords(facts, sections) {
    const keywords = new Set();
    for (const value of [facts.attribute, facts.className, facts.damageType, facts.ability, facts.artifact]) {
      if (value) {
        keywords.add(value);
      }
    }

    const abilityText = sections["能力"] || "";
    for (const keyword of this.extractMechanicKeywords(abilityText)) {
      keywords.add(keyword);
    }

    const list = [...keywords].filter(Boolean);
    return list.length ? list.map((item) => `- ${item}`).join("\n") : "暂无自动提取关键词。";
  }

  buildLeaderSuggestions(facts, sections) {
    const suggestions = [];

    if (facts.className === "法师" || /法术|控制|减速|眩晕|治疗|支援/.test(`${facts.damageType}\n${sections["能力"] || ""}`)) {
      suggestions.push("- 科学家：可承载研究、异常、空间、预知、法术或神器解析相关设定。");
    }
    if (/辅助|治疗|增益|护盾|友方|支援|管理|中央庭/.test(`${facts.className}\n${sections["能力"] || ""}\n${sections["羁绊片段"] || ""}`)) {
      suggestions.push("- 行政官：可承载治理、支援、维护、资源或组织管理相关设定。");
    }
    if (/战士|坦克|射手|伤害|眩晕|穿透|攻击|敌人|战斗/.test(`${facts.className}\n${sections["能力"] || ""}`)) {
      suggestions.push("- 指挥官：可承载舰队战斗、控制、伤害、护盾或战场机动相关设定。");
    }

    if (!suggestions.length) {
      suggestions.push("- 待人工确认：clean markdown 中没有足够明确的职业转化线索。");
    }

    return suggestions.join("\n");
  }

  buildConvertibleMechanics(facts, sections) {
    const mechanics = [];
    const ability = sections["能力"] || "";
    const artifact = `${facts.artifact}\n${sections["神器"] || ""}\n${sections["神器故事"] || ""}`;

    const rules = [
      [/治疗|回复|生命值/, "治疗 / 回复 → 舰队或星球恢复、领袖辅助特质。"],
      [/护盾|格挡|防御|减伤/, "防御 / 护盾 → 舰船组件、光环或防御型领袖技能。"],
      [/眩晕|减速|控制|放逐|沉默/, "控制效果 → 敌方射速、亚光速、闪避或紧急跃迁惩罚。"],
      [/穿透|暴击|伤害|攻击|法术/, "输出关键词 → 武器伤害、穿透、暴击或舰队火力修正。"],
      [/空间|瞬移|传送|次元|移动/, "空间机动 → 跃迁、闪避、紧急撤离、星系移动事件。"],
      [/预言|命运|卡牌|塔罗|概率|运气/, "命运 / 概率 → 随机事件、抽牌式国家修正、议程或法令。"],
      [/方舟|避世|庇护|保存|生存/, "庇护 / 方舟 → 避难设施、人口保护、危机生存机制。"],
    ];

    for (const [pattern, text] of rules) {
      if (pattern.test(`${ability}\n${artifact}\n${facts.ability}`)) {
        mechanics.push(`- ${text}`);
      }
    }

    return mechanics.length ? mechanics.join("\n") : "- 暂无明确机制映射，需人工复核 clean markdown。";
  }

  buildEventDirections(facts, sections) {
    const directions = [];
    if (sections["神器故事"]) {
      directions.push("- 神器觉醒 / 神器共鸣事件：来源于 clean markdown 的神器故事。");
    }
    if (sections["日常故事"]) {
      directions.push("- 日常通讯事件：来源于 clean markdown 的日常故事。");
    }
    if (sections["羁绊片段"]) {
      directions.push("- 羁绊阶段事件：来源于 clean markdown 的羁绊片段。");
    }
    if (sections["回忆片段"]) {
      directions.push("- 回忆解锁事件：来源于 clean markdown 的回忆片段。");
    }
    if (sections["同伴评价"] && !sections["同伴评价"].includes("暂无自动解析内容")) {
      directions.push("- 同伴评价通讯：来源于 clean markdown 的同伴评价。");
    }

    return directions.length ? directions.join("\n") : "- 暂无可直接转化事件方向。";
  }

  buildBuildEdictTechDirections(facts, sections) {
    const directions = [];
    const text = `${facts.artifact}\n${facts.ability}\n${sections["能力"] || ""}\n${sections["神器"] || ""}`;

    if (/研究|解析|预言|命运|卡牌|塔罗|空间|次元/.test(text)) {
      directions.push("- 科技方向：神器解析、空间理论、命运观测或概率干涉。");
    }
    if (/庇护|方舟|治疗|回复|支援|管理|中央庭/.test(text)) {
      directions.push("- 建筑方向：神器工坊、中央庭设施、避难所、支援中枢。");
    }
    if (/抽取|命运|预言|召唤|支援|增益/.test(text)) {
      directions.push("- 法令方向：神器使支援、命运抽取、临时舰队 / 星球修正。");
    }

    return directions.length ? directions.join("\n") : "- 暂无明确建筑 / 法令 / 科技方向，需人工确认。";
  }

  buildDoNotCopy(facts, sections) {
    return [
      "- 不直接照搬原作数值，例如技能倍率、冷却时间、伤害数值。",
      "- 不直接照搬长篇剧情原文，应在事件脚本中改写为 Stellaris 语境。",
      "- 不直接下载或内嵌图片资源；图片处理属于后续 Milestone。",
      "- 不把同伴评价自动当作角色关系，仍需人工确认。",
    ].join("\n");
  }

  buildManualChecks(facts, sections) {
    const checks = [];
    checks.push("- 人工确认领袖职业：科学家 / 行政官 / 指挥官是否都适配。");
    checks.push("- 人工确认神器技能能否转化为可平衡的 Stellaris modifier。");
    checks.push("- 人工确认事件文本是否需要避开原文复刻。");
    if (!facts.ability) {
      checks.push("- clean markdown 未提取到 ability，需要人工补充能力关键词。");
    }
    if (!sections["同伴评价"] || sections["同伴评价"].includes("暂无自动解析内容")) {
      checks.push("- 同伴评价为空或未解析，需要人工确认。");
    }

    return checks.join("\n");
  }

  extractMechanicKeywords(text) {
    const keywords = [];
    const candidates = ["治疗", "回复", "护盾", "眩晕", "减速", "穿透", "闪避", "伤害", "控制", "空间", "瞬移", "命运", "概率", "支援", "友方", "敌方"];
    for (const keyword of candidates) {
      if (text.includes(keyword)) {
        keywords.push(keyword);
      }
    }
    return keywords;
  }

  readListValue(text, label) {
    const match = new RegExp(`^- ${label}：(.+)$`, "m").exec(text || "");
    return match ? match[1].trim() : "";
  }

  cleanBlock(text) {
    return String(text || "")
      .replace(/\r\n/g, "\n")
      .replace(/回顾\s*$/gm, "")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  joinNonEmpty(items) {
    const filtered = items.filter((item) => item && item.trim());
    return filtered.length ? filtered.join("\n\n") : "暂无可整理内容。";
  }

  limitText(text, maxLength) {
    const clean = this.cleanBlock(text);
    if (clean.length <= maxLength) {
      return clean;
    }

    return `${clean.slice(0, maxLength).trim()}\n\n……`;
  }

  yamlScalar(value) {
    return JSON.stringify(String(value ?? ""));
  }
}

module.exports = {
  ModReadyGenerator,
  REQUIRED_SECTIONS,
};
