class Parser {
  // Parser 只做 HTML / 页面数据到 Markdown 的转换，不联网、不调用 Browser、不调用 API。
  parseCharacter(page) {
    const plainMarkdown = this.htmlToMarkdown(page.html);
    const images = this.extractImages(page.html, page.imageInfo || []);
    const sections = this.extractSections(plainMarkdown);

    const frontmatter = this.buildFrontmatter({
      title: page.title,
      type: "character",
      source: ["Huiji Wiki"],
      last_sync: page.lastSync || "",
      aliases: page.aliases || [],
      category: page.categories || [],
      images,
    });

    const intro = this.pickIntro(plainMarkdown);
    const experience = this.pickSections(sections, ["经历", "故事", "剧情", "资料", "档案", "背景"]);
    const abilities = this.pickSections(sections, ["技能", "能力", "神器", "属性", "影装", "战斗", "资质"]);
    const related = this.pickRelatedLinks(page.links || []);

    const blocks = [
      frontmatter,
      `# 简介\n\n${intro || "暂无自动解析内容。"}`,
      `# 基本资料\n\n${this.buildBasicInfo(page)}`,
      `# 人物经历\n\n${experience || "暂无自动解析内容。"}`,
      `# 能力\n\n${abilities || "暂无自动解析内容。"}`,
      `# 相关角色\n\n${related || "暂无自动解析内容。"}`,
    ];

    return {
      markdown: `${blocks.join("\n\n")}\n`,
      imageIndex: images,
      plainMarkdown,
    };
  }

  htmlToMarkdown(html) {
    if (!html) {
      return "";
    }

    let text = html;

    text = text.replace(/<!--[\s\S]*?-->/g, "");
    text = text.replace(/<script[\s\S]*?<\/script>/gi, "");
    text = text.replace(/<style[\s\S]*?<\/style>/gi, "");
    text = text.replace(/<noscript[\s\S]*?<\/noscript>/gi, "");
    text = text.replace(/<sup[^>]*class="[^"]*reference[^"]*"[\s\S]*?<\/sup>/gi, "");
    text = text.replace(/<span[^>]*class="[^"]*mw-editsection[^"]*"[\s\S]*?<\/span>/gi, "");
    text = text.replace(/<table[^>]*class="[^"]*(navbox|metadata|ambox)[^"]*"[\s\S]*?<\/table>/gi, "");

    text = text.replace(/<h2[^>]*>[\s\S]*?<span[^>]*class="mw-headline"[^>]*>([\s\S]*?)<\/span>[\s\S]*?<\/h2>/gi, "\n\n## $1\n\n");
    text = text.replace(/<h3[^>]*>[\s\S]*?<span[^>]*class="mw-headline"[^>]*>([\s\S]*?)<\/span>[\s\S]*?<\/h3>/gi, "\n\n### $1\n\n");
    text = text.replace(/<h4[^>]*>[\s\S]*?<span[^>]*class="mw-headline"[^>]*>([\s\S]*?)<\/span>[\s\S]*?<\/h4>/gi, "\n\n#### $1\n\n");

    text = text.replace(/<br\s*\/?>/gi, "\n");
    text = text.replace(/<\/p>/gi, "\n\n");
    text = text.replace(/<li[^>]*>/gi, "\n- ");
    text = text.replace(/<\/li>/gi, "");
    text = text.replace(/<\/tr>/gi, "\n");
    text = text.replace(/<\/t[dh]>/gi, " | ");
    text = text.replace(/<a[^>]*href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/gi, "$2");
    text = text.replace(/<img[^>]*alt="([^"]*)"[^>]*>/gi, " $1 ");
    text = text.replace(/<[^>]+>/g, "");
    text = this.decodeEntities(text);

    return text
      .split(/\r?\n/)
      .map((line) => line.replace(/[ \t]+/g, " ").trim())
      .join("\n")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  extractImages(html, apiImages = []) {
    const imagesByName = new Map();

    for (const image of apiImages) {
      imagesByName.set(image.name || image.title, {
        name: image.name || image.title,
        url: image.url || "",
        file_page: image.file_page || "",
        width: image.width || null,
        height: image.height || null,
        mime: image.mime || "",
      });
    }

    const imgPattern = /<img\b([^>]*)>/gi;
    let match;
    while ((match = imgPattern.exec(html || ""))) {
      const attrs = match[1];
      const src = this.readAttr(attrs, "src");
      const alt = this.readAttr(attrs, "alt");
      const fullSrc = src?.startsWith("//") ? `https:${src}` : src || "";
      const name = alt || this.filenameFromUrl(fullSrc);

      if (!name || imagesByName.has(name)) {
        continue;
      }

      imagesByName.set(name, {
        name,
        url: fullSrc,
        file_page: "",
        width: this.readNumberAttr(attrs, "width"),
        height: this.readNumberAttr(attrs, "height"),
        mime: "",
      });
    }

    return [...imagesByName.values()];
  }

