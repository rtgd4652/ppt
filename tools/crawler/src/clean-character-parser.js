const { Parser } = require("./parser");

class CleanCharacterParser {
  constructor() {
    // 复用通用 HTML→Markdown 与基础抽取工具，但本类只输出干净知识库格式。
    this.rawParser = new Parser();
  }

  parseCharacter(page, rawResult) {
    const plainMarkdown = rawResult?.plainMarkdown || this.rawParser.htmlToMarkdown(page.html || "");
    const sections = this.rawParser.extractSections(plainMarkdown);
    const images = this.classifyImages(rawResult?.imageIndex || this.rawParser.extractImages(page.html || "", page.imageInfo || []));
    const facts = this.extractFacts(page, plainMarkdown, sections);

    const frontmatter = this.buildFrontmatter({
      title: page.title,
      type: "character",
      source: ["Huiji Wiki"],
      last_sync: page.lastSync || "",
      rarity: facts.rarity,
      attribute: facts.attribute,
      className: facts.className,
      damage_type: facts.damage_type,
      artifact: facts.artifact,
      ability: facts.ability,
      related_characters: [],
    });

    const markdown = [
      frontmatter,
      `# 简介\n\n${this.buildIntro(page, facts)}`,
      `# 基本资料\n\n${this.buildBasicInfo(page, facts)}`,
      `# 神器\n\n${this.buildArtifactSection(sections, facts) || "暂无自动解析内容。"}`,
      `# 神器故事\n\n${this.buildArtifactStory(sections) || "暂无自动解析内容。"}`,
      `# 能力\n\n${this.pickSections(sections, ["被动技能", "主动技能", "终极技能", "能力"], ["神器技能"]) || "暂无自动解析内容。"}`,
      `# 日常故事\n\n${this.buildDailyStories(sections) || "暂无自动解析内容。"}`,
      `# 羁绊片段\n\n${this.buildBondFragments(sections) || "暂无自动解析内容。"}`,
      `# 回忆片段\n\n${this.buildMemoryFragments(sections) || "暂无自动解析内容。"}`,
      `# 同伴评价\n\n${this.buildCompanionReviews(sections) || "暂无自动解析内容。"}`,
      `# MOD 可用设定摘录\n\n${this.buildModExcerpt(page, facts)}`,
    ].join("\n\n");

    return {
      markdown: `${markdown.trim()}\n`,
      imageIndex: images,
      facts,
    };
  }

  extractFacts(page, markdown, sections) {
    const categoryText = (page.categories || []).join(" ");
    const infoText = [
      this.sectionContent(sections, ["情报"]),
      this.sectionContent(sections, ["基础档案"]),
      this.sectionContent(sections, ["进阶档案"]),
      this.sectionContent(sections, ["高阶档案"]),
      markdown.slice(0, 5000),
    ].join("\n");

    return {
      rarity: this.pickRarity(categoryText, infoText),
      attribute: this.pickFromCategory(page.categories || [], ["巧", "刚", "灵"], "属性"),
      className: this.pickClass(page.categories || [], infoText),
      damage_type: this.pickDamageType(page.categories || [], infoText),
      artifact: this.pickNextValue(infoText, ["神器", "神器名称", "神器名"]) || this.pickField(infoText, ["神器", "神器名称", "神器名"]) || this.pickArtifactFromSections(sections),
      ability: this.pickAbility(infoText),
    };
  }

  pickRarity(categoryText, infoText) {
    const combined = `${categoryText}\n${infoText}`;
    const match = /([SABC]级)/.exec(combined);
    return match ? match[1] : "";
  }

  pickFromCategory(categories, values, suffix) {
    for (const category of categories) {
      for (const value of values) {
        if (category.includes(value) && (!suffix || category.includes(suffix))) {
          return value;
        }
      }
    }

    return "";
  }

  pickClass(categories, infoText) {
    const classes = ["战士", "坦克", "射手", "法师", "辅助", "影袭"];
    for (const category of categories) {
      for (const item of classes) {
        if (category.includes(item)) {
          return item;
        }
      }
    }

    const match = new RegExp(`(${classes.join("|")})`).exec(infoText);
    return match ? match[1] : "";
  }

  pickDamageType(categories, infoText) {
    for (const category of categories) {
      if (category.includes("法术攻击")) {
        return "法术攻击";
      }
      if (category.includes("物理攻击")) {
        return "物理攻击";
      }
    }

    const match = /(法术攻击|物理攻击)/.exec(infoText);
    return match ? match[1] : "";
  }

