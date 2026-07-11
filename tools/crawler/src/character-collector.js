const fs = require("node:fs");
const path = require("node:path");

class CharacterCollector {
  constructor({ wikiClient, parser, rawParser, cleanParser, outputRoot, rawRoot, indexRoot }) {
    if (!wikiClient) {
      throw new Error("CharacterCollector 需要 wikiClient。");
    }
    if (!parser && !rawParser) {
      throw new Error("CharacterCollector 需要 raw parser。");
    }
    if (!cleanParser) {
      throw new Error("CharacterCollector 需要 clean parser。");
    }

    this.wikiClient = wikiClient;
    this.rawParser = rawParser || parser;
    this.cleanParser = cleanParser;
    this.outputRoot = path.resolve(outputRoot);
    this.rawRoot = path.resolve(rawRoot || path.join(this.outputRoot, "..", "raw"));
    this.indexRoot = path.resolve(indexRoot || path.join(this.outputRoot, "..", "indexes"));
  }

  // 第一版只支持单个角色页面，不做全站同步、不做分类批量同步。
  async collect_character(title) {
    const page = await this.wikiClient.get_page(title);
    const imageInfo = await this.wikiClient.get_image_info(page.imageNames);
    const lastSync = new Date().toISOString();

    const pagePayload = {
      ...page,
      imageInfo,
      lastSync,
    };

    // 完整原始 Markdown：保留所有自动转换内容，作为可追溯 raw 层。
    const rawParsed = this.rawParser.parseCharacter(pagePayload);

    // 干净知识库 Markdown：只保留 Milestone 1.1 定义字段和章节。
    const cleanParsed = this.cleanParser.parseCharacter(pagePayload, rawParsed);

    const filename = `${this.safeFilename(page.title)}.md`;

    const rawDir = path.join(this.rawRoot, "huiji", "characters");
    fs.mkdirSync(rawDir, { recursive: true });
    const rawMarkdownPath = path.join(rawDir, filename.replace(/\.md$/, ".raw.md"));
    fs.writeFileSync(rawMarkdownPath, rawParsed.markdown, "utf8");

    const characterDir = path.join(this.outputRoot, "characters");
    fs.mkdirSync(characterDir, { recursive: true });
    const markdownPath = path.join(characterDir, filename);
    fs.writeFileSync(markdownPath, cleanParsed.markdown, "utf8");

    const imageIndexPath = this.writeImageIndex(page.title, cleanParsed.imageIndex, lastSync);

    return {
      title: page.title,
      markdownPath,
      rawMarkdownPath,
      imageIndexPath,
      imageCount: this.countImages(cleanParsed.imageIndex),
      categoryCount: page.categories.length,
      linkCount: page.links.length,
    };
  }

  writeImageIndex(title, images, lastSync) {
    const imageIndexDir = path.join(this.indexRoot, "images");
    fs.mkdirSync(imageIndexDir, { recursive: true });

    const imageIndexPath = path.join(imageIndexDir, `${this.safeFilename(title)}.images.json`);
    const payload = {
      title,
      last_sync: lastSync,
      images,
    };

    fs.writeFileSync(imageIndexPath, JSON.stringify(payload, null, 2), "utf8");

    return imageIndexPath;
  }

  countImages(images) {
    if (Array.isArray(images)) {
      return images.length;
    }

    return Object.values(images || {}).reduce((sum, bucket) => sum + (Array.isArray(bucket) ? bucket.length : 0), 0);
  }

  safeFilename(title) {
    return title.replace(/[<>:"/\\|?*\u0000-\u001F]/g, "_").trim();
  }
}

module.exports = {
  CharacterCollector,
};
