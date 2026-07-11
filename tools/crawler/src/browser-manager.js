const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

// 默认使用项目内的浏览器用户数据目录。
// 这样 Cloudflare Challenge 通过后，Cookie / LocalStorage 会被复用，不需要每次重新验证。
const DEFAULT_PROFILE_DIR = path.resolve(__dirname, "..", ".playwright-profile", "default");

// 默认调试产物目录：截图、临时 HTML、下载验证文件等都可以放这里。
const DEFAULT_ARTIFACT_DIR = path.resolve(__dirname, "..", "artifacts");

class BrowserManager {
  constructor(options = {}) {
    this.profileDir = path.resolve(options.profileDir || DEFAULT_PROFILE_DIR);
    this.artifactDir = path.resolve(options.artifactDir || DEFAULT_ARTIFACT_DIR);
    this.headless = options.headless ?? false;
    this.channel = options.channel || "chrome";
    this.locale = options.locale || "zh-CN";
    this.viewport = options.viewport || { width: 1400, height: 900 };
    this.timeout = options.timeout || 120_000;

    this.context = null;
    this.page = null;
    this.lastUrl = null;
  }

  // 启动浏览器并复用用户数据目录。
  async start() {
    fs.mkdirSync(this.profileDir, { recursive: true });
    fs.mkdirSync(this.artifactDir, { recursive: true });

    this.context = await chromium.launchPersistentContext(this.profileDir, {
      channel: this.channel,
      headless: this.headless,
      viewport: this.viewport,
      locale: this.locale,
    });

    this.page = this.context.pages()[0] || (await this.context.newPage());
    return this;
  }

  // 打开页面。
  async goto(url, options = {}) {
    this.#assertStarted();
    this.lastUrl = url;

    await this.page.goto(url, {
      waitUntil: options.waitUntil || "domcontentloaded",
      timeout: options.timeout || this.timeout,
    });

    return this.page;
  }

  // 等待页面完全加载；包含对 Cloudflare Challenge 的温和等待。
  // 如果站点要求人工点选验证，脚本会给用户留出时间在浏览器中处理。
  async wait_ready(options = {}) {
    this.#assertStarted();

    const timeout = options.timeout || this.timeout;
    const settleMs = options.settleMs ?? 3000;

    await this.page.waitForLoadState("domcontentloaded", { timeout }).catch(() => {});
    await this.page.waitForLoadState("networkidle", { timeout }).catch(() => {});

    const deadline = Date.now() + timeout;
    while (Date.now() < deadline) {
      const title = await this.page.title().catch(() => "");
      const bodyText = await this.page.locator("body").innerText({ timeout: 1000 }).catch(() => "");
      const stillChallenge =
        /just a moment/i.test(title) ||
        /cloudflare/i.test(bodyText) ||
        /checking your browser/i.test(bodyText) ||
        /请稍候|正在检查|验证/i.test(bodyText);

      if (!stillChallenge) {
        break;
      }

      await this.page.waitForTimeout(2000);
    }

    await this.page.waitForTimeout(settleMs);
    return this.page;
  }

  // 获取最终 HTML。
  async html() {
    this.#assertStarted();
    return this.page.content();
  }

  // 调试截图。未传 path 时，自动写入 artifacts 目录。
  async screenshot(outputPath = null, options = {}) {
    this.#assertStarted();

    const finalPath =
      outputPath ||
      path.join(this.artifactDir, `screenshot-${this.#safeTimestamp()}.png`);

    fs.mkdirSync(path.dirname(finalPath), { recursive: true });
    await this.page.screenshot({
      path: finalPath,
      fullPage: options.fullPage ?? true,
    });

    return finalPath;
  }

  // 在当前会话下下载资源。
  // 默认使用页面内 fetch：这会复用真实页面的 Cookie、Cloudflare 会话和浏览器请求环境。
  // 如果需要旧的 Playwright APIRequestContext 模式，可以传入 { mode: "request" }。
  // 若提供 outputPath，则保存到文件并返回文件信息；否则返回 Buffer 与响应头。
  async download(url, outputPath = null, options = {}) {
    this.#assertStarted();

    const mode = options.mode || "page";
    let status;
    let headers;
    let buffer;

    if (mode === "request") {
      const response = await this.context.request.get(url, {
        headers: options.headers || {},
        timeout: options.timeout || this.timeout,
      });

      status = response.status();
      headers = response.headers();
      buffer = await response.body();
    } else {
      const result = await this.page.evaluate(
        async ({ targetUrl, requestHeaders }) => {
          const response = await fetch(targetUrl, {
            method: "GET",
            credentials: "include",
            cache: "no-store",
            headers: requestHeaders || {},
          });

          const arrayBuffer = await response.arrayBuffer();
          const bytes = Array.from(new Uint8Array(arrayBuffer));
          const headers = {};

          for (const [key, value] of response.headers.entries()) {
            headers[key] = value;
          }

          return {
            status: response.status,
            headers,
            bytes,
          };
        },
        {
          targetUrl: url,
          requestHeaders: options.headers || {},
        }
      );

      status = result.status;
      headers = result.headers;
      buffer = Buffer.from(result.bytes);
    }

    if (options.throwOnError !== false && (status < 200 || status >= 300)) {
      throw new Error(`下载失败：HTTP ${status} ${url}`);
    }

    if (!outputPath) {
      return {
        url,
        status,
        headers,
        buffer,
      };
    }

    const finalPath = path.resolve(outputPath);
    fs.mkdirSync(path.dirname(finalPath), { recursive: true });
    fs.writeFileSync(finalPath, buffer);

    return {
      url,
      status,
      headers,
      path: finalPath,
      bytes: buffer.length,
    };
  }

  // 关闭浏览器。
  async close() {
    if (this.context) {
      await this.context.close();
      this.context = null;
      this.page = null;
    }
  }

  #assertStarted() {
    if (!this.context || !this.page) {
      throw new Error("BrowserManager 尚未启动，请先调用 browser.start()。");
    }
  }

  #safeTimestamp() {
    return new Date().toISOString().replace(/[:.]/g, "-");
  }
}

module.exports = {
  BrowserManager,
};