  pickField(text, labels) {
    for (const label of labels) {
      const patterns = [
        new RegExp(`${label}\\s*[：:]\\s*([^\\n|]+)`),
        new RegExp(`${label}\\s*\\|\\s*([^\\n|]+)`),
      ];

      for (const pattern of patterns) {
        const match = pattern.exec(text);
        if (match) {
          return this.cleanInline(match[1]);
        }
      }
    }

    return "";
  }

  pickNextValue(text, labels) {
    const lines = this.usefulLines(text);

    for (let index = 0; index < lines.length; index += 1) {
      const line = lines[index];
      if (!labels.some((label) => line === label || line.endsWith(` ${label}`))) {
        continue;
      }

      const value = lines[index + 1] || "";
      if (value && !labels.includes(value)) {
        return this.cleanInline(value);
      }
    }

    return "";
  }

  pickAbility(infoText) {
    const value =
      this.pickNextValue(infoText, ["神器使能力"]) ||
      this.pickField(infoText, ["神器使能力"]) ||
      this.pickNextValue(infoText, ["能力"]) ||
      this.pickField(infoText, ["能力"]);

    if (!value || /神器使能力|能力$|才能$|资质$|获得途径/.test(value)) {
      return "";
    }

    return value;
  }

  pickArtifactFromSections(sections) {
    const artifact = this.sectionContent(sections, ["神器"]);
    const line = this.usefulLines(artifact).find((item) => /・|·|方舟|神器/.test(item));
    return line ? this.cleanInline(line).slice(0, 80) : "";
  }

  buildIntro(page, facts) {
    const parts = [];
    parts.push(`${page.title}是《永远的7日之都》中的神器使角色。`);

    const tags = [
      facts.rarity,
      facts.attribute && `${facts.attribute}属性`,
      facts.className,
      facts.damage_type,
    ].filter(Boolean);

    if (tags.length) {
      parts.push(`当前自动解析到的基础定位为：${tags.join(" / ")}。`);
    }
    if (facts.artifact) {
      parts.push(`其神器为「${facts.artifact}」。`);
    }
    parts.push("本条目由灰机 Wiki 页面自动采集并清洗，后续可继续由人工补充剧情摘要与 MOD 设定。");

    return parts.join("\n\n");
  }

  buildArtifactSection(sections, facts) {
    const blocks = [];
    if (facts.artifact) {
      blocks.push(`- 神器：${facts.artifact}`);
    }

    const artifact = this.pickSections(sections, ["神器", "神器技能"], ["神器故事", "羁绊影装", "突破影装"]);
    if (artifact) {
      blocks.push(artifact);
    }

    return blocks.join("\n\n").trim();
  }

  buildArtifactStory(sections) {
    const direct = this.pickSections(sections, ["神器故事", "神器传说", "神器档案"]);
    if (direct) {
      return direct;
    }

    const advanced = this.sectionContent(sections, ["进阶档案"]);
    return this.extractLabeledFragments(advanced, ["神器故事"]);
  }

  buildBondFragments(sections) {
    const direct = this.pickSections(sections, ["羁绊片段"], ["羁绊影装"]);
    if (direct) {
      return direct;
    }

    const advanced = this.sectionContent(sections, ["高阶档案", "羁绊"]);
    return this.extractLabeledFragments(advanced, ["羁绊片段"]);
  }

  buildDailyStories(sections) {
    const direct = this.pickSections(sections, ["日常故事", "人物故事"], ["神器故事", "羁绊片段"]);
    if (direct) {
      return direct;
    }

    const advanced = this.sectionContent(sections, ["进阶档案"]);
    return this.extractLabeledFragments(advanced, ["日常故事"]);
  }

  buildMemoryFragments(sections) {
    const direct = this.pickSections(sections, ["回忆片段"]);
    if (direct) {
      return this.cleanMemoryText(direct);
    }

    const advanced = this.sectionContent(sections, ["高阶档案", "回忆"]);
    return this.extractLabeledFragments(advanced, ["回忆片段"]);
  }