  extractSections(markdown) {
    const lines = markdown.split(/\r?\n/);
    const sections = [];
    let current = null;

    for (const line of lines) {
      const heading = /^(#{2,4})\s+(.+)$/.exec(line);
      if (heading) {
        current = {
          level: heading[1].length,
          title: heading[2].trim(),
          lines: [],
        };
        sections.push(current);
      } else if (current) {
        current.lines.push(line);
      }
    }

    return sections.map((section) => ({
      ...section,
      content: section.lines.join("\n").trim(),
    }));
  }

  pickIntro(markdown) {
    const beforeFirstHeading = markdown.split(/\n##\s+/)[0]?.trim() || "";
    return this.limitText(beforeFirstHeading, 2000);
  }

  pickSections(sections, keywords) {
    const picked = sections.filter((section) => keywords.some((keyword) => section.title.includes(keyword)));
    return picked
      .map((section) => `## ${section.title}\n\n${this.limitText(section.content, 2500)}`)
      .join("\n\n")
      .trim();
  }

  pickRelatedLinks(links) {
    const titles = [...new Set(
      links
        .filter((link) => link.ns === 0 && link.exists !== false)
        .map((link) => link["*"] || link.title)
        .filter(Boolean)
        .filter((title) => !/^(文件|File|分类|Category):/.test(title))
    )];

    return titles.slice(0, 50).map((title) => `- ${title}`).join("\n");
  }

  buildBasicInfo(page) {
    const lines = [
      `- 标题：${page.title}`,
      `- 页面 ID：${page.pageid || "未知"}`,
      `- 来源页面：${page.sourceUrl || "未知"}`,
      `- 最后修订：${page.touched || "未知"}`,
    ];

    if (page.categories?.length) {
      lines.push(`- 分类：${page.categories.join("、")}`);
    }

    return lines.join("\n");
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
    lines.push("aliases:");
    for (const alias of data.aliases || []) {
      lines.push(`  - ${this.yamlScalar(alias)}`);
    }
    lines.push("category:");
    for (const category of data.category || []) {
      lines.push(`  - ${this.yamlScalar(category)}`);
    }
    lines.push("images:");
    for (const image of data.images || []) {
      lines.push(`  - name: ${this.yamlScalar(image.name)}`);
      lines.push(`    url: ${this.yamlScalar(image.url)}`);
      lines.push(`    file_page: ${this.yamlScalar(image.file_page)}`);
    }
    lines.push("---");
    return lines.join("\n");
  }

  decodeEntities(text) {
    const entities = {
      amp: "&",
      lt: "<",
      gt: ">",
      quot: "\"",
      apos: "'",
      nbsp: " ",
    };

    return text.replace(/&(#x?[0-9a-fA-F]+|[a-zA-Z]+);/g, (full, entity) => {
      if (entity.startsWith("#x")) {
        return String.fromCodePoint(Number.parseInt(entity.slice(2), 16));
      }
      if (entity.startsWith("#")) {
        return String.fromCodePoint(Number.parseInt(entity.slice(1), 10));
      }
      return entities[entity] || full;
    });
  }

  readAttr(attrs, name) {
    const match = new RegExp(`${name}="([^"]*)"`, "i").exec(attrs);
    return match ? this.decodeEntities(match[1]) : "";
  }

  readNumberAttr(attrs, name) {
    const value = this.readAttr(attrs, name);
    return value ? Number.parseInt(value, 10) || null : null;
  }

  filenameFromUrl(url) {
    if (!url) {
      return "";
    }

    const last = url.split("/").pop() || "";
    return decodeURIComponent(last.split("?")[0]);
  }

  yamlScalar(value) {
    const text = String(value ?? "");
    return JSON.stringify(text);
  }

  limitText(text, maxLength) {
    const clean = text.trim();
    if (clean.length <= maxLength) {
      return clean;
    }

    return `${clean.slice(0, maxLength).trim()}\n\n……`;
  }
}

module.exports = {
  Parser,
};
