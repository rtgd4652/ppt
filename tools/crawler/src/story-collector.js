const fs = require("node:fs");
const path = require("node:path");

class StoryCollector {
  constructor({ wikiClient, storyParser, outputRoot, rawRoot, indexRoot }) {
    if (!wikiClient) {
      throw new Error("StoryCollector 需要 WikiClient。");
    }
    if (!storyParser) {
      throw new Error("StoryCollector 需要 StoryParser。");
    }

    this.wikiClient = wikiClient;
    this.storyParser = storyParser;
    this.outputRoot = path.resolve(outputRoot);
    this.rawRoot = path.resolve(rawRoot || path.join(this.outputRoot, "..", "raw"));
    this.indexRoot = path.resolve(indexRoot || path.join(this.outputRoot, "..", "indexes"));
  }

  // 单页剧情采集入口。第一阶段明确不做全站同步，由页面清单控制批量范围。
  async collect_story_page(title, options = {}) {
    const page = await this.wikiClient.get_page(title);
    const lastSync = new Date().toISOString();
    const pagePayload = {
      ...page,
      lastSync,
    };

    const rawParsed = this.storyParser.parseRaw(pagePayload);
    const cleanParsed = this.storyParser.parseStory(pagePayload, rawParsed, options);
    const filename = `${this.safeFilename(page.title)}.md`;

    const rawDir = path.join(this.rawRoot, "huiji", "stories");
    fs.mkdirSync(rawDir, { recursive: true });
    const rawMarkdownPath = path.join(rawDir, filename.replace(/\.md$/, ".raw.md"));
    fs.writeFileSync(rawMarkdownPath, rawParsed.markdown, "utf8");

    const storyDir = path.join(this.outputRoot, "story", "pages");
    fs.mkdirSync(storyDir, { recursive: true });
    const markdownPath = path.join(storyDir, filename);
    fs.writeFileSync(markdownPath, cleanParsed.markdown, "utf8");

    const sourceIndexPath = this.writeSourceIndex(page, cleanParsed, rawMarkdownPath, markdownPath, lastSync, options);

    return {
      title: page.title,
      rawMarkdownPath,
      markdownPath,
      sourceIndexPath,
      sectionCount: cleanParsed.sections.length,
      linkCount: page.links.length,
      categoryCount: page.categories.length,
    };
  }

  writeSourceIndex(page, parsed, rawMarkdownPath, markdownPath, lastSync, options) {
    const indexDir = path.join(this.indexRoot, "story_pages");
    fs.mkdirSync(indexDir, { recursive: true });

    const filename = `${this.safeFilename(page.title)}.source.json`;
    const sourceIndexPath = path.join(indexDir, filename);
    const articleLinks = (page.links || [])
      .filter((link) => link && (link.ns === 0 || link.ns === "0" || link.ns === undefined))
      .map((link) => String(link["*"] || link.title || "").trim())
      .filter(Boolean);
    const payload = {
      title: page.title,
      source_url: page.sourceUrl || "",
      page_id: page.pageid || null,
      touched: page.touched || "",
      last_sync: lastSync,
      story_scope: options.storyScope || "unclassified",
      route: options.route || "",
      chapter: options.chapter || "",
      day: options.day || "",
      categories: page.categories || [],
      sections: parsed.sections || [],
      choice_trees: parsed.choiceTrees || [],
      article_links: [...new Set(articleLinks)],
      image_names: page.imageNames || [],
      legacy_video_evidence: options.legacyVideoEvidence || [],
      manual_structure_note: options.manualStructureNote || "",
      manual_structure_reference: options.manualStructureReference || "",
      raw_markdown_path: this.relativePath(rawMarkdownPath),
      clean_markdown_path: this.relativePath(markdownPath),
    };

    fs.writeFileSync(sourceIndexPath, JSON.stringify(payload, null, 2), "utf8");
    return sourceIndexPath;
  }

  relativePath(fullPath) {
    return path.relative(path.resolve(this.outputRoot, ".."), fullPath).split(path.sep).join("/");
  }

  safeFilename(title) {
    return String(title || "untitled").replace(/[<>:"/\\|?*\u0000-\u001F]/g, "_").trim();
  }
}

module.exports = {
  StoryCollector,
};