  buildCompanionReviews(sections) {
    const text = [
      this.sectionContent(sections, ["进阶档案"]),
      this.sectionContent(sections, ["同伴评价"]),
      this.sectionContent(sections, ["评价"]),
    ].join("\n");

    const lines = this.usefulLines(text);
    const start = lines.findIndex((line) => line === "同伴评价" || line.endsWith(" 同伴评价"));
    if (start < 0) {
      return "";
    }

    const reviews = [];
    for (let index = start + 1; index < lines.length; index += 1) {
      const speaker = lines[index];
      if (this.looksLikeNextTableLabel(speaker)) {
        break;
      }
      if (!this.looksLikeSpeakerName(speaker)) {
        continue;
      }

      const body = [];
      for (let cursor = index + 1; cursor < lines.length; cursor += 1) {
        const line = lines[cursor];
        if (this.looksLikeNextTableLabel(line) || this.looksLikeSpeakerName(line)) {
          break;
        }
        body.push(line);
      }

      const content = this.cleanBlock(body.join("\n"));
      if (content) {
        reviews.push(`- ${speaker}：${content}`);
      }
    }

    return reviews.join("\n");
  }

  buildBasicInfo(page, facts) {
    const lines = [
      `- 标题：${page.title}`,
      `- 稀有度：${facts.rarity || "未知"}`,
      `- 属性：${facts.attribute || "未知"}`,
      `- 职业：${facts.className || "未知"}`,
      `- 伤害类型：${facts.damage_type || "未知"}`,
      `- 神器：${facts.artifact || "未知"}`,
      `- 能力：${facts.ability || "未知"}`,
      `- 来源页面：${page.sourceUrl || "未知"}`,
    ];

    return lines.join("\n");
  }

  buildModExcerpt(page, facts) {
    const lines = [
      `- 角色定位：${[facts.rarity, facts.attribute && `${facts.attribute}属性`, facts.className, facts.damage_type].filter(Boolean).join(" / ") || "待整理"}`,
      `- 神器设定：${facts.artifact || "待整理"}`,
      `- 能力关键词：${facts.ability || "待整理"}`,
      "- 相关角色：暂不自动提取，等待人工确认。",
      "- MOD 用途建议：可作为领袖特质、职业技能、神器建筑或事件文本的设定来源。",
    ];

    return lines.join("\n");
  }

  pickSections(sections, includeKeywords, excludeKeywords = []) {
    const picked = sections.filter((section) => {
      const included = includeKeywords.some((keyword) => section.title.includes(keyword));
      const excluded = excludeKeywords.some((keyword) => section.title.includes(keyword));
      return included && !excluded;
    });

    return picked
      .map((section) => ({
        title: section.title,
        content: this.limitText(this.cleanBlock(section.content), 2500),
      }))
      .filter((section) => section.content.trim())
      .map((section) => `## ${section.title}\n\n${section.content}`)
      .join("\n\n")
      .trim();
  }

  extractLabeledFragments(text, labelPrefixes) {
    const lines = this.usefulLines(text);
    const fragments = [];

    for (let index = 0; index < lines.length; index += 1) {
      const label = lines[index];
      if (!labelPrefixes.some((prefix) => label.startsWith(prefix))) {
        continue;
      }

      const body = [];
      for (let cursor = index + 1; cursor < lines.length; cursor += 1) {
        const line = lines[cursor];
        if (labelPrefixes.some((prefix) => line.startsWith(prefix)) || this.looksLikeNextTableLabel(line)) {
          break;
        }
        body.push(line);
      }

      const content = this.cleanBlock(body.join("\n"));
      if (content) {
        fragments.push(`## ${label}\n\n${this.limitText(content, 1800)}`);
      }
    }

    return fragments.join("\n\n").trim();
  }

  sectionContent(sections, keywords) {
    return sections
      .filter((section) => keywords.some((keyword) => section.title.includes(keyword)))
      .map((section) => section.content)
      .join("\n");
  }

  classifyImages(images) {
    const buckets = {
      portraits: [],
      illustrations: [],
      skins: [],
      icons: [],
      voice: [],
      other: [],
    };

    for (const image of images || []) {
      const normalized = {
        name: image.name || "",
        url: image.url || "",
        file_page: image.file_page || "",
        width: image.width || null,
        height: image.height || null,
        mime: image.mime || "",
      };

      buckets[this.classifyImage(normalized)].push(normalized);
    }

    return buckets;
  }

  classifyImage(image) {
    const name = image.name.toLowerCase();
    const url = image.url.toLowerCase();
    const text = `${name} ${url}`;

    if (/voice|语音|声音|audio|\.ogg|\.mp3|\.wav/.test(text)) {
      return "voice";
    }
    if (/icon|头像|技能|skill|rare|type|item|badge/.test(text)) {
      return "icons";
    }
    if (/skin|时装|觉醒|泳装|礼服|装束|衣装/.test(text)) {
      return "skins";
    }
    if (/illustration|立绘|char_illustration|cut|cg|海报/.test(text)) {
      return "illustrations";
    }
    if (/portrait|face|角色|char/.test(text)) {
      return "portraits";
    }

    return "other";
  }

  buildFrontmatter(data) {
    const lines = ["---"];
    lines.push(`title: ${this.yamlScalar(data.title)}`);
    lines.push(`type: ${this.yamlScalar(data.type)}`);
    lines.push("source:");
    for (const source of data.source || []) {
      lines.push(`  - ${this.yamlScalar(source)}`);
    }
    lines.push(`last_sync: ${this.yamlScalar(data.last_sync)}`);
    lines.push(`rarity: ${this.yamlScalar(data.rarity)}`);
    lines.push(`attribute: ${this.yamlScalar(data.attribute)}`);
    lines.push(`class: ${this.yamlScalar(data.className)}`);
    lines.push(`damage_type: ${this.yamlScalar(data.damage_type)}`);
    lines.push(`artifact: ${this.yamlScalar(data.artifact)}`);
    lines.push(`ability: ${this.yamlScalar(data.ability)}`);
    lines.push("related_characters: []");
    lines.push("---");
    return lines.join("\n");
  }

  cleanBlock(text) {
    return String(text || "")
      .replace(/\u00a0/g, " ")
      .replace(/[ \t]+/g, " ")
      .replace(/\n{3,}/g, "\n\n")
      .split(/\r?\n/)
      .map((line) => this.cleanInline(line))
      .filter((line) => !this.isNoiseLine(line))
      .filter((line, index, lines) => line || lines[index - 1])
      .join("\n")
      .trim();
  }

  cleanInline(text) {
    return String(text || "")
      .replace(/\s+/g, " ")
      .replace(/\|+/g, " | ")
      .replace(/^[|：:\-\s]+/, "")
      .replace(/[|：:\-\s]+$/, "")
      .trim();
  }

  yamlScalar(value) {
    return JSON.stringify(String(value ?? ""));
  }

  limitText(text, maxLength) {
    const clean = String(text || "").trim();
    if (clean.length <= maxLength) {
      return clean;
    }

    return `${clean.slice(0, maxLength).trim()}\n\n……`;
  }

  usefulLines(text) {
    return String(text || "")
      .split(/\r?\n/)
      .map((line) => this.normalizeLine(line))
      .filter((line) => line && !this.isNoiseLine(line));
  }

  isNoiseLine(line) {
    const isolatedResidualWords = new Set([
      "能力",
      "回忆",
      "技能",
      "情报",
      "描述",
      "等级",
      "条件",
      "材料",
      "生命值",
      "攻击力",
      "神器技能",
    ]);

    return (
      !line ||
      line === "|" ||
      isolatedResidualWords.has(line) ||
      /\.(png|jpg|jpeg|gif|webp|ogg|mp3|wav)$/i.test(line) ||
      /\b(rare|char illustration|char portrait|artifact icon)\b/i.test(line)
    );
  }

  looksLikeNextTableLabel(line) {
    return /^(喜欢的东西|讨厌的东西|神器|神器使能力|神器故事\d*|日常故事\d*|羁绊片段\d*|回忆片段\d*|同伴评价|条件|材料|生命值|攻击力)$/.test(line);
  }

  looksLikeSpeakerName(line) {
    return (
      /^[\u4e00-\u9fa5A-Za-z0-9「」·・]{1,12}$/.test(line) &&
      !this.looksLikeNextTableLabel(line) &&
      !/^(等级|描述|觉醒|条件|材料|生命值|攻击力|神器技能|被动技能|主动技能|终极技能)$/.test(line)
    );
  }

  normalizeLine(line) {
    const clean = this.cleanInline(line);

    const iconLabel = /(?:Icon|Dialogue icon|Link Icon)[^|\n]*?\.(?:png|jpg|jpeg|gif|webp)\s+(.+)$/i.exec(clean);
    if (iconLabel) {
      return this.cleanInline(iconLabel[1]);
    }

    return clean;
  }

  cleanMemoryText(text) {
    return String(text || "")
      .split(/\r?\n/)
      .map((line) => this.stripMemoryReviewSuffix(line))
      .join("\n")
      .trim();
  }

  stripMemoryReviewSuffix(line) {
    return String(line || "").replace(/回顾\s*$/g, "").trim();
  }
}

module.exports = {
  CleanCharacterParser,
};
